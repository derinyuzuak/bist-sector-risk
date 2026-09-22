"""Validate saved outputs independently of UI and report rendering."""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
from bist_risk.data import sha256

out = Path(sys.argv[1])
m = json.loads((out/"manifest.json").read_text(encoding="utf-8"))
for name, digest in m["result_hashes"].items():
    assert sha256(out/f"{name}.csv") == digest, name
p = pd.read_csv(out/"predictions.csv", parse_dates=["origin","target_date","fit_until"])
assert (p.origin < p.target_date).all()
assert (p.fit_until <= p.origin).all()
assert (p.target_date.dt.year == m["config"]["study"]["test_year"]).all()
assert np.isfinite(p[["actual","prediction"]]).all().all()
assert (p.groupby(["sector","target","model"]).size() == 12).all()
w = pd.read_csv(out/"weights.csv")
assert (w.weight >= 0).all()
np.testing.assert_allclose(w.groupby(["date","strategy"]).weight.sum(), 1)
assert m["mode"] == "research"
assert "GERÇEK VERİ ANALİZİ" in (out/"report_tr.md").read_text(encoding="utf-8")
print("Verified hashes, temporal ordering, finite predictions, holdout coverage and portfolio weights.")
