# Macroeconomic Shocks and Investor Risk Perception in Borsa Istanbul

**A reproducible empirical study of macroeconomic shocks, sector returns and the volatility-based proxy for investor risk perception.**

[Türkçe](README.tr.md) · [Methodology](docs/methodology.md) · [Data guide](docs/data.md) · [References](docs/references.md)

This repository implements the January 2019–December 2024 ADF, Toda–Yamamoto and XGBoost framework with real data. Stored results were generated from daily `XBANK` and `XUSIN` index closes and EVDS macro series. Raw data and API credentials are not included. Executed Jupyter notebooks are the primary research narrative; `src/` contains small reusable calculation helpers.

> **Scope:** `XBANK` is a banking-index proxy, not the broad financial index. `XUSIN` is the industrial index. Representatives without verified continuous Yahoo Finance history were excluded. Findings are limited to two indexes, 72 months and a 12-month final evaluation period.

## Run

Python 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts\verify_results.py results\research
.\.venv\Scripts\python scripts\execute_notebooks.py
.\.venv\Scripts\python -m streamlit run app.py
```

The dashboard and notebooks use the stored real outputs in `results/research/` by default. To regenerate the analysis, prepare local raw inputs according to the [data guide](docs/data.md), then run `fetch-evds`, `prepare-evds`, `prepare-yahoo`, `assemble-study`, `validate`, and `scripts/execute_notebooks.py`.

## Contents

| Path | Contents |
|---|---|
| `results/research/` | Derived real-result tables, generated Turkish report and verification manifest |
| `notebooks/` | Four notebooks that show real-data decisions and analysis cell by cell |
| `src/bist_risk/` | Data preparation, ADF, Toda–Yamamoto, modelling and portfolio engine |
| `tests/` | Date alignment, no-look-ahead, Wald restrictions, price and portfolio tests |
| `docs/` | Methods, data contract, corrections, references and publication guide |

## Notebook route

1. `01_data_collection_and_quality.ipynb`: source, coverage, trading-session and release-time checks.
2. `02_eda_and_econometrics.ipynb`: EDA, ADF and Toda–Yamamoto tables.
3. `03_forecasting_backtest.ipynb`: chronological train/validation/test work and model comparison.
4. `04_portfolio_and_conclusions.ipynb`: portfolio simulation, manifest and report generation.

## Interpretation

Volatility is an indirect market-risk proxy. Toda–Yamamoto relationships do not establish structural causality. Model selection stops at 2023; 2024 is the untouched final period. The 12-month holdout is small, and the portfolio is a non-levered index research simulation, not investment advice.

## GitHub status

No raw data, credential or personal file is included. This repository was published to GitHub with the project owner's approval.
