---
name: policy-evaluator
description: "Cost-effectiveness analysis (CEA/CUA), DALY estimation, budget-constrained resource..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [cost-effectiveness, DALY, CEA, CUA, health-economics, resource-allocation]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"⚖️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["policy","policy evaluator","cost-effectiveness","daly","cost per daly","health economics","cea","cua","icer","who threshold"]}}
---

# ⚖️ Policy Evaluator

Use this skill when the user needs cost-effectiveness analysis (CEA/CUA), DALY estimation, budget-constrained resource allocation optimization.

## OpenClaw Routing

- Route here for: `policy`, `policy evaluator`, `cost-effectiveness`, `daly`, `cost per daly`, `health economics`
- Alias: `policy`
- Entrypoint: `skills/policy-evaluator/policy_evaluator.py`
- Expected inputs: 2×2 tables, cohorts, study summaries, regression-ready tabular data, or study-design assumptions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `epi-analyst`, `meta-analysis`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `policy`
- `policy evaluator`
- `cost-effectiveness`
- `daly`
- `cost per daly`
- `health economics`
- `cea`
- `cua`
- `icer`
- `who threshold`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python policy_evaluator.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
