---
name: vcf-annotator
description: "VCF INFO-field parsing and prioritised variant reporting with ClinVar / gnomAD-aware..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [vcf, variant-annotation, vep, clinvar, gnomad, genomics]
metadata: {"openclaw":{"requires":{"bins":["python3","vep"],"env":[],"config":[]},"always":false,"emoji":"🦖","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"cyvcf2","bins":[]},{"kind":"uv","package":"pandas","bins":[]}],"trigger_keywords":["vcf annotator","vcf annotation","annotate variants","vep","clinvar","gnomad"]}}
---

# 🦖 VCF Annotator

Use this skill when the user needs VCF INFO-field parsing and prioritised variant reporting with ClinVar / gnomAD-aware context.

## OpenClaw Routing

- Route here for: `vcf annotator`, `vcf annotation`, `annotate variants`, `vep`, `clinvar`, `gnomad`
- Alias: `vcf-annotator`
- Entrypoint: `skills/vcf-annotator/vcf_annotator.py`
- Expected inputs: FASTQ/FASTA/VCF/count matrices, sequence metadata, and pipeline configuration choices.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `seq-wrangler`, `rnaseq-de`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `vcf annotator`
- `vcf annotation`
- `annotate variants`
- `vep`
- `clinvar`
- `gnomad`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python vcf_annotator.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
