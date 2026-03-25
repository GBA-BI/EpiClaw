---
name: metagenomics-classifier
description: "Metagenomic pathogen detection: Kraken2/MetaPhlAn taxonomic classification; abundance..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [metagenomics, Kraken2, MetaPhlAn, taxonomic-classification, pathogen-detection, clinical-metagenomics]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["kraken2","metaphlan"],"env":[],"config":[]},"always":false,"emoji":"🌿","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["meta class","metagenomics classifier","metagenomics","kraken2","metaphlan","taxonomic classification","microbiome","pathogen detection","clinical metagenomics","shotgun sequencing"]}}
---

# 🌿 Metagenomics Classifier

Use this skill when the user needs metagenomic pathogen detection: Kraken2/MetaPhlAn taxonomic classification; abundance profiling; novel pathogen flagging.

## OpenClaw Routing

- Route here for: `meta class`, `metagenomics classifier`, `metagenomics`, `kraken2`, `metaphlan`, `taxonomic classification`
- Alias: `meta-class`
- Entrypoint: `skills/metagenomics-classifier/metagenomics_classifier.py`
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

- `meta class`
- `metagenomics classifier`
- `metagenomics`
- `kraken2`
- `metaphlan`
- `taxonomic classification`
- `microbiome`
- `pathogen detection`
- `clinical metagenomics`
- `shotgun sequencing`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python metagenomics_classifier.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
