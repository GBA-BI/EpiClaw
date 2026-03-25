---
name: disease-forecaster
description: "Time-series disease forecasting with Prophet, statsmodels SARIMAX; multi-horizon..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [forecasting, time-series, Holt-Winters, ARIMA, epidemic-projection]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🔮","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["forecast","disease forecaster","predict cases","case projection","epidemic forecast","time series","future cases","case prediction","epidemic projection"]}}
---

# 🔮 Disease Forecaster

Use this skill when the user needs time-series disease forecasting with Prophet, statsmodels SARIMAX; multi-horizon projections with prediction intervals.

## OpenClaw Routing

- Route here for: `forecast`, `disease forecaster`, `predict cases`, `case projection`, `epidemic forecast`, `time series`
- Alias: `forecast`
- Entrypoint: `skills/disease-forecaster/disease_forecaster.py`
- Expected inputs: Case time series, epidemiological parameters, population size, and scenario assumptions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `stochastic-modeler`, `rt-estimator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `forecast`
- `disease forecaster`
- `predict cases`
- `case projection`
- `epidemic forecast`
- `time series`
- `future cases`
- `case prediction`
- `epidemic projection`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python disease_forecaster.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
