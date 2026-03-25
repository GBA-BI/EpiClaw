---
name: rnaseq-de
description: "Differential expression workflow for bulk and pseudo-bulk RNA-seq with QC tables and..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [rna-seq, differential expression, bulk, pseudo-bulk, transcriptomics, DESeq2, PyDESeq2, QC, PCA]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"🧬","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"pandas","bins":[]},{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"uv","package":"scikit-learn","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["rnaseq de","rna-seq","differential expression","bulk rna","pseudo-bulk","volcano plot","ma plot","count matrix","deseq2","pydeseq2"]}}
---

# 🧬 RNA-seq DE

Use this skill when the user needs differential expression workflow for bulk and pseudo-bulk RNA-seq with QC tables and reproducibility bundle.

## OpenClaw Routing

- Route here for: `rnaseq de`, `rna-seq`, `differential expression`, `bulk rna`, `pseudo-bulk`, `volcano plot`
- Alias: `rnaseq-de`
- Entrypoint: `skills/rnaseq-de/rnaseq_de.py`
- Expected inputs: FASTQ/FASTA/VCF/count matrices, sequence metadata, and pipeline configuration choices.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `seq-wrangler`, `vcf-annotator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `rnaseq de`
- `rna-seq`
- `differential expression`
- `bulk rna`
- `pseudo-bulk`
- `volcano plot`
- `ma plot`
- `count matrix`
- `deseq2`
- `pydeseq2`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python rnaseq_de.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
