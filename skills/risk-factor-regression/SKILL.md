---
name: risk-factor-regression
description: "Multivariate logistic and Poisson regression for risk factor analysis; confounder..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [logistic-regression, risk-factors, multivariable, confounder, odds-ratio, Poisson-regression]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"📊","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["regression","risk factor regression","logistic regression","risk factors","multivariable","confounder adjustment","odds ratio adjusted","poisson regression","relative risk regression","effect modification"]}}
---

# 📊 Risk Factor Regression

Use this skill when the user needs multivariate logistic and Poisson regression for risk factor analysis; confounder adjustment; OR/RR with 95% CIs; model diagnostics.

## OpenClaw Routing

- Route here for: `regression`, `risk factor regression`, `logistic regression`, `risk factors`, `multivariable`, `confounder adjustment`
- Alias: `regression`
- Entrypoint: `skills/risk-factor-regression/risk_factor_regression.py`
- Expected inputs: 2×2 tables, cohorts, study summaries, regression-ready tabular data, or study-design assumptions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `epi-analyst`, `meta-analysis`, `policy-evaluator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `regression`
- `risk factor regression`
- `logistic regression`
- `risk factors`
- `multivariable`
- `confounder adjustment`
- `odds ratio adjusted`
- `poisson regression`
- `relative risk regression`
- `effect modification`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python risk_factor_regression.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
