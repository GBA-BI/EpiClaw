---
name: within-host-modeler
description: "Viral dynamics within-host ODE models (target-cell limited, eclipse phase, immune..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [within-host, viral-dynamics, target-cell, viral-load, pharmacodynamics]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🦠","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["within host","within host modeler","within-host","viral dynamics","viral load","target cell","viral kinetics","infection dynamics","antiviral","eclipse phase"]}}
---

# 🦠 Within-Host Modeler

Use this skill when the user needs viral dynamics within-host ODE models (target-cell limited, eclipse phase, immune response); parameter fitting to viral load data.

## OpenClaw Routing

- Route here for: `within host`, `within host modeler`, `within-host`, `viral dynamics`, `viral load`, `target cell`
- Alias: `within-host`
- Entrypoint: `skills/within-host-modeler/within_host_modeler.py`
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

- `within host`
- `within host modeler`
- `within-host`
- `viral dynamics`
- `viral load`
- `target cell`
- `viral kinetics`
- `infection dynamics`
- `antiviral`
- `eclipse phase`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python within_host_modeler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
