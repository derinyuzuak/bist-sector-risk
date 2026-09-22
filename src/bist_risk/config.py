"""Validation for the small, explicit research configuration."""
from pathlib import Path
import tomllib
import pandas as pd


def load_config(path: str | Path) -> dict:
    with Path(path).open("rb") as stream:
        config = tomllib.load(stream)
    study = config["study"]
    if pd.Timestamp(study["start"]) >= pd.Timestamp(study["end"]) or study["validation_year"] >= study["test_year"]:
        raise ValueError("Invalid study dates")
    if config["model"]["feature_selection"] not in {"toda_yamamoto", "all"}:
        raise ValueError("Unsupported feature selection")
    if not study["sectors"] or study["min_days"] < 1:
        raise ValueError("At least one sector and one scheduled session are required")
    return config
