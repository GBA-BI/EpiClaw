---
name: sample-size-calculator
description: "Power and sample size calculations for cohort, case-control, RCT, cross-sectional,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [sample-size, power-calculation, study-design, cohort, case-control, RCT]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"📐","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["samplesize","sample size calculator","sample size","power calculation","study design","power analysis","cohort sample size","case-control sample size","rct sample size","detectable difference"]}}
---

# 📐 Sample Size Calculator

Use this skill when the user needs power and sample size calculations for cohort, case-control, RCT, cross-sectional, and cluster-randomized study designs.

## OpenClaw Routing

- Route here for: `samplesize`, `sample size calculator`, `sample size`, `power calculation`, `study design`, `power analysis`
- Alias: `samplesize`
- Entrypoint: `skills/sample-size-calculator/sample_size_calculator.py`
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

- `samplesize`
- `sample size calculator`
- `sample size`
- `power calculation`
- `study design`
- `power analysis`
- `cohort sample size`
- `case-control sample size`
- `rct sample size`
- `detectable difference`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python sample_size_calculator.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
