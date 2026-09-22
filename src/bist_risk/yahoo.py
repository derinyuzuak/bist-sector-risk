"""Secondary-source daily BIST index acquisition via yfinance."""
from pathlib import Path
import json
from datetime import datetime, timezone
import pandas as pd


# Verified by an actual 2019–2024 availability check on 2026-09-21.
# Other proposal representatives are intentionally excluded when Yahoo does not
# expose continuous daily index history for them.
YAHOO_INDEXES = {"XBANK": "XBANK.IS", "XUSIN": "XUSIN.IS"}


def prepare_yahoo_prices(output, start="2017-12-01", end="2025-01-01", indexes=YAHOO_INDEXES):
    """Download verifiable Yahoo Finance index closes into the project's contract.

    This is a secondary, latest-available source. It cannot establish BIST's
    official historical-vintage record and it does not grant redistribution
    rights; generated raw input remains under data/private.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ValueError("Install the yfinance dependency before using prepare-yahoo") from exc
    rows, calendar = [], []
    for sector, ticker in indexes.items():
        history = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False, actions=False)
        if history.empty or "Close" not in history:
            raise ValueError(f"Yahoo Finance returned no daily close history for {ticker}")
        close = pd.to_numeric(history["Close"], errors="coerce")
        index = pd.to_datetime(history.index).tz_localize(None).normalize()
        if close.isna().any() or (close <= 0).any() or index.duplicated().any():
            raise ValueError(f"Invalid Yahoo Finance close history for {ticker}")
        rows.extend(dict(date=date, sector=sector, close=float(value)) for date, value in zip(index, close))
        calendar.extend(index)
    prices = pd.DataFrame(rows).sort_values(["date", "sector"])
    if prices.duplicated(["date", "sector"]).any():
        raise ValueError("Duplicate Yahoo Finance date/index rows")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    prices.to_csv(output / "prices.csv", index=False)
    pd.DataFrame({"date": pd.DatetimeIndex(calendar).unique().sort_values()}).to_csv(output / "calendar.csv", index=False)
    now = datetime.now(timezone.utc).isoformat()
    entries = {sector: dict(source_url=f"https://finance.yahoo.com/quote/{ticker}/history/", retrieved_at=now,
        unit="BIST price index points", frequency="daily", transformation="Yahoo Finance unadjusted Close; no imputation",
        redistribution="secondary-source raw data remains private; verify Yahoo Finance terms before sharing",
        vintage_policy="latest-available download; not an official BIST historical vintage") for sector, ticker in indexes.items()}
    (output / "bist_provenance.json").write_text(json.dumps(dict(series=entries,
        calendar="Union of observed Yahoo Finance index trading dates", source="yfinance secondary-source acquisition",
        indexes=indexes, retrieved_at=now), ensure_ascii=False, indent=2), encoding="utf-8")
