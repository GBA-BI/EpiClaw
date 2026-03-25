---
name: pathogen-intel
description: "Rapid pathogen characterization: taxonomy, zoonotic potential, emergence risk..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [pathogen-intelligence, zoonotic, emergence-risk, taxonomy, WHO-priority, rapid-characterization]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"\ud83d\udd0d","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"requests","bins":[]}],"trigger_keywords":["intel","pathogen intel","pathogen characterization","emerging pathogen","zoonotic risk","emergence risk","who priority pathogen","pathogen profile rapid","unknown pathogen","novel pathogen"]}}
---

# 🔍 Pathogen Intel

Use this skill when the user needs rapid pathogen characterization: taxonomy, zoonotic potential, emergence risk scoring, NCBI Taxonomy + UniProt integration.

## OpenClaw Routing

- Route here for: `intel`, `pathogen intel`, `pathogen characterization`, `emerging pathogen`, `zoonotic risk`, `emergence risk`
- Alias: `intel`
- Entrypoint: `skills/pathogen-intel/pathogen_intel.py`
- Expected inputs: Disease names, pathogen names, destination countries, literature questions, or surveillance briefing prompts.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `lit-reviewer`, `disease-profiler`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `intel`
- `pathogen intel`
- `pathogen characterization`
- `emerging pathogen`
- `zoonotic risk`
- `emergence risk`
- `who priority pathogen`
- `pathogen profile rapid`
- `unknown pathogen`
- `novel pathogen`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python pathogen_intel.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
