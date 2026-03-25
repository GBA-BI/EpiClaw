---
name: comparative-genomics
description: "Pan-genome analysis (Roary/Panaroo); core vs. accessory genome; pairwise SNP matrix;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [pan-genome, Roary, Panaroo, core-genome, accessory-genome, SNP-matrix]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["roary","panaroo","prokka","snippy","iqtree2"],"env":[],"config":[]},"always":false,"emoji":"🔬","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["pangenom","comparative genomics","pan-genome","core genome","accessory genome","roary","panaroo","snp matrix","whole-genome comparison","genomic diversity"]}}
---

# 🔬 Comparative Genomics

Use this skill when the user needs pan-genome analysis (Roary/Panaroo); core vs. accessory genome; pairwise SNP matrix; maximum-likelihood phylogeny from SNPs.

## OpenClaw Routing

- Route here for: `pangenom`, `comparative genomics`, `pan-genome`, `core genome`, `accessory genome`, `roary`
- Alias: `pangenom`
- Entrypoint: `skills/comparative-genomics/comparative_genomics.py`
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

- `pangenom`
- `comparative genomics`
- `pan-genome`
- `core genome`
- `accessory genome`
- `roary`
- `panaroo`
- `snp matrix`
- `whole-genome comparison`
- `genomic diversity`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python comparative_genomics.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
