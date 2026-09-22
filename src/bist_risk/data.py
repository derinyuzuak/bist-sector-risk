"""Explicit input contracts, provenance and release-time alignment."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_inputs(folder, mode):
    folder = Path(folder)
    provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
    if provenance["mode"] != mode:
        raise ValueError("Input provenance mode does not match requested mode")
    prices = pd.read_csv(folder / "prices.csv", parse_dates=["date"])
    macro = pd.read_csv(folder / "macro.csv", parse_dates=["period", "available_at"])
    calendar = pd.read_csv(folder / "calendar.csv", parse_dates=["date"])
    required = {"source_url", "retrieved_at", "unit", "frequency", "transformation", "redistribution", "vintage_policy"}
    ids = set(prices.sector) | set(macro.series)
    for name in ids:
        entry = provenance["series"].get(name, {})
        if not required <= entry.keys() or any(not entry[x] for x in required):
            raise ValueError(f"Incomplete provenance for {name}")
    if prices.duplicated(["date", "sector"]).any() or macro.duplicated(["series", "period", "available_at"]).any():
        raise ValueError("Duplicate observations")
    if prices[["date", "sector", "close"]].isna().any().any() or not np.isfinite(prices.close).all() or (prices.close <= 0).any():
        raise ValueError("Prices must be dated, finite and strictly positive")
    if macro[["series", "period", "available_at", "value"]].isna().any().any() or not np.isfinite(macro.value).all():
        raise ValueError("Invalid macro observation")
    if (macro.available_at < macro.period).any():
        raise ValueError("Macro release predates its observation period")
    if calendar.date.isna().any() or calendar.date.duplicated().any():
        raise ValueError("Invalid trading calendar")
    if not set(prices.date) <= set(calendar.date):
        raise ValueError("Prices contain dates outside the supplied trading calendar")
    return prices, macro, calendar, provenance


def monthly_prices(prices, calendar, min_days=15):
    """No imputation. A missing scheduled session invalidates its month and next return."""
    sessions = pd.DatetimeIndex(calendar.date).sort_values()
    rows = []
    for sector, group in prices.groupby("sector"):
        p = group.set_index("date").close.reindex(sessions)
        daily = np.log(p / p.shift(1))
        frame = pd.DataFrame({"price": p, "log_return": daily}, index=sessions)
        previous_close = np.nan
        previous_valid = False
        for period, g in frame.groupby(frame.index.to_period("M")):
            complete = g.price.notna().all() and len(g) >= min_days
            close = g.price.iloc[-1] if complete else np.nan
            ret = close / previous_close - 1 if complete and previous_valid else np.nan
            # Includes the previous-month close to first-session return.
            vol = g.log_return.std(ddof=1) * np.sqrt(252) if complete and g.log_return.notna().all() else np.nan
            rows.append(dict(date=period.to_timestamp("M"), sector=sector, close=close,
                             return_value=ret, volatility=vol, observed_days=int(g.price.count()),
                             expected_days=len(g), complete=bool(complete)))
            previous_close, previous_valid = close, complete
    return pd.DataFrame(rows)


def align_macro(macro, dates):
    """Use latest known vintage of the latest released period, never future revisions."""
    rows = []
    for date in dates:
        row = {"date": pd.Timestamp(date)}
        for name, group in macro.groupby("series"):
            known = group[group.available_at <= date].sort_values(["period", "available_at"])
            row[name] = known.iloc[-1].value if len(known) else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index("date").sort_index()


def shock_scores(aligned):
    """Changes standardized exclusively with earlier changes; threshold is descriptive."""
    changes = aligned.diff()
    history = changes.shift(1).expanding(min_periods=12)
    return (changes - history.mean()) / history.std(ddof=1).replace(0, np.nan)


