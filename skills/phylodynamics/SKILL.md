---
name: phylodynamics
description: "Time-scaled phylogeny: TreeTime/BEAST2 integration; molecular clock estimation;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [phylodynamics, molecular-clock, BEAST2, TreeTime, TMRCA, coalescent]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["treetime","beast","beast2","mafft","iqtree2"],"env":[],"config":[]},"always":false,"emoji":"🌳","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"brew","formula":"mafft","bins":["mafft"]},{"kind":"brew","formula":"iq-tree","bins":["iqtree2"]}],"trigger_keywords":["phylo","phylodynamics","molecular clock","tmrca","beast","treetime","time-scaled phylogeny","evolutionary rate","coalescent","phylogenetic tree"]}}
---

# 🌳 Phylodynamics

Use this skill when the user needs time-scaled phylogeny: TreeTime/BEAST2 integration; molecular clock estimation; population size dynamics; annotated tree export.

## OpenClaw Routing

- Route here for: `phylo`, `phylodynamics`, `molecular clock`, `tmrca`, `beast`, `treetime`
- Alias: `phylo`
- Entrypoint: `skills/phylodynamics/phylodynamics.py`
- Expected inputs: Consensus genomes, alignments, metadata tables, typing outputs, and dated outbreak context.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `pathogen-typing`, `transmission-inference`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `phylo`
- `phylodynamics`
- `molecular clock`
- `tmrca`
- `beast`
- `treetime`
- `time-scaled phylogeny`
- `evolutionary rate`
- `coalescent`
- `phylogenetic tree`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python phylodynamics.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
