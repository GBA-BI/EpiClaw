---
name: immune-repertoire
description: "Vaccine response monitoring: antibody/TCR repertoire diversity, clone tracking,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [immune-repertoire, BCR, TCR, antibody, CDR3, clonotype, Shannon-diversity]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🛡️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["immune","immune repertoire","bcr","tcr","antibody repertoire","cdr3","v gene","clonotype","shannon diversity","neutralizing antibody"]}}
---

# 🛡️ Immune Repertoire

Use this skill when the user needs vaccine response monitoring: antibody/TCR repertoire diversity, clone tracking, population immunity assessment.

## OpenClaw Routing

- Route here for: `immune`, `immune repertoire`, `bcr`, `tcr`, `antibody repertoire`, `cdr3`
- Alias: `immune`
- Entrypoint: `skills/immune-repertoire/immune_repertoire.py`
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

- `immune`
- `immune repertoire`
- `bcr`
- `tcr`
- `antibody repertoire`
- `cdr3`
- `v gene`
- `clonotype`
- `shannon diversity`
- `neutralizing antibody`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python immune_repertoire.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
