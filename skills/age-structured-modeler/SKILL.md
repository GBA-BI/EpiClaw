---
name: age-structured-modeler
description: "Age-structured SEIR with POLYMOD contact matrices; age-specific attack rates; age-..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [age-structured, SEIR, POLYMOD, contact-matrix, vaccination, age-specific]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"👶","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["age model","age structured modeler","age-structured model","age-specific","polymod","contact matrix","age groups","elderly vaccination","pediatric","age-dependent risk"]}}
---

# 👶 Age-Structured Modeler

Use this skill when the user needs age-structured SEIR with POLYMOD contact matrices; age-specific attack rates; age-targeted vaccination impact analysis.

## OpenClaw Routing

- Route here for: `age model`, `age structured modeler`, `age-structured model`, `age-specific`, `polymod`, `contact matrix`
- Alias: `age-model`
- Entrypoint: `skills/age-structured-modeler/age_structured_modeler.py`
- Expected inputs: Case time series, epidemiological parameters, population size, and scenario assumptions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `disease-forecaster`, `stochastic-modeler`, `rt-estimator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `age model`
- `age structured modeler`
- `age-structured model`
- `age-specific`
- `polymod`
- `contact matrix`
- `age groups`
- `elderly vaccination`
- `pediatric`
- `age-dependent risk`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python age_structured_modeler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
