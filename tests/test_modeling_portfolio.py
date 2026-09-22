import numpy as np
import pandas as pd
import pytest
from bist_risk.modeling import training_rows, supervised, evaluate_sector
from bist_risk.config import load_config
from bist_risk.portfolio import simulate
from pathlib import Path


def test_only_matured_targets_enter_training():
    frame = pd.DataFrame(dict(target_date=pd.to_datetime(["2022-12-31", "2023-01-31"]), target_return=[1,999], target_volatility=[1,999]))
    assert len(training_rows(frame, pd.Timestamp("2022-12-31"), 1)) == 1


def test_test_year_changes_do_not_change_fit_or_first_forecast():
    rng = np.random.default_rng(4)
    dates = pd.date_range("2019-01-31", periods=72, freq="ME")
    m = pd.DataFrame(dict(date=dates, return_value=rng.normal(0,.04,72), volatility=rng.uniform(.1,.3,72)))
    macro = pd.DataFrame({"macro":rng.normal(size=72)}, index=dates)
    config = load_config(Path(__file__).parents[1]/"config.toml")
    config["model"].update(feature_selection="all", trees=5, depths=[1], ridge_alphas=[1.])
    p1,s1 = evaluate_sector(supervised(m, macro), ["macro"], config, "A")
    m.loc[m.date.dt.year == 2024, "return_value"] += 10
    p2,s2 = evaluate_sector(supervised(m, macro), ["macro"], config, "A")
    pd.testing.assert_frame_equal(s1,s2)
    np.testing.assert_allclose(p1[p1.target_date == "2024-01-31"].prediction, p2[p2.target_date == "2024-01-31"].prediction)
    assert (p2.fit_until == pd.Timestamp("2023-12-31")).all()


def portfolio_fixture():
    rows = []
    for date in pd.to_datetime(["2024-01-31", "2024-02-29"]):
        for sector, vol, ret in [("A",.1,.1),("B",.2,0.)]:
            rows.append(dict(target_date=date, sector=sector, target="volatility", model="xgboost", prediction=vol, actual=vol))
            rows.append(dict(target_date=date, sector=sector, target="return", model="xgboost", prediction=0., actual=ret))
    return pd.DataFrame(rows)


def test_weights_costs_drift_and_drawdown():
    paths, summaries, weights = simulate(portfolio_fixture(), costs=[0,100])
    np.testing.assert_allclose(weights.groupby(["date","strategy"]).weight.sum(), 1)
    assert (weights.weight >= 0).all()
    np.testing.assert_allclose(weights[(weights.strategy == "inverse_forecast_vol") & (weights.sector == "A")].weight, 2/3)
    free = paths[(paths.strategy == "equal_weight") & (paths.cost_bps == 0)]
    assert free.iloc[0].turnover == pytest.approx(1)
    assert free.iloc[1].turnover == pytest.approx(2*abs(.5-.55/1.05))
    paid = summaries[summaries.cost_bps == 100].set_index("strategy")
    unpaid = summaries[summaries.cost_bps == 0].set_index("strategy")
    assert (paid.total_return < unpaid.total_return).all()
    assert (summaries.max_drawdown <= 0).all()


def test_incomplete_portfolio_rejected():
    with pytest.raises(ValueError, match="complete"):
        simulate(portfolio_fixture().iloc[1:])
