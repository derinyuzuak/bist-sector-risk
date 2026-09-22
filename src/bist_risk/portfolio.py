"""Index-return simulation, not executable trading or a licensed benchmark."""
import numpy as np
import pandas as pd


def simulate(predictions, costs=(0, 10, 25, 50), floor=.01):
    vol = predictions[(predictions.target == "volatility") & (predictions.model == "xgboost")].pivot(index="target_date", columns="sector", values="prediction")
    ret = predictions[(predictions.target == "return") & (predictions.model == "xgboost")].pivot(index="target_date", columns="sector", values="actual")
    if not vol.index.equals(ret.index) or not vol.columns.equals(ret.columns) or vol.isna().any().any() or ret.isna().any().any():
        raise ValueError("Portfolio requires a common complete sector/date universe")
    inverse = 1 / vol.clip(lower=floor)
    weights = inverse.div(inverse.sum(axis=1), axis=0)
    equal = weights * 0 + 1 / len(weights.columns)
    paths, summaries, weight_rows = [], [], []
    for strategy, ws in [("inverse_forecast_vol", weights), ("equal_weight", equal)]:
        for date, w in ws.iterrows():
            weight_rows.extend(dict(date=date, strategy=strategy, sector=s, weight=float(v)) for s, v in w.items())
        for bps in costs:
            wealth, peak, previous = 1., 1., np.zeros(len(ws.columns))
            drawdowns = []
            for date, w in ws.iterrows():
                # Sum of absolute traded notional: initial full deployment = 1.
                turnover = float(np.abs(w.to_numpy()-previous).sum())
                gross = float(w @ ret.loc[date])
                net = (1 - bps/10000 * turnover) * (1 + gross) - 1
                wealth *= 1 + net
                peak = max(peak, wealth)
                dd = wealth/peak - 1
                drawdowns.append(dd)
                paths.append(dict(date=date, strategy=strategy, cost_bps=bps, gross_return=gross,
                                  net_return=net, turnover=turnover, wealth=wealth, drawdown=dd))
                previous = (w.to_numpy()*(1+ret.loc[date].to_numpy()))/(1+gross)
            summaries.append(dict(strategy=strategy, cost_bps=bps, total_return=wealth-1, max_drawdown=min(drawdowns), months=len(ws)))
    return pd.DataFrame(paths), pd.DataFrame(summaries), pd.DataFrame(weight_rows)
