---
name: pathogen-typing
description: "MLST/cgMLST strain characterization; sequence type (ST) clustering; outbreak cluster..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [MLST, cgMLST, strain-typing, sequence-type, outbreak-cluster, Salmonella]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["mlst","chewbbaca","cgmlst"],"env":[],"config":[]},"always":false,"emoji":"🏷️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["typing","pathogen typing","mlst","sequence type","st","strain typing","cgmlst","outbreak cluster","molecular epidemiology","clonal complex"]}}
---

# 🏷️ Pathogen Typing

Use this skill when the user needs MLST/cgMLST strain characterization; sequence type (ST) clustering; outbreak cluster definition; BV-BRC schema lookup.

## OpenClaw Routing

- Route here for: `typing`, `pathogen typing`, `mlst`, `sequence type`, `st`, `strain typing`
- Alias: `typing`
- Entrypoint: `skills/pathogen-typing/pathogen_typing.py`
- Expected inputs: Consensus genomes, alignments, metadata tables, typing outputs, and dated outbreak context.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `phylodynamics`, `transmission-inference`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `typing`
- `pathogen typing`
- `mlst`
- `sequence type`
- `st`
- `strain typing`
- `cgmlst`
- `outbreak cluster`
- `molecular epidemiology`
- `clonal complex`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python pathogen_typing.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
