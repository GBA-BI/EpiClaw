---
name: sequence-qc
description: "Sequencing quality control: FastQC/MultiQC reports, adapter trimming, contamination..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [sequencing-QC, FastQC, MultiQC, adapter-trimming, read-quality, FASTQ]
metadata: {"openclaw":{"requires":{"bins":["python3","fastqc"],"anyBins":["multiqc","fastp","samtools"],"env":[],"config":[]},"always":false,"emoji":"🔍","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"brew","formula":"fastqc","bins":["fastqc"]},{"kind":"brew","formula":"multiqc","bins":["multiqc"]}],"trigger_keywords":["seqqc","sequence qc","fastqc","sequence quality","read quality","adapter trimming","fastq","sequencing qc","per-base quality","gc content"]}}
---

# 🔍 Sequence Qc

Use this skill when the user needs sequencing quality control: FastQC/MultiQC reports, adapter trimming, contamination screening, FASTQ statistics.

## OpenClaw Routing

- Route here for: `seqqc`, `sequence qc`, `fastqc`, `sequence quality`, `read quality`, `adapter trimming`
- Alias: `seqqc`
- Entrypoint: `skills/sequence-qc/sequence_qc.py`
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

- `seqqc`
- `sequence qc`
- `fastqc`
- `sequence quality`
- `read quality`
- `adapter trimming`
- `fastq`
- `sequencing qc`
- `per-base quality`
- `gc content`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python sequence_qc.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
