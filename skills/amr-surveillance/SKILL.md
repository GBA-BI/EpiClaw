---
name: amr-surveillance
description: "Antimicrobial resistance: AMRFinderPlus/ResFinder gene detection; antibiogram..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [AMR, antimicrobial-resistance, antibiogram, AMRFinderPlus, ResFinder, resistance-genes]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["amrfinder","amrfinderplus","resfinder"],"env":[],"config":[]},"always":false,"emoji":"💊","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["amr","amr surveillance","antimicrobial resistance","antibiogram","resistance genes","mrsa","carbapenem resistance","esbl","mcr-1","blatem"]}}
---

# 💊 Amr Surveillance

Use this skill when the user needs antimicrobial resistance: AMRFinderPlus/ResFinder gene detection; antibiogram generation; temporal trend analysis; BV-BRC integration.

## OpenClaw Routing

- Route here for: `amr`, `amr surveillance`, `antimicrobial resistance`, `antibiogram`, `resistance genes`, `mrsa`
- Alias: `amr`
- Entrypoint: `skills/amr-surveillance/amr_surveillance.py`
- Expected inputs: Consensus genomes, alignments, metadata tables, typing outputs, and dated outbreak context.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `pathogen-typing`, `phylodynamics`, `transmission-inference`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `amr`
- `amr surveillance`
- `antimicrobial resistance`
- `antibiogram`
- `resistance genes`
- `mrsa`
- `carbapenem resistance`
- `esbl`
- `mcr-1`
- `blatem`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python amr_surveillance.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
