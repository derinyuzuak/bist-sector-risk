import json
import zipfile
import pandas as pd
from bist_risk.bist import prepare_bist_prices, assemble_study


def test_prepare_bist_price_archive_and_scale_adjustment(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    text = "Tarih;Endeks Kodu;Endeksler;Kur Türü;Seans No;Kapanış Değeri\n26.07.2020;XUMAL;Mali;TL;1;12300.0\n27.07.2020;XUMAL;Mali;TL;1;125.0\n27.07.2020;XUSIN;Sanayi;TL;1;210.0\n"
    with zipfile.ZipFile(raw / "prices.zip", "w") as archive:
        archive.writestr("FiyatEndeksleri.csv", text.encode("cp1254"))
    out = tmp_path / "prepared"
    prepare_bist_prices(raw, out, sectors=("XUMAL", "XUSIN"))
    prices = pd.read_csv(out / "prices.csv")
    assert prices.loc[prices.date.eq("2020-07-26"), "close"].iat[0] == 123.0
    assert set(pd.read_csv(out / "calendar.csv").date) == {"2020-07-26", "2020-07-27"}
    assert set(json.loads((out / "bist_provenance.json").read_text())["series"]) == {"XUMAL", "XUSIN"}


def test_assemble_study_combines_provenance(tmp_path):
    price = tmp_path / "price"
    macro = tmp_path / "macro"
    price.mkdir(); macro.mkdir()
    (price / "prices.csv").write_text("date,sector,close\n2024-01-31,XUMAL,100\n")
    (price / "calendar.csv").write_text("date\n2024-01-31\n")
    (macro / "macro.csv").write_text("series,period,available_at,value\ncpi,2024-01-31,2024-03-06,100\n")
    entry = {"source_url":"x", "retrieved_at":"x", "unit":"x", "frequency":"x", "transformation":"x", "redistribution":"x", "vintage_policy":"x"}
    (price / "bist_provenance.json").write_text(json.dumps({"calendar":"BIST", "series":{"XUMAL":entry}}))
    (macro / "macro_provenance.json").write_text(json.dumps({"series":{"cpi":entry}}))
    out = tmp_path / "study"
    assemble_study(price, macro, out)
    provenance = json.loads((out / "provenance.json").read_text())
    assert provenance["mode"] == "research" and set(provenance["series"]) == {"XUMAL", "cpi"}
