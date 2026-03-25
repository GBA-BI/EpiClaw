---
name: syndromic-surveillance
description: "NLP syndrome extraction from unstructured clinical text; multivariate aberration..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [syndromic-surveillance, emergency-department, EWMA, aberration-detection, pre-diagnostic]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🩺","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]}],"trigger_keywords":["syndromic","syndromic surveillance","ili","influenza-like illness","ed visits","emergency department","pre-diagnostic","syndrome","ewma"]}}
---

# 🩺 Syndromic Surveillance

Use this skill when the user needs NLP syndrome extraction from unstructured clinical text; multivariate aberration detection.

## OpenClaw Routing

- Route here for: `syndromic`, `syndromic surveillance`, `ili`, `influenza-like illness`, `ed visits`, `emergency department`
- Alias: `syndromic`
- Entrypoint: `skills/syndromic-surveillance/syndromic_surveillance.py`
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

- `syndromic`
- `syndromic surveillance`
- `ili`
- `influenza-like illness`
- `ed visits`
- `emergency department`
- `pre-diagnostic`
- `syndrome`
- `ewma`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python syndromic_surveillance.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
