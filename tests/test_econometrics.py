import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa.api import VAR
from bist_risk.econometrics import wald_first_k, toda_yamamoto


def generated(n=600):
    rng = np.random.default_rng(8)
    x = rng.normal(size=(n,2))
    for i in range(1,n):
        x[i,0] += .4*x[i-1,0]
        x[i,1] += .9*x[i-1,0] + .2*x[i-1,1]
    return pd.DataFrame(x, columns=["cause", "effect"])


def test_wald_matches_statsmodels_without_augmentation():
    result = VAR(generated()).fit(2)
    statistic, p, _ = wald_first_k(result, "cause", "effect", 2)
    reference = result.test_causality("effect", ["cause"], kind="wald")
    assert statistic == pytest.approx(reference.test_statistic)
    assert p == pytest.approx(reference.pvalue)


def test_augmented_lags_excluded_from_restrictions():
    result = VAR(generated()).fit(3)
    _, _, r = wald_first_k(result, "cause", "effect", 1)
    assert r.shape == (1, result.params.size)
    assert np.count_nonzero(r) == 1
    assert np.count_nonzero(r[:, (1+2)*2:]) == 0


def test_known_predictive_direction():
    result = toda_yamamoto(generated(), "cause", "effect")
    assert result["p_value"] < .001
    assert result["k"] >= 1


def test_internal_time_gaps_are_rejected():
    x = generated(72)
    x.index = pd.date_range("2019-01-31", periods=72, freq="ME")
    with pytest.raises(ValueError, match="gaps"):
        toda_yamamoto(x.drop(x.index[20]), "cause", "effect")
