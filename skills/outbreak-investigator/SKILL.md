---
name: outbreak-investigator
description: "Linelist CSV parsing, epidemic curve generation, attack rate tables, food-specific χ²..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [epidemiology, outbreak, epi-curve, attack-rate, linelist]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🚨","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"pandas","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["outbreak","outbreak investigator","outbreak investigation","epidemic curve","epi curve","linelist","attack rate","case-control","foodborne outbreak","secondary attack rate"]}}
---

# 🚨 Outbreak Investigator

Use this skill when the user needs linelist CSV parsing, epidemic curve generation, attack rate tables, food-specific χ² analysis, descriptive epi.

## OpenClaw Routing

- Route here for: `outbreak`, `outbreak investigator`, `outbreak investigation`, `epidemic curve`, `epi curve`, `linelist`
- Alias: `outbreak`
- Entrypoint: `skills/outbreak-investigator/outbreak_investigator.py`
- Expected inputs: Linelist CSV with one row per person. Required columns: `case_id`, `onset_date`, `ill`. Exposure columns (any column with Yes/No values, e.g. `potato_salad`, `chicken`) are auto-detected.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--demo` | flag | off | Run built-in synthetic foodborne outbreak linelist (60 persons) |
| `--input` | path | none | Input linelist CSV file |
| `--output` | path | required | Output directory for report, figures, and JSON |
| `--pathogen` | string | none | Pathogen name (optional; used in report title) |

**Note:** `--output` is required. Either `--input` or `--demo` must be used.

## Input CSV Format

```csv
case_id,onset_date,age,sex,potato_salad,chicken,water,ill,outcome
C001,2025-06-17 10:30,45,F,Yes,No,Yes,Yes,recovered
C002,,32,M,No,Yes,Yes,No,well
C003,2025-06-17 14:00,67,M,Yes,Yes,Yes,Yes,hospitalized
```

**Column conventions:**
- `onset_date`: YYYY-MM-DD or YYYY-MM-DD HH:MM format; blank = no illness onset
- `ill`: `Yes` or `No`
- Exposure columns: any column with `Yes`/`No` values (excluding `case_id`, `onset_date`, `age`, `sex`, `ill`, `outcome`) are automatically treated as potential exposures

## Output Format

```
output/
├── report.md              # Descriptive epi, ASCII epi curve, attack rate table
├── result.json            # Machine-readable summary + full data
└── figures/
    └── epi_curve.png      # Bar chart of cases by date of onset
```

**result.json `summary` keys:**

| Key | Description |
|-----|-------------|
| `total_persons` | Total rows in linelist |
| `total_cases` | Persons with `ill == Yes` |
| `overall_attack_rate` | total_cases / total_persons × 100 |
| `age_range` | Min–max age among cases |
| `median_age` | Median age among cases |
| `sex_distribution` | Dict with M/F/Unknown counts |
| `outcomes` | Dict of outcome value counts |
| `exposures_tested` | Number of exposure columns analysed |

**result.json `data` keys:** `descriptive`, `epi_curve` (date → count dict), `attack_rates` (list of per-exposure dicts)

**attack_rates list item keys:** `exposure`, `exposed_ill`, `exposed_total`, `attack_rate_exposed`, `unexposed_ill`, `unexposed_total`, `attack_rate_unexposed`, `risk_ratio`

## Sample Output

Demo data (60 persons, synthetic foodborne outbreak):

```
Descriptive Epidemiology
- Total persons: 60
- Total cases: 28
- Overall attack rate: 46.7%
- Age range: 7-84 (median: 41)
- Sex distribution: {'M': 14, 'F': 14}
- Outcomes: {'recovered': 21, 'hospitalized': 7}

Food-Specific Attack Rates
| Exposure     | Exposed Ill/Total | AR (Exposed) | Unexposed Ill/Total | AR (Unexposed) | RR   |
|--------------|-------------------|--------------|---------------------|----------------|------|
| potato_salad | 24/41             | 58.5%        | 4/19                | 21.1%          | 2.77 |
| chicken      | 17/37             | 45.9%        | 11/23               | 47.8%          | 0.96 |
| water        | 25/54             | 46.3%        | 3/6                 | 50.0%          | 0.93 |

Strongest association: potato_salad (RR = 2.77)
```

## Code Examples

```bash
# Demo mode
python skills/outbreak-investigator/outbreak_investigator.py \
  --demo --output /tmp/outbreak_demo

# Real linelist
python skills/outbreak-investigator/outbreak_investigator.py \
  --input linelist.csv \
  --pathogen "Salmonella" \
  --output /tmp/salmonella_outbreak

# ```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Exposure detection is automatic: any column with only Yes/No values (excluding standard metadata columns) is treated as an exposure variable.
- matplotlib is optional; epi curve PNG is generated if available; ASCII fallback is always included in report.md.
- Write `report.md` and `result.json`.

## Downstream Skill Chains

```bash
# Outbreak investigation → Rt estimation
python skills/outbreak-investigator/outbreak_investigator.py \
  --input linelist.csv --output /tmp/outbreak
python skills/rt-estimator/rt_estimator.py \
  --input /tmp/outbreak/epi_curve.csv --output /tmp/rt

# Outbreak → contact tracing
python skills/outbreak-investigator/outbreak_investigator.py \
  --input linelist.csv --output /tmp/outbreak
python skills/contact-tracing/contact_tracing.py \
  --input /tmp/outbreak/result.json --output /tmp/trace
```

## Chaining

- Works well with: `contact-tracing`, `rt-estimator`, `epi-analyst`, `epi-orchestrator`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| No exposures in attack rate table | No columns with Yes/No values | Ensure exposure columns use `Yes`/`No` values exactly (case-sensitive) |
| Epi curve is empty | No valid `onset_date` values | Check date format is YYYY-MM-DD; `ill == No` rows have blank onset_date by convention |
| `KeyError` on `ill` column | Column named differently in CSV | Rename column to `ill` or check CSV header row |
| RR shows `undefined` | Zero unexposed cases | Expected when all unexposed are well; RR is mathematically undefined |
| Figure not generated | matplotlib not installed | Run `pip install matplotlib`; ASCII curve is always included |

## Trigger Keywords

- `outbreak`
- `outbreak investigator`
- `outbreak investigation`
- `epidemic curve`
- `epi curve`
- `linelist`
- `attack rate`
- `case-control`
- `foodborne outbreak`
- `secondary attack rate`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python outbreak_investigator.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
