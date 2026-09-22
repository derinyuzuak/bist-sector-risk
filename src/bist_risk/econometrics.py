"""Lag-augmented VAR with explicit first-k-lag Wald restrictions."""
import numpy as np
import pandas as pd
from inspect import signature
from scipy.stats import chi2
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.multitest import multipletests

_ADF_OPTIONS = {"result_object": False} if "result_object" in signature(adfuller).parameters else {}


def integration_order(series, alpha=.05, max_order=2):
    x = pd.Series(series).dropna().astype(float)
    records = []
    for order in range(max_order + 1):
        if len(x) < 20 or x.nunique() < 3:
            raise ValueError("Insufficient variation/observations for ADF")
        stat, p, lag, n, *_ = adfuller(x, maxlag=min(3, len(x)//5-1), regression="c", autolag="BIC", **_ADF_OPTIONS)
        records.append(dict(order=order, statistic=float(stat), p_value=float(p), lag=int(lag), n=int(n)))
        if p < alpha:
            return order, records
        x = x.diff().dropna()
    raise ValueError("Integration order unresolved within configured maximum")


def wald_first_k(result, cause, effect, k):
    """statsmodels params/cov_params order: regressor major, equation minor."""
    names = list(result.names)
    n = len(names)
    c, e = names.index(cause), names.index(effect)
    params = np.asarray(result.params)
    restriction = np.zeros((k, params.size))
    for lag in range(1, k + 1):
        restriction[lag-1, (result.k_trend + (lag-1)*n + c)*n + e] = 1
    beta = params.reshape(-1)
    covariance = restriction @ np.asarray(result.cov_params()) @ restriction.T
    if np.linalg.matrix_rank(covariance) != k:
        raise ValueError("Singular Wald covariance")
    rb = restriction @ beta
    statistic = float(rb @ np.linalg.solve(covariance, rb))
    return statistic, float(chi2.sf(statistic, k)), restriction


def toda_yamamoto(frame, cause, effect, max_lags=3, alpha=.05, max_integration=2):
    x = frame[[cause, effect]].dropna().astype(float)
    if len(x) < 25:
        raise ValueError("Too few complete observations for pairwise VAR")
    if isinstance(x.index, pd.DatetimeIndex) and len(x.index.to_period("M").unique()) != (x.index.max().to_period("M")-x.index.min().to_period("M")).n+1:
        raise ValueError("Internal monthly gaps: VAR cannot compress calendar time")
    if isinstance(x.index, pd.DatetimeIndex):
        x = x.asfreq("ME")
    orders, adf = {}, {}
    for col in x:
        orders[col], adf[col] = integration_order(x[col], alpha, max_integration)
    dmax = max(orders.values())
    # Use a common sample for BIC comparisons. k must accommodate suspected order.
    upper = min(max_lags, (len(x)-12)//4)
    if upper < max(1, dmax):
        raise ValueError("Insufficient sample for admissible lag order")
    model = VAR(x.to_numpy())
    selection = model.select_order(upper)
    k = max(1, dmax, int(selection.selected_orders["bic"]))
    result = VAR(x).fit(k + dmax, trend="c")
    statistic, p, _ = wald_first_k(result, cause, effect, k)
    white = result.test_whiteness(nlags=k+dmax+2, adjusted=True)
    return dict(cause=cause, effect=effect, k=k, dmax=dmax, n=int(result.nobs),
                statistic=statistic, p_value=p, whiteness_p=float(white.pvalue),
                residual_ok=bool(white.pvalue >= alpha), adf=adf)


def family_tests(frame, causes, effect, settings):
    results = []
    for cause in causes:
        try:
            row = toda_yamamoto(frame, cause, effect, **settings)
            row.pop("adf")
            row["status"] = "ok"
        except (ValueError, np.linalg.LinAlgError) as exc:
            row = dict(cause=cause, effect=effect, status=str(exc), p_value=np.nan)
        results.append(row)
    df = pd.DataFrame(results)
    df["q_value"] = np.nan
    valid = df.p_value.notna()
    if valid.any():
        df.loc[valid, "q_value"] = multipletests(df.loc[valid, "p_value"], method="fdr_bh")[1]
    return df
