---
name: variant-surveillance
description: "Pathogen lineage classification (Nextclade, Pangolin); variant prevalence tracking;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [variant-surveillance, lineage, Nextclade, Pangolin, SARS-CoV-2, genomic-surveillance]
metadata: {"openclaw":{"requires":{"bins":["python3"],"anyBins":["nextclade","pangolin"],"env":[],"config":[]},"always":false,"emoji":"🧬","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"brew","formula":"nextclade","bins":["nextclade"]}],"trigger_keywords":["variant","variant surveillance","lineage","nextclade","pangolin","sars-cov-2 variant","ba.2","xbb","variant prevalence","immune escape"]}}
---

# 🧬 Variant Surveillance

Use this skill when the user needs pathogen lineage classification (Nextclade, Pangolin); variant prevalence tracking; immune escape scoring; NCBI Virus integration.

## OpenClaw Routing

- Route here for: `variant`, `variant surveillance`, `lineage`, `nextclade`, `pangolin`, `sars-cov-2 variant`
- Alias: `variant`
- Entrypoint: `skills/variant-surveillance/variant_surveillance.py`
- Expected inputs: FASTA file of consensus genomes for real-mode classification; `--demo` for synthetic data.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--input` | path | none | Path to input FASTA file of consensus genomes |
| `--output` | path | `output/variant-surveillance` | Output directory |
| `--demo` | flag | off | Run demo mode with synthetic lineage count data |
| `--pathogen` | string | `"SARS-CoV-2"` | Pathogen name used in report |
| `--country` | string | `"Global"` | Country or region label used in report |
| `--tool` | choice | `auto` | Classification tool: `nextclade`, `pangolin`, or `auto` (nextclade preferred if found) |
| `--nextclade-dataset` | string | `"sars-cov-2"` | Dataset slug passed to `nextclade run --input-dataset` |

**Tool resolution order (auto):** nextclade → pangolin → demo fallback with warning.

## External Tool Requirements

| Tool | Installation | Column parsed |
|------|-------------|---------------|
| Nextclade | `brew install nextclade` or bioconda | `Nextclade_pango`, `clade`, or `lineage` |
| Pangolin | conda/pip (see pangolin docs) | `lineage`, `pangoLineage` |

When neither tool is found, the skill falls back to demo data and prints a warning.

## Output Format

```
output/
├── report.md                       # Lineage prevalence table with trends
├── result.json                     # Machine-readable summary + lineage data
├── nextclade_results.csv           # Raw Nextclade output (real mode only)
└── pangolin_lineages.csv           # Raw Pangolin output (real mode only)
```

**result.json `summary` keys:**

| Key | Description |
|-----|-------------|
| `n_sequences` | Total sequences classified |
| `n_lineages` | Number of distinct lineages detected |
| `dominant_lineage` | Lineage with highest count |
| `dominant_prevalence` | Dominant lineage prevalence (%) |
| `pathogen` | Pathogen name |
| `country` | Country/region label |

**result.json `data` keys:**

| Key | Description |
|-----|-------------|
| `lineage_counts` | Dict: lineage → count |
| `lineage_prevalence` | Dict: lineage → prevalence % (rounded to 1 dp) |
| `trend` | Dict: lineage → `increasing`/`decreasing`/`stable` (demo) or `stable` (real mode) |
| `immune_escape_scores` | Dict: lineage → float score (0.0 in real mode; simulated in demo) |

**report.md table columns:** `Lineage | Count | Prevalence (%) | Trend`

## Sample Output

Demo data (200 sequences, 4 lineages):

```
Summary
| Metric                    | Value         |
|---------------------------|---------------|
| Sequences classified      | 200           |
| Lineages observed         | 4             |
| Dominant lineage          | B.1.617.2     |
| Dominant prevalence (%)   | 40.0          |

Lineage Prevalence
| Lineage   | Count | Prevalence (%) | Trend      |
|-----------|-------|----------------|------------|
| B.1.617.2 | 80    | 40.0           | increasing |
| BA.1      | 60    | 30.0           | decreasing |
| B.1.1.7   | 45    | 22.5           | stable     |
| BA.2      | 15    | 7.5            | increasing |
```

## Code Examples

```bash
# Demo mode (no FASTA required)
python skills/variant-surveillance/variant_surveillance.py \
  --demo --output /tmp/variant_demo

# Real FASTA with Nextclade (auto-detected)
python skills/variant-surveillance/variant_surveillance.py \
  --input genomes.fasta \
  --pathogen "SARS-CoV-2" \
  --country "USA" \
  --output /tmp/variant_usa

# Force Pangolin
python skills/variant-surveillance/variant_surveillance.py \
  --input genomes.fasta \
  --tool pangolin \
  --output /tmp/variant_pangolin

# Nextclade with alternative dataset (e.g. influenza)
python skills/variant-surveillance/variant_surveillance.py \
  --input influenza_genomes.fasta \
  --tool nextclade \
  --nextclade-dataset flu-h3n2 \
  --pathogen "Influenza H3N2" \
  --output /tmp/variant_flu

# ```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Real mode requires `nextclade` or `pangolin` on PATH; skill falls back to demo data if neither is found.
- Lineage column is auto-detected from output CSV: checks `lineage`, `pangoLineage`, `Nextclade_pango`, `clade` (in that order).
- Write `report.md` and `result.json`.

## Downstream Skill Chains

```bash
# Variant surveillance → phylodynamics
python skills/variant-surveillance/variant_surveillance.py \
  --input genomes.fasta --output /tmp/variants
python skills/phylodynamics/phylodynamics.py \
  --input genomes.fasta --output /tmp/phylo

# Variant → pathogen typing for MLST comparison
python skills/variant-surveillance/variant_surveillance.py \
  --input genomes.fasta --output /tmp/variants
python skills/pathogen-typing/pathogen_typing.py \
  --input genomes.fasta --output /tmp/typing
```

## Chaining

- Works well with: `pathogen-typing`, `phylodynamics`, `transmission-inference`, `recombination-detector`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `Neither nextclade nor pangolin is available` | Tools not installed or not on PATH | Install via `brew install nextclade` or `conda install pangolin`; or use `--demo` |
| `Nextclade failed` error | Dataset slug incorrect or network issue | Check `--nextclade-dataset` matches your pathogen; run `nextclade dataset list` |
| `No classified sequences were returned` | FASTA headers malformed or tool output has no lineage column | Check FASTA format; verify tool version compatibility |
| Demo fallback triggered unexpectedly | FASTA provided but tool not found | Install required tool; fallback reason is printed and stored in `result.json` under `data.fallback_reason` |
| Immune escape scores all 0.0 | Real mode does not compute escape scores | Scores are populated only in demo mode; integrate with dedicated escape scoring tools for real data |

## Trigger Keywords

- `variant`
- `variant surveillance`
- `lineage`
- `nextclade`
- `pangolin`
- `sars-cov-2 variant`
- `ba.2`
- `xbb`
- `variant prevalence`
- `immune escape`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python variant_surveillance.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
