"""Explicit EVDS acquisition. Raw response is never silently treated as vintage data."""
from pathlib import Path
import os
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
import pandas as pd


EVDS_SERIES = {
    "TP.DK.USD.A": {"name": "usdtry", "frequency": "daily", "unit": "TRY per USD", "aggregation": "month-end", "lag_days": 0},
    "TP.BRENTPETROL.EUBP": {"name": "brent", "frequency": "daily", "unit": "USD per barrel", "aggregation": "month-end", "lag_days": 0},
    "TP.GENENDEKS.T1": {"name": "cpi", "frequency": "monthly", "unit": "index (2003=100)", "aggregation": "last", "lag_days": 35},
    "TP.TSANAYMT2021.BCD": {"name": "industrial_production", "frequency": "monthly", "unit": "index (2021=100)", "aggregation": "last", "lag_days": 60},
    "TP.BISPOLFAIZ.TUR": {"name": "policy_rate", "frequency": "monthly", "unit": "percent", "aggregation": "last", "lag_days": 35},
    "TP.GSYIH60.HY.B1GQ": {"name": "gdp_growth", "frequency": "quarterly", "unit": "percent quarter-on-quarter", "aggregation": "qoq change from chained-volume index", "lag_days": 100},
}


def load_evds_key(key_file=None):
    """Read a local, Git-ignored EVDS key without emitting it to logs or outputs."""
    key = os.environ.get("EVDS_API_KEY", "").strip()
    if key:
        return key
    path = Path(key_file or "data/private/evds.key")
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            candidate = line.split("=", 1)[-1].strip().strip('"').strip("'")
            if candidate:
                return candidate
    return ""


def fetch_evds(series, start, end, output, key_file=None):
    key = load_evds_key(key_file)
    if not key:
        raise ValueError("Set EVDS_API_KEY or place it in the Git-ignored data/private/evds.key file; do not paste it into source code.")
    endpoint = "https://evds3.tcmb.gov.tr/igmevdsms-dis/"
    first, last = datetime.strptime(start, "%d-%m-%Y"), datetime.strptime(end, "%d-%m-%Y")
    if first > last:
        raise ValueError("Start date follows end date")
    payloads = []
    try:
        # EVDS aligns a multi-series response to common dates. Requesting daily,
        # monthly and quarterly series together would therefore discard valid
        # observations. Keep each native frequency intact and split daily spans
        # annually to avoid the service's 1,000-observation truncation.
        for code in series:
            for year in range(first.year, last.year + 1):
                lo, hi = max(first, datetime(year, 1, 1)), min(last, datetime(year, 12, 31))
                params = {"series": code, "startDate": lo.strftime("%d-%m-%Y"),
                          "endDate": hi.strftime("%d-%m-%Y"), "type": "json"}
                response = requests.get(endpoint + urlencode(params), headers={"key": key}, timeout=60, allow_redirects=False)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not payload.get("items"):
                    raise ValueError("No observations")
                payloads.append(dict(series=code, start=params["startDate"], end=params["endDate"], response=payload))
    except (requests.RequestException, ValueError):
        raise ValueError("EVDS request failed. Check key, series codes and official service status; credentials are not logged.") from None
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/"evds_raw.json").write_text(json.dumps(payloads, ensure_ascii=False, indent=2), encoding="utf-8")
    (output/"evds_request.json").write_text(json.dumps(dict(endpoint=endpoint, series=series, start=start, end=end,
        retrieved_at=datetime.now(timezone.utc).isoformat(), vintage_policy="latest revised download; not point-in-time"), indent=2), encoding="utf-8")


def _evds_period(value):
    """Parse EVDS daily, YYYY-M and YYYY-Q labels to observation-period ends."""
    text = str(value)
    if "-Q" in text:
        year, quarter = text.split("-Q")
        return pd.Period(f"{year}Q{quarter}", freq="Q").to_timestamp(how="end").normalize()
    if len(text.split("-")) == 2 and text[:4].isdigit():
        year, month = text.split("-")
        return pd.Period(f"{year}-{int(month):02d}", freq="M").to_timestamp("M")
    return pd.to_datetime(text, dayfirst=True)


def build_evds_macro(raw_folder, output):
    """Convert explicitly mapped EVDS raw downloads to a macro input plus audit file.

    Publication guards are deliberately conservative calendar assumptions, not
    historical first-release vintages. They prevent future observation periods
    from entering a forecast but do not make a latest-revised download a genuine
    real-time data set.
    """
    raw_folder, output = Path(raw_folder), Path(output)
    chunks = json.loads((raw_folder / "evds_raw.json").read_text(encoding="utf-8"))
    request = json.loads((raw_folder / "evds_request.json").read_text(encoding="utf-8"))
    values = {code: [] for code in EVDS_SERIES}
    for chunk in chunks:
        code = chunk.get("series")
        if code not in values:
            continue
        field = code.replace(".", "_")
        for item in chunk["response"]["items"]:
            raw = item.get(field)
            if raw in (None, "", "-"):
                continue
            values[code].append((_evds_period(item["Tarih"]), float(raw)))
    rows, entries = [], {}
    for code, spec in EVDS_SERIES.items():
        raw = pd.DataFrame(values[code], columns=["period", "value"]).drop_duplicates("period").sort_values("period")
        if raw.empty:
            raise ValueError(f"EVDS raw response does not contain mapped series {code}")
        if spec["frequency"] == "daily":
            # Forecast features use the final published daily value in each month.
            raw["month"] = raw["period"].dt.to_period("M")
            raw = raw.groupby("month", as_index=False).tail(1).drop(columns="month")
            raw["period"] = raw["period"].dt.to_period("M").dt.to_timestamp("M")
        if spec["name"] == "gdp_growth":
            raw["value"] = raw["value"].pct_change() * 100
            raw = raw.dropna(subset=["value"])
        for item in raw.itertuples(index=False):
            rows.append(dict(series=spec["name"], period=item.period, available_at=item.period + pd.Timedelta(days=spec["lag_days"]), value=item.value))
        entries[spec["name"]] = dict(
            source_url="https://evds3.tcmb.gov.tr/igmevdsms-dis/",
            retrieved_at=request["retrieved_at"], unit=spec["unit"], frequency=spec["frequency"],
            transformation=f"EVDS {code}; {spec['aggregation']}; availability guard +{spec['lag_days']} calendar days",
            redistribution="raw response remains private; verify source terms before sharing",
            vintage_policy="latest revised download with conservative calendar availability guard; not first-release vintage",
        )
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(["series", "period"]).to_csv(output / "macro.csv", index=False)
    (output / "macro_provenance.json").write_text(json.dumps(dict(mode="research", series=entries,
        note="Macro-only preparation. Add licensed BIST prices and a verified BIST trading calendar before validation."), ensure_ascii=False, indent=2), encoding="utf-8")
