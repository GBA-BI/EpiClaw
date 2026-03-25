---
name: seq-wrangler
description: "Sequence QC, FASTQ inspection, and alignment pipeline planning with..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [sequence-qc, fastq, alignment, samtools, bam, bioinformatics]
metadata: {"openclaw":{"requires":{"bins":["python3","samtools"],"anyBins":["bwa","bowtie2","minimap2","fastqc","multiqc","fastp"],"env":[],"config":[]},"always":false,"emoji":"🦖","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"brew","formula":"samtools","bins":["samtools"]},{"kind":"brew","formula":"bwa","bins":["bwa"]}],"trigger_keywords":["seq wrangler","fastq qc","read alignment","bam processing","samtools","bwa","bowtie2"]}}
---

# 🦖 Seq Wrangler

Use this skill when the user needs sequence QC, FASTQ inspection, and alignment pipeline planning with FastQC/BWA/Bowtie2/SAMtools-oriented handoff.

## OpenClaw Routing

- Route here for: `seq wrangler`, `fastq qc`, `read alignment`, `bam processing`, `samtools`, `bwa`
- Alias: `seq-wrangler`
- Entrypoint: `skills/seq-wrangler/seq_wrangler.py`
- Expected inputs: FASTQ/FASTA/VCF/count matrices, sequence metadata, and pipeline configuration choices.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `vcf-annotator`, `rnaseq-de`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `seq wrangler`
- `fastq qc`
- `read alignment`
- `bam processing`
- `samtools`
- `bwa`
- `bowtie2`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python seq_wrangler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
