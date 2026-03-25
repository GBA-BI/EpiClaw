---
name: transmission-inference
description: "Transmission network reconstruction (TransPhylo); infer source, timing, and..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [transmission-network, TransPhylo, who-infected-whom, outbreak-reconstruction, bottleneck]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"anyBins":["transphylo"],"env":[],"config":[]},"always":false,"emoji":"🔗","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["transmit","transmission inference","transmission network","who infected whom","transphylo","outbreak reconstruction","source attribution","transmission bottleneck","phylogenetic transmission"]}}
---

# 🔗 Transmission Inference

Use this skill when the user needs transmission network reconstruction (TransPhylo); infer source, timing, and bottleneck size; outbreak likely-source ranking.

## OpenClaw Routing

- Route here for: `transmit`, `transmission inference`, `transmission network`, `who infected whom`, `transphylo`, `outbreak reconstruction`
- Alias: `transmit`
- Entrypoint: `skills/transmission-inference/transmission_inference.py`
- Expected inputs: Consensus genomes, alignments, metadata tables, typing outputs, and dated outbreak context.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `pathogen-typing`, `phylodynamics`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `transmit`
- `transmission inference`
- `transmission network`
- `who infected whom`
- `transphylo`
- `outbreak reconstruction`
- `source attribution`
- `transmission bottleneck`
- `phylogenetic transmission`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python transmission_inference.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
