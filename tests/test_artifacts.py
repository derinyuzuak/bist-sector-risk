import json
import pandas as pd

from bist_risk.artifacts import create_manifest, sha256, write_tables, write_turkish_report


def test_notebook_artifacts_are_hashed_and_reported(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in ["prices.csv", "macro.csv", "calendar.csv", "provenance.json"]:
        (inputs / name).write_text("fixture", encoding="utf-8")
    output = tmp_path / "results"
    tables = {
        "quality": pd.DataFrame([{"sector":"XUSIN", "eligible":True, "months":72, "reason":"complete"}]),
        "metrics": pd.DataFrame([{"sector":"XUSIN", "target":"return", "model":"ridge", "mae":.1}]),
        "portfolio_summary": pd.DataFrame([{"strategy":"equal_weight", "cost_bps":0, "total_return":.1, "max_drawdown":-.1, "months":12}]),
    }
    write_tables(output, tables)
    config = {"study":{"start":"2019-01-01", "end":"2024-12-31", "min_days":10}}
    manifest = create_manifest(output, config, {"series":{}}, ["XUSIN"], inputs, tables)
    write_turkish_report(output, manifest)
    saved = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert saved["mode"] == "research"
    assert saved["result_hashes"]["metrics"] == sha256(output / "metrics.csv")
    assert "GERÇEK VERİ ANALİZİ" in (output / "report_tr.md").read_text(encoding="utf-8")
