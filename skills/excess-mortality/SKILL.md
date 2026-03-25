---
name: excess-mortality
description: "Estimate excess mortality using P-scores, Z-scores, and Farrington baseline..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [excess-mortality, mortality, P-score, Z-score, COVID-19, death-surveillance]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"📉","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]}],"trigger_keywords":["excess","excess mortality","excess deaths","p-score","z-score","baseline mortality","covid mortality","all-cause mortality","mortality surplus"]}}
---

# 📉 Excess Mortality

Use this skill when the user needs estimate excess mortality using P-scores, Z-scores, and Farrington baseline modelling; account for reporting delays.

## OpenClaw Routing

- Route here for: `excess`, `excess mortality`, `excess deaths`, `p-score`, `z-score`, `baseline mortality`
- Alias: `excess`
- Entrypoint: `skills/excess-mortality/excess_mortality.py`
- Expected inputs: Time series, surveillance tables, syndromic counts, wastewater measurements, or country/pathogen context.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `multi-pathogen-dashboard`, `rt-estimator`, `epi-orchestrator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `excess`
- `excess mortality`
- `excess deaths`
- `p-score`
- `z-score`
- `baseline mortality`
- `covid mortality`
- `all-cause mortality`
- `mortality surplus`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python excess_mortality.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
