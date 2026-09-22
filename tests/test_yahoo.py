import json
import pandas as pd
from bist_risk.yahoo import prepare_yahoo_prices


def test_yahoo_prices_write_private_contract(monkeypatch, tmp_path):
    def history(self, **kwargs):
        return pd.DataFrame({"Close":[100.0, 101.0]}, index=pd.DatetimeIndex(["2019-01-02", "2019-01-03"], tz="Europe/Istanbul"))
    class Ticker:
        def __init__(self, symbol): self.symbol = symbol
    Ticker.history = history
    monkeypatch.setattr("yfinance.Ticker", Ticker)
    out = tmp_path / "yahoo"
    prepare_yahoo_prices(out, indexes={"XBANK":"XBANK.IS", "XUSIN":"XUSIN.IS"})
    prices = pd.read_csv(out / "prices.csv")
    meta = json.loads((out / "bist_provenance.json").read_text())
    assert len(prices) == 4 and set(prices.sector) == {"XBANK", "XUSIN"}
    assert meta["source"] == "yfinance secondary-source acquisition"
