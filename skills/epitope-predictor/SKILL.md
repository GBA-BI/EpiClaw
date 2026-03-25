---
name: epitope-predictor
description: "Vaccine target identification: B/T-cell epitope prediction; conservation scoring..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [epitope-prediction, vaccine-design, MHC-binding, B-cell-epitope, T-cell-epitope, IEDB]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🎯","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["epitope","epitope predictor","epitope prediction","vaccine design","mhc binding","b-cell epitope","t-cell epitope","hla","iedb","bepipred"]}}
---

# 🎯 Epitope Predictor

Use this skill when the user needs vaccine target identification: B/T-cell epitope prediction; conservation scoring across lineages; immunogenicity ranking.

## OpenClaw Routing

- Route here for: `epitope`, `epitope predictor`, `epitope prediction`, `vaccine design`, `mhc binding`, `b-cell epitope`
- Alias: `epitope`
- Entrypoint: `skills/epitope-predictor/epitope_predictor.py`
- Expected inputs: FASTQ/FASTA/VCF/count matrices, sequence metadata, and pipeline configuration choices.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `seq-wrangler`, `vcf-annotator`, `rnaseq-de`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `epitope`
- `epitope predictor`
- `epitope prediction`
- `vaccine design`
- `mhc binding`
- `b-cell epitope`
- `t-cell epitope`
- `hla`
- `iedb`
- `bepipred`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python epitope_predictor.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
