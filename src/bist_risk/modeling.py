"""Fixed holdout and nested training-only feature selection."""
import json
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from .econometrics import family_tests


def supervised(monthly, macro):
    x = monthly.set_index("date")[["return_value", "volatility"]].join(macro)
    # Level and change features are computed without future information.
    for name in macro:
        x[name + "_change"] = x[name].diff()
    x["target_date"] = x.index + pd.offsets.MonthEnd(1)
    x["target_return"] = x.return_value.shift(-1)
    x["target_volatility"] = x.volatility.shift(-1)
    return x


def training_rows(frame, origin, min_train):
    train = frame[(frame.target_date <= origin)].dropna(subset=["target_return", "target_volatility"])
    if len(train) < min_train:
        raise ValueError("Insufficient historical training targets")
    return train


def build_model(name, setting, config):
    if name == "ridge":
        return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), Ridge(alpha=setting))
    return XGBRegressor(n_estimators=config["model"]["trees"], max_depth=int(setting),
                        learning_rate=.04, reg_lambda=10, min_child_weight=5,
                        subsample=1, colsample_bytree=1, random_state=config["study"]["seed"], n_jobs=1)


def features_at(frame, origin, target, macro_names, config):
    # Screening observes only values available at/before forecast origin.
    history = frame.loc[frame.index <= origin]
    effect = "return_value" if target == "return" else "volatility"
    settings = config["econometrics"]
    selected = list(macro_names)
    if config["model"]["feature_selection"] == "toda_yamamoto":
        tests = family_tests(history, macro_names, effect, settings)
        selected = tests.loc[(tests.q_value < settings["alpha"]) & (tests.get("residual_ok", False) == True), "cause"].tolist()
    return ["return_value", "volatility"] + [f for name in selected for f in (name, name+"_change")]


def evaluate_sector(frame, macro_names, config, sector):
    validation_year, test_year = config["study"]["validation_year"], config["study"]["test_year"]
    rows, selections = [], []
    candidates = [("ridge", a) for a in config["model"]["ridge_alphas"]] + [("xgboost", d) for d in config["model"]["depths"]]
    for target in ["return", "volatility"]:
        ycol = "target_" + target
        cache = {}
        for origin, row in frame[frame.target_date.dt.year == validation_year].iterrows():
            train = training_rows(frame, origin, config["model"]["min_train"])
            features = features_at(frame, origin, target, macro_names, config)
            cache[origin] = (train, features)
        scores = []
        for name, setting in candidates:
            errors = []
            for origin, (train, features) in cache.items():
                model = build_model(name, setting, config).fit(train[features], train[ycol])
                pred = float(model.predict(frame.loc[[origin], features])[0])
                if target == "volatility":
                    pred = max(0, pred)
                errors.append(abs(pred - frame.loc[origin, ycol]))
            scores.append(dict(model=name, setting=setting, validation_mae=float(np.mean(errors))))
        chosen = {name: min([s for s in scores if s["model"] == name], key=lambda s:s["validation_mae"]) for name in ["ridge", "xgboost"]}
        selections.extend(dict(sector=sector, target=target, **s) for s in scores)
        # The 2024 holdout uses frozen models trained at 2023-12, including known Dec targets.
        # No 2024 observations affect fitting or screening; lagged predictors remain observable.
        origin = pd.Timestamp(test_year-1, 12, 31)
        train = training_rows(frame, origin, config["model"]["min_train"])
        features = features_at(frame, origin, target, macro_names, config)
        test = frame[frame.target_date.dt.year == test_year].dropna(subset=[ycol])
        for name, choice in chosen.items():
            model = build_model(name, choice["setting"], config).fit(train[features], train[ycol])
            predictions = model.predict(test[features])
            if target == "volatility":
                predictions = np.maximum(0, predictions)
            for (date, item), pred in zip(test.iterrows(), predictions):
                rows.append(dict(sector=sector, target=target, model=name, origin=date, target_date=item.target_date,
                                 actual=item[ycol], prediction=float(pred), fit_until=origin,
                                 features=json.dumps(features)))
        for date, item in test.iterrows():
            for name, value in [("historical_mean", train[ycol].mean()),
                                ("persistence", item["return_value" if target == "return" else "volatility"])]:
                rows.append(dict(sector=sector, target=target, model=name, origin=date, target_date=item.target_date,
                                 actual=item[ycol], prediction=float(value), fit_until=origin, features="[]"))
    return pd.DataFrame(rows), pd.DataFrame(selections)


def metrics(predictions, seed=2209):
    rows = []
    rng = np.random.default_rng(seed)
    for (sector, target, model), g in predictions.groupby(["sector", "target", "model"]):
        errors = (g.sort_values("target_date").prediction - g.sort_values("target_date").actual).to_numpy()
        n = len(errors)
        # Circular block bootstrap, block=3 months; descriptive, small-sample uncertainty.
        starts = rng.integers(0, n, size=(1000, int(np.ceil(n/3))))
        indices = ((starts[..., None] + np.arange(3)) % n).reshape(1000, -1)[:, :n]
        boot = np.abs(errors[indices]).mean(axis=1)
        low, high = np.quantile(boot, [.025, .975])
        rows.append(dict(sector=sector, target=target, model=model, n=n, mae=float(np.abs(errors).mean()),
                         rmse=float(np.sqrt(np.mean(errors**2))), mae_low=float(low), mae_high=float(high)))
    out = pd.DataFrame(rows)
    baseline = out[out.model == "historical_mean"][["sector", "target", "mae"]].rename(columns={"mae":"baseline_mae"})
    out = out.merge(baseline, on=["sector", "target"])
    out["mae_improvement"] = 1 - out.mae / out.baseline_mae.replace(0, np.nan)
    return out
