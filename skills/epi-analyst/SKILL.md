---
name: epi-analyst
description: "CDC 10-step outbreak investigation framework, Bradford Hill causality criteria, study..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [epidemiology, outbreak, surveillance, causal-inference]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🔬","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"pandas","bins":[]}],"trigger_keywords":["epi analyst","epidemiological analysis","bradford hill","causal inference","study design","surveillance system","public health assessment","outbreak framework"]}}
---

# 🔬 Epi Analyst

Use this skill when the user needs CDC 10-step outbreak investigation framework, Bradford Hill causality criteria, study design consultation.

## OpenClaw Routing

- Route here for: `epi analyst`, `epidemiological analysis`, `bradford hill`, `causal inference`, `study design`, `surveillance system`
- Alias: `epi-analyst`
- Entrypoint: `skills/epi-analyst/epi_analyst.py`
- Expected inputs: Linelists, case counts, exposure histories, contact networks, or outbreak framing questions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `contact-tracing`, `rt-estimator`, `epi-orchestrator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `epi analyst`
- `epidemiological analysis`
- `bradford hill`
- `causal inference`
- `study design`
- `surveillance system`
- `public health assessment`
- `outbreak framework`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python epi_analyst.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
