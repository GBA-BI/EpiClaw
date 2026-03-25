---
name: genome-assembler
description: "De novo genome assembly pipeline (SPAdes/Unicycler/Flye); assembly QC..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [genome-assembly, SPAdes, Unicycler, Flye, de-novo, QUAST, N50]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["spades.py","unicycler","flye","quast"],"env":[],"config":[]},"always":false,"emoji":"🧩","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["assemble","genome assembler","genome assembly","de novo assembly","spades","unicycler","flye","n50","contig","scaffold"]}}
---

# 🧩 Genome Assembler

Use this skill when the user needs de novo genome assembly pipeline (SPAdes/Unicycler/Flye); assembly QC (QUAST/Bandage); reference-guided polishing.

## OpenClaw Routing

- Route here for: `assemble`, `genome assembler`, `genome assembly`, `de novo assembly`, `spades`, `unicycler`
- Alias: `assemble`
- Entrypoint: `skills/genome-assembler/genome_assembler.py`
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

- `assemble`
- `genome assembler`
- `genome assembly`
- `de novo assembly`
- `spades`
- `unicycler`
- `flye`
- `n50`
- `contig`
- `scaffold`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python genome_assembler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
