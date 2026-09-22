import json
import pytest
from bist_risk.providers import fetch_evds, build_evds_macro


def test_missing_key_fails_without_network(monkeypatch, tmp_path):
    monkeypatch.delenv("EVDS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="EVDS_API_KEY"):
        fetch_evds(["TP.DK.USD.A"], "01-01-2024", "31-12-2024", tmp_path, tmp_path/"missing.key")


def test_yearly_chunks_and_header_only_secret(monkeypatch, tmp_path):
    calls = []
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"items":[{"Tarih":"01-01-2023", "TP_DK_USD_A":"10"}]}
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()
    monkeypatch.setenv("EVDS_API_KEY", "test-secret")
    monkeypatch.setattr("bist_risk.providers.requests.get", get)
    fetch_evds(["TP.DK.USD.A"], "01-01-2023", "31-12-2024", tmp_path, tmp_path/"missing.key")
    assert len(calls) == 2
    assert all(url.startswith("https://evds3.tcmb.gov.tr/igmevdsms-dis/series=") for url,_ in calls)
    assert all("test-secret" not in url and kwargs["headers"]["key"] == "test-secret" for url,kwargs in calls)
    assert all(not kwargs["allow_redirects"] for _,kwargs in calls)
    chunks = json.loads((tmp_path/"evds_raw.json").read_text())
    assert len(chunks) == 2 and {chunk["series"] for chunk in chunks} == {"TP.DK.USD.A"}
    assert "test-secret" not in (tmp_path/"evds_request.json").read_text()


def test_key_file_is_supported_without_exposing_value(monkeypatch, tmp_path):
    monkeypatch.delenv("EVDS_API_KEY", raising=False)
    key_file = tmp_path/"evds.key"
    key_file.write_text("# local only\nEVDS_API_KEY='test-key-from-file'\n", encoding="utf-8")
    seen = []
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"items":[{"Tarih":"01-01-2024"}]}
    def get(url, **kwargs):
        seen.append(kwargs["headers"])
        return Response()
    monkeypatch.setattr("bist_risk.providers.requests.get", get)
    fetch_evds(["TP.DK.USD.A"], "01-01-2024", "31-12-2024", tmp_path/"out", key_file)
    assert seen == [{"key":"test-key-from-file"}]


def test_mixed_frequency_series_are_not_intersection_aligned(monkeypatch, tmp_path):
    calls = []
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"items":[{"Tarih":"01-01-2024", "value":"1"}]}
    def get(url, **kwargs):
        calls.append(url)
        return Response()
    monkeypatch.setenv("EVDS_API_KEY", "local-test-key")
    monkeypatch.setattr("bist_risk.providers.requests.get", get)
    fetch_evds(["DAILY", "QUARTERLY"], "01-01-2024", "31-12-2024", tmp_path)
    chunks = json.loads((tmp_path/"evds_raw.json").read_text())
    assert len(calls) == 2
    assert [x["series"] for x in chunks] == ["DAILY", "QUARTERLY"]


def test_evds_macro_converter_preserves_periods_and_release_guard(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    chunks = [
        {"series":"TP.DK.USD.A", "response":{"items":[
            {"Tarih":"30-01-2024", "TP_DK_USD_A":"30.0"}, {"Tarih":"31-01-2024", "TP_DK_USD_A":"31.0"}]}},
        {"series":"TP.BRENTPETROL.EUBP", "response":{"items":[{"Tarih":"31-01-2024", "TP_BRENTPETROL_EUBP":"80.0"}]}},
        {"series":"TP.GENENDEKS.T1", "response":{"items":[{"Tarih":"2024-1", "TP_GENENDEKS_T1":"100"}]}},
        {"series":"TP.TSANAYMT2021.BCD", "response":{"items":[{"Tarih":"2024-1", "TP_TSANAYMT2021_BCD":"100"}]}},
        {"series":"TP.BISPOLFAIZ.TUR", "response":{"items":[{"Tarih":"2024-1", "TP_BISPOLFAIZ_TUR":"45"}]}},
        {"series":"TP.GSYIH60.HY.B1GQ", "response":{"items":[
            {"Tarih":"2023-Q4", "TP_GSYIH60_HY_B1GQ":"100"}, {"Tarih":"2024-Q1", "TP_GSYIH60_HY_B1GQ":"105"}]}}
    ]
    (raw/"evds_raw.json").write_text(json.dumps(chunks), encoding="utf-8")
    (raw/"evds_request.json").write_text(json.dumps({"retrieved_at":"2026-09-21T00:00:00+00:00"}), encoding="utf-8")
    out = tmp_path / "out"
    build_evds_macro(raw, out)
    macro = __import__("pandas").read_csv(out/"macro.csv")
    assert macro.loc[macro.series.eq("usdtry"), "value"].iat[0] == 31.0
    gdp = macro.loc[macro.series.eq("gdp_growth")].iloc[0]
    assert round(gdp.value, 6) == 5.0 and gdp.available_at == "2024-07-09"
