---
name: network-epidemic-model
description: "SIR/SIS epidemic simulation on contact networks (NetworkX/EoN); heterogeneous mixing;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [network, contact-network, SIR, heterogeneous-mixing, scale-free, small-world]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🕸️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["net model","network epidemic model","network epidemic","contact network","scale-free network","small world","heterogeneous mixing","network sir","degree distribution","herd immunity threshold"]}}
---

# 🕸️ Network Epidemic Model

Use this skill when the user needs SIR/SIS epidemic simulation on contact networks (NetworkX/EoN); heterogeneous mixing; degree distribution effects on R₀.

## OpenClaw Routing

- Route here for: `net model`, `network epidemic model`, `network epidemic`, `contact network`, `scale-free network`, `small world`
- Alias: `net-model`
- Entrypoint: `skills/network-epidemic-model/network_epidemic_model.py`
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

- `net model`
- `network epidemic model`
- `network epidemic`
- `contact network`
- `scale-free network`
- `small world`
- `heterogeneous mixing`
- `network sir`
- `degree distribution`
- `herd immunity threshold`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python network_epidemic_model.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
