---
name: recombination-detector
description: "Detect genomic recombination events in viral sequences; breakpoint mapping;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [recombination, breakpoints, RDP4, recombinant-lineage, viral-evolution]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["gubbins","rdp4"],"env":[],"config":[]},"always":false,"emoji":"🔀","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["recombination","recombination detector","recombinant","breakpoint","mosaic genome","parental sequence","rdp4","recombination detection","chimeric sequence","hybrid lineage"]}}
---

# 🔀 Recombination Detector

Use this skill when the user needs detect genomic recombination events in viral sequences; breakpoint mapping; recombinant lineage identification.

## OpenClaw Routing

- Route here for: `recombination`, `recombination detector`, `recombinant`, `breakpoint`, `mosaic genome`, `parental sequence`
- Alias: `recombination`
- Entrypoint: `skills/recombination-detector/recombination_detector.py`
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

- `recombination`
- `recombination detector`
- `recombinant`
- `breakpoint`
- `mosaic genome`
- `parental sequence`
- `rdp4`
- `recombination detection`
- `chimeric sequence`
- `hybrid lineage`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python recombination_detector.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
