---
name: multi-pathogen-dashboard
description: "Aggregate multi-pathogen surveillance trends, detect anomalies, generate HTML dashboard"
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [surveillance, dashboard, multi-pathogen, trends]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"📊","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["dashboard","multi pathogen dashboard","surveillance trends","multi-pathogen","surveillance report","disease trends"]}}
---

# 📊 Multi-Pathogen Dashboard

Use this skill when the user needs aggregate multi-pathogen surveillance trends, detect anomalies, generate HTML dashboard.

## OpenClaw Routing

- Route here for: `dashboard`, `multi pathogen dashboard`, `surveillance trends`, `multi-pathogen`, `surveillance report`, `disease trends`
- Alias: `dashboard`
- Entrypoint: `skills/multi-pathogen-dashboard/dashboard.py`
- Expected inputs: Time series, surveillance tables, syndromic counts, wastewater measurements, or country/pathogen context.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `rt-estimator`, `epi-orchestrator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `dashboard`
- `multi pathogen dashboard`
- `surveillance trends`
- `multi-pathogen`
- `surveillance report`
- `disease trends`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python dashboard.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
