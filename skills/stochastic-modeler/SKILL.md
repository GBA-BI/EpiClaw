---
name: stochastic-modeler
description: "Gillespie algorithm and tau-leaping stochastic SEIR simulations; ensemble runs;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [stochastic-model, Gillespie, tau-leaping, SIR, SEIR, extinction-probability, superspreading]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🎲","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["stochastic","stochastic modeler","stochastic epidemic","gillespie","tau-leaping","extinction probability","outbreak uncertainty","superspreading","dispersion parameter","k parameter"]}}
---

# 🎲 Stochastic Modeler

Use this skill when the user needs gillespie algorithm and tau-leaping stochastic SEIR simulations; ensemble runs; extinction probability; superspreading (negative binomial offspring).

## OpenClaw Routing

- Route here for: `stochastic`, `stochastic modeler`, `stochastic epidemic`, `gillespie`, `tau-leaping`, `extinction probability`
- Alias: `stochastic`
- Entrypoint: `skills/stochastic-modeler/stochastic_modeler.py`
- Expected inputs: Case time series, epidemiological parameters, population size, and scenario assumptions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `disease-forecaster`, `rt-estimator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `stochastic`
- `stochastic modeler`
- `stochastic epidemic`
- `gillespie`
- `tau-leaping`
- `extinction probability`
- `outbreak uncertainty`
- `superspreading`
- `dispersion parameter`
- `k parameter`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python stochastic_modeler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
