---
name: early-warning-system
description: "Aberration detection (CUSUM, EARS, Farrington) and multi-signal early warning alerts"
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [surveillance, aberration-detection, early-warning, CUSUM, EARS]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"⚠️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]}],"trigger_keywords":["ews","early warning system","aberration detection","cusum","early warning","surveillance alert","outbreak signal","unusual increase","ears","farrington"]}}
---

# ⚠️ Early Warning System

Use this skill when the user needs aberration detection (CUSUM, EARS, Farrington) and multi-signal early warning alerts.

## OpenClaw Routing

- Route here for: `ews`, `early warning system`, `aberration detection`, `cusum`, `early warning`, `surveillance alert`
- Alias: `ews`
- Entrypoint: `skills/early-warning-system/early_warning.py`
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

- `ews`
- `early warning system`
- `aberration detection`
- `cusum`
- `early warning`
- `surveillance alert`
- `outbreak signal`
- `unusual increase`
- `ears`
- `farrington`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python early_warning.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
