"""Import the documented Borsa Istanbul price-index archive format."""
from pathlib import Path
import csv
import json
import zipfile
import pandas as pd


SECTORS = ("XUMAL", "XELKT", "XINSA", "XUSIN", "XTCRT", "XBLSM")
ZERO_CHANGE_DATE = pd.Timestamp("2020-07-27")


def _read_csv_bytes(content):
    """Read the documented semicolon CSV with common BIST encodings."""
    for encoding in ("utf-8-sig", "cp1254", "latin1"):
        try:
            return pd.read_csv(__import__("io").BytesIO(content), sep=";", encoding=encoding, dtype=str)
        except UnicodeDecodeError:
            pass
    raise ValueError("Could not decode a BIST CSV")


def _files(raw):
    for path in sorted(Path(raw).glob("**/*")):
        if path.suffix.lower() == ".csv":
            yield path.name, path.read_bytes()
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if member.lower().endswith(".csv"):
                        yield f"{path.name}:{member}", archive.read(member)


def _column(frame, *aliases):
    normal = {str(c).strip().casefold(): c for c in frame.columns}
    for name in aliases:
        if name.casefold() in normal:
            return normal[name.casefold()]
    raise ValueError(f"Missing BIST archive column; expected one of {aliases}")


def prepare_bist_prices(raw, output, sectors=SECTORS):
    """Create price/calendar inputs from authorised BIST daily price-index files.

    BIST documents the fields as date, index code, name, currency, session and
    closing value. No dates or prices are imputed. The 27 July 2020 1:100
    historical scale adjustment is applied before return calculations.
    """
    frames = []
    all_sessions = []
    for name, content in _files(raw):
        frame = _read_csv_bytes(content)
        date = _column(frame, "Tarih", "Date")
        code = _column(frame, "Endeks Kodu", "Index Code")
        close = _column(frame, "Kapanış Değeri", "Closing Value", "Close")
        session = next((c for c in frame.columns if str(c).strip().casefold() in {"seans no", "session no"}), None)
        parsed = pd.DataFrame({"date": pd.to_datetime(frame[date], dayfirst=True, errors="coerce"),
                               "sector": frame[code].astype(str).str.strip(),
                               "close": pd.to_numeric(frame[close].astype(str).str.replace(",", "", regex=False), errors="coerce")})
        if parsed.date.isna().any() or parsed.close.isna().any():
            raise ValueError(f"Invalid date or closing value in {name}")
        all_sessions.append(parsed.date)
        parsed = parsed[parsed.sector.isin(sectors)]
        if session is not None:
            parsed = parsed.assign(_session=pd.to_numeric(frame.loc[parsed.index, session], errors="coerce").fillna(-1))
            parsed = parsed.sort_values(["date", "sector", "_session"]).drop_duplicates(["date", "sector"], keep="last").drop(columns="_session")
        frames.append(parsed)
    if not frames:
        raise ValueError("No CSV files found in BIST archive folder")
    prices = pd.concat(frames, ignore_index=True)
    if prices.duplicated(["date", "sector"]).any():
        raise ValueError("Duplicate date/index rows across BIST files")
    if prices.empty:
        raise ValueError("None of the requested sector codes appears in the BIST files")
    prices.loc[prices.date < ZERO_CHANGE_DATE, "close"] /= 100.0
    calendar = pd.DataFrame({"date": pd.DatetimeIndex(pd.concat(all_sessions).unique()).sort_values()})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    prices.sort_values(["date", "sector"]).to_csv(output / "prices.csv", index=False)
    calendar.to_csv(output / "calendar.csv", index=False)
    provenance = {code: dict(source_url="https://datastore.borsaistanbul.com/product-type/3180",
        retrieved_at=pd.Timestamp.now(tz="UTC").isoformat(), unit="BIST price index points", frequency="daily",
        transformation="authorised BIST price-index archive; close; pre-2020-07-27 values divided by 100",
        redistribution="raw archive remains private; verify BIST licence before sharing",
        vintage_policy="end-of-day source file; historical revisions/republish events retained if supplied") for code in sectors}
    (output / "bist_provenance.json").write_text(json.dumps(dict(series=provenance,
        calendar="Union of dates recorded in authorised BIST daily price-index files", source_files=[x[0] for x in _files(raw)]), ensure_ascii=False, indent=2), encoding="utf-8")


def assemble_study(prices_folder, macro_folder, output):
    """Combine separately audited BIST and EVDS preparations into research input."""
    prices_folder, macro_folder, output = Path(prices_folder), Path(macro_folder), Path(output)
    bist_meta = json.loads((prices_folder / "bist_provenance.json").read_text(encoding="utf-8"))
    macro_meta = json.loads((macro_folder / "macro_provenance.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    for name, source in (("prices.csv", prices_folder), ("calendar.csv", prices_folder), ("macro.csv", macro_folder)):
        (output / name).write_bytes((source / name).read_bytes())
    provenance = dict(mode="research", calendar=bist_meta["calendar"], series={**bist_meta["series"], **macro_meta["series"]})
    (output / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
