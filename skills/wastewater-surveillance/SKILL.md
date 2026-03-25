---
name: wastewater-surveillance
description: "Wastewater-based epidemiology (WBE): normalize concentration data, correlate with..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [wastewater, WBE, environmental-surveillance, SARS-CoV-2, normalization]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🚰","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["wbe","wastewater surveillance","wastewater","wastewater-based epidemiology","environmental surveillance","sewage","pmmov","concentration","sars-cov-2 wastewater"]}}
---

# 🚰 Wastewater Surveillance

Use this skill when the user needs wastewater-based epidemiology (WBE): normalize concentration data, correlate with clinical cases, detect trends.

## OpenClaw Routing

- Route here for: `wbe`, `wastewater surveillance`, `wastewater`, `wastewater-based epidemiology`, `environmental surveillance`, `sewage`
- Alias: `wbe`
- Entrypoint: `skills/wastewater-surveillance/wastewater_surveillance.py`
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

- `wbe`
- `wastewater surveillance`
- `wastewater`
- `wastewater-based epidemiology`
- `environmental surveillance`
- `sewage`
- `pmmov`
- `concentration`
- `sars-cov-2 wastewater`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python wastewater_surveillance.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
