---
name: disease-profiler
description: "Comprehensive 10-dimension disease profile: pathogen, ICD-10, transmission, CFR,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [disease, research, epidemiology, WHO, public-health]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"\ud83e\udda0","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"requests","bins":[]}],"trigger_keywords":["disease profile","disease profiler","disease overview","disease burden","disease epidemiology","malaria profile","tuberculosis profile","pathogen overview"]}}
---

# 🦠 Disease Profiler

Use this skill when the user needs comprehensive 10-dimension disease profile: pathogen, ICD-10, transmission, CFR, symptoms, treatment, prevention, WHO burden data, PubMed articles.

## OpenClaw Routing

- Route here for: `disease profile`, `disease profiler`, `disease overview`, `disease burden`, `disease epidemiology`, `malaria profile`
- Alias: `disease-profile`
- Entrypoint: `skills/disease-profiler/disease_profiler.py`
- Expected inputs: Disease names, pathogen names, destination countries, literature questions, or surveillance briefing prompts.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `lit-reviewer`, `pathogen-intel`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `disease profile`
- `disease profiler`
- `disease overview`
- `disease burden`
- `disease epidemiology`
- `malaria profile`
- `tuberculosis profile`
- `pathogen overview`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python disease_profiler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
