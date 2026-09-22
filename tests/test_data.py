import numpy as np
import pandas as pd
import pytest
from bist_risk.data import align_macro, monthly_prices, shock_scores, read_inputs


def test_release_and_revision_alignment():
    macro = pd.DataFrame(dict(series=["gdp"]*3,
        period=pd.to_datetime(["2020-03-31", "2020-06-30", "2020-03-31"]),
        available_at=pd.to_datetime(["2020-05-30", "2020-08-31", "2020-09-01"]), value=[1.,2.,999.]))
    x = align_macro(macro, pd.to_datetime(["2020-04-30", "2020-05-31", "2020-09-30"]))
    assert np.isnan(x.iloc[0,0])
    assert x.iloc[1,0] == 1
    assert x.iloc[2,0] == 2


def test_monthly_return_and_volatility():
    dates = pd.bdate_range("2018-12-03", "2019-02-28")
    logs = np.sin(np.arange(len(dates)))*.01
    prices = pd.DataFrame(dict(date=dates, sector="A", close=100*np.exp(np.cumsum(logs))))
    out = monthly_prices(prices, pd.DataFrame(dict(date=dates))).set_index("date")
    jan = dates.month == 1
    expected = prices.loc[jan,"close"].iloc[-1]/prices.loc[dates.month == 12,"close"].iloc[-1]-1
    assert out.loc["2019-01-31", "return_value"] == pytest.approx(expected)
    assert out.loc["2019-01-31", "volatility"] == pytest.approx(np.std(logs[jan], ddof=1)*np.sqrt(252))


def test_missing_session_invalidates_month_without_fill():
    dates = pd.bdate_range("2018-12-03", "2019-03-29")
    prices = pd.DataFrame(dict(date=dates, sector="A", close=np.arange(len(dates))+100.)).drop(30)
    x = monthly_prices(prices, pd.DataFrame(dict(date=dates))).set_index("date")
    assert not x.loc["2019-01-31", "complete"]
    assert np.isnan(x.loc["2019-02-28", "return_value"])
    assert pd.notna(x.loc["2019-03-31", "return_value"])


def test_shock_normalization_excludes_current_observation():
    x = pd.DataFrame({"a":np.arange(30.)**2}, index=pd.date_range("2020-01-31", periods=30, freq="ME"))
    y = x.copy(); y.iloc[-1] += 1000
    a, b = shock_scores(x), shock_scores(y)
    pd.testing.assert_frame_equal(a.iloc[:-1], b.iloc[:-1])
    historical_std = x.diff().iloc[1:-1].std().iloc[0]
    assert b.iloc[-1,0]-a.iloc[-1,0] == pytest.approx(1000/historical_std)


def test_provenance_mode_and_duplicates(tmp_path):
    entry = dict(source_url="https://example.test", retrieved_at="2026-09-21", unit="index", frequency="daily",
                 transformation="test fixture", redistribution="test fixture", vintage_policy="test fixture")
    (tmp_path/"prices.csv").write_text("date,sector,close\n2024-01-02,XUSIN,100\n")
    (tmp_path/"macro.csv").write_text("series,period,available_at,value\ncpi,2023-12-31,2024-01-02,100\n")
    (tmp_path/"calendar.csv").write_text("date\n2024-01-02\n")
    (tmp_path/"provenance.json").write_text(__import__("json").dumps({"mode":"research", "calendar":"test fixture", "series":{"XUSIN":entry, "cpi":entry}}))
    read_inputs(tmp_path, "research")
    with pytest.raises(ValueError, match="mode"):
        read_inputs(tmp_path, "other")
    p = pd.read_csv(tmp_path/"prices.csv")
    pd.concat([p,p.iloc[:1]]).to_csv(tmp_path/"prices.csv", index=False)
    with pytest.raises(ValueError, match="Duplicate"):
        read_inputs(tmp_path, "research")
