---
name: seroprevalence
description: "Seroprevalence survey analysis: weighted prevalence estimates, IFR calculation,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [seroprevalence, IFR, antibody-survey, population-immunity, Rogan-Gladen]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🩸","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]}],"trigger_keywords":["sero","seroprevalence","antibody survey","ifr","infection fatality ratio","population immunity","serology","rogan-gladen","serosurvey"]}}
---

# 🩸 Seroprevalence

Use this skill when the user needs seroprevalence survey analysis: weighted prevalence estimates, IFR calculation, population immunity assessment, test performance adjustment.

## OpenClaw Routing

- Route here for: `sero`, `seroprevalence`, `antibody survey`, `ifr`, `infection fatality ratio`, `population immunity`
- Alias: `sero`
- Entrypoint: `skills/seroprevalence/seroprevalence.py`
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

- `sero`
- `seroprevalence`
- `antibody survey`
- `ifr`
- `infection fatality ratio`
- `population immunity`
- `serology`
- `rogan-gladen`
- `serosurvey`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python seroprevalence.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
