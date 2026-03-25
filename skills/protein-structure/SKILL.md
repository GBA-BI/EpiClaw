---
name: protein-structure
description: "Protein structure prediction (ESMFold/AlphaFold2 API); antigenic site mapping;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [protein-structure, AlphaFold2, ESMFold, antigenic-site, structural-biology, pLDDT]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🎯","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["structure","protein structure","alphafold","esmfold","plddt","antigenic site","structural prediction","protein fold","antibody binding","structural alignment"]}}
---

# 🎯 Protein Structure

Use this skill when the user needs protein structure prediction (ESMFold/AlphaFold2 API); antigenic site mapping; structural alignment for variant impact assessment.

## OpenClaw Routing

- Route here for: `structure`, `protein structure`, `alphafold`, `esmfold`, `plddt`, `antigenic site`
- Alias: `structure`
- Entrypoint: `skills/protein-structure/protein_structure.py`
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

- `structure`
- `protein structure`
- `alphafold`
- `esmfold`
- `plddt`
- `antigenic site`
- `structural prediction`
- `protein fold`
- `antibody binding`
- `structural alignment`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python protein_structure.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
