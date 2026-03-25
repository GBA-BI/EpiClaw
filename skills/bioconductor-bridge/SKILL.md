---
name: bioconductor-bridge
description: "Bioconductor package recommendation, workflow suggestion, and local R/BiocManager..."
version: 0.1.0
author: Hiranyamaya Dash
license: MIT
tags: [bioconductor, r, package-discovery, workflows, transcriptomics, genomics, single-cell, annotation]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"🧬","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[],"trigger_keywords":["bioc bridge","bioconductor bridge","bioconductor","bioc","biocmanager","summarizedexperiment","singlecellexperiment","genomicranges","variantannotation","annotationhub"]}}
---

# 🧬 Bioconductor Bridge

Use this skill when the user needs bioconductor package recommendation, workflow suggestion, and local R/BiocManager setup bridge.

## OpenClaw Routing

- Route here for: `bioc bridge`, `bioconductor bridge`, `bioconductor`, `bioc`, `biocmanager`, `summarizedexperiment`
- Alias: `bioc-bridge`
- Entrypoint: `skills/bioconductor-bridge/bioconductor_bridge.py`
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

- `bioc bridge`
- `bioconductor bridge`
- `bioconductor`
- `bioc`
- `biocmanager`
- `summarizedexperiment`
- `singlecellexperiment`
- `genomicranges`
- `variantannotation`
- `annotationhub`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python bioconductor_bridge.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
