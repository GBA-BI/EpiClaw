---
name: ncbi-sequence-fetcher
description: "Search and download pathogen/viral genome sequences from NCBI Nucleotide and NCBI..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [ncbi, sequences, fasta, genomics, virus, phylodynamics, download]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["NCBI_API_KEY"],"config":[]},"always":false,"emoji":"\ud83e\uddec","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"requests","bins":[]}],"trigger_keywords":["download sequences","fetch sequences","ncbi","ncbi virus","genbank","sars-cov-2 sequences","influenza sequences","viral genomes","fasta download","entrez query","sequence search","genome download"]}}
---

# 🧬 NCBI Sequence Fetcher

Use this skill when the user needs to search and download pathogen/viral genome sequences
from NCBI for use in variant surveillance, phylodynamics, or sequence QC workflows.

## OpenClaw Routing

- Route here for: `ncbi`, `genbank`, `download sequences`, `viral genomes`, `fasta download`
- Alias: `ncbi-seq`
- Entrypoint: `skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py`
- Expected inputs: Organism name or custom Entrez query

## Organism Presets

| Preset | Description |
|--------|-------------|
| `sars-cov-2` | SARS-CoV-2 complete genomes |
| `influenza-a` | Influenza A virus segments |
| `mpox` | Monkeypox virus complete genomes |
| `dengue` | Dengue virus complete genomes |
| `ebola` | Ebola virus complete genomes |
| `rsv` | RSV complete genomes |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--organism` | (none) | Organism preset name |
| `--query` | (none) | Custom NCBI Entrez query (overrides `--organism`) |
| `--db` | `nuccore` | NCBI database: `nuccore`, `protein`, `biosample` |
| `--max-results` | `50` | Maximum sequences to retrieve |
| `--download-fasta` | off | Download FASTA file (first 20 sequences) |
| `--output` | `output/ncbi-sequence-fetcher` | Output directory |
| `--demo` | off | Offline demo with 3 SARS-CoV-2 reference records |

## Output Format

```
output/
├── metadata.csv      # Accession, organism, length, collection date, country
├── sequences.fasta   # FASTA file (if --download-fasta or demo)
├── report.md         # Summary with sequence list and downstream guidance
└── result.json       # Machine-readable summary envelope
```

## Example Commands

```bash
# Download 50 SARS-CoV-2 complete genomes (metadata only)
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py \
  --organism sars-cov-2 --max-results 50 --output output/sars_seqs

# Download Influenza A with FASTA sequences
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py \
  --organism influenza-a --max-results 100 --download-fasta --output output/flu_seqs

# Custom Entrez query
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py \
  --query 'West Nile virus[Organism] AND "complete genome" AND 2023[PDAT]:2025[PDAT]' \
  --max-results 30 --output output/wnv_2023

# Demo mode (no internet required)
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py --demo
```

## Downstream Skill Chains

```bash
# Fetch → Variant surveillance
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py \
  --organism sars-cov-2 --download-fasta --output /tmp/seqs
python skills/variant-surveillance/variant_surveillance.py \
  --input /tmp/seqs/sequences.fasta

# Fetch → Sequence QC
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py \
  --organism influenza-a --download-fasta --output /tmp/flu
python skills/sequence-qc/sequence_qc.py --input /tmp/flu/sequences.fasta

# Fetch → Phylodynamics
python skills/ncbi-sequence-fetcher/ncbi_sequence_fetcher.py \
  --organism mpox --download-fasta --output /tmp/mpox
python skills/phylodynamics/phylodynamics.py --input /tmp/mpox/sequences.fasta
```

## Rate Limits & API Key

- Without `NCBI_API_KEY`: 3 requests/second
- With `NCBI_API_KEY` (free, register at NCBI): 10 requests/second
- Set key: `export NCBI_API_KEY=your_key_here`
- Responses cached locally for 24 hours to reduce API load

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `No accessions returned` | Query too specific or no results | Broaden query or check syntax |
| `Rate limit exceeded` | Too many requests | Register for NCBI API key |
| `FASTA download failed` | Network timeout for large batch | Reduce `--max-results` or try without `--download-fasta` first |
| Demo shows 3 records | Demo mode active | Remove `--demo` and provide `--organism` |

## Chaining

- Works well with: `variant-surveillance`, `phylodynamics`, `sequence-qc`, `genome-assembler`, `transmission-inference`
- For AMR analysis: use `--db biosample` then feed into `amr-surveillance`

## Trigger Keywords

- download sequences
- fetch sequences
- ncbi
- ncbi virus
- genbank
- sars-cov-2 sequences
- influenza sequences
- viral genomes
- fasta download
- entrez query
- sequence search
- genome download

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python ncbi_sequence_fetcher.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
