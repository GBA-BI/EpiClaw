---
name: vaccine-effectiveness
description: "Vaccine effectiveness: screening method, test-negative design, waning immunity..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [vaccine-effectiveness, VE, test-negative, screening-method, waning-immunity]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"💉","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["ve","vaccine effectiveness","test-negative design","screening method","vaccine protection","waning immunity","booster effectiveness"]}}
---

# 💉 Vaccine Effectiveness

Use this skill when the user needs vaccine effectiveness: screening method, test-negative design, waning immunity curves, dose-response, schedule comparison.

## OpenClaw Routing

- Route here for: `ve`, `vaccine effectiveness`, `test-negative design`, `screening method`, `vaccine protection`, `waning immunity`
- Alias: `ve`
- Entrypoint: `skills/vaccine-effectiveness/vaccine_effectiveness.py`
- Expected inputs: Cohort or test-negative 2×2 counts supplied via CLI flags or as a CSV file.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--method` | choice | `screening` | Analysis method: `screening` (cohort/attack-rate), `test-negative`, or `cohort` |
| `--pathogen` | string | `"Influenza"` | Pathogen name for report |
| `--vaccine` | string | `"Seasonal Flu Vaccine"` | Vaccine name for report |
| `--output` | path | `output/vaccine-effectiveness` | Output directory |
| `--demo` | flag | off | Run built-in demo for selected method |
| `--input` | path | none | CSV file (see format per method below) |
| `--cases-vax` | int | none | Cases among vaccinated (direct CLI input) |
| `--pop-vax` | int | none | Total vaccinated population (screening/cohort) |
| `--cases-unvax` | int | none | Cases among unvaccinated |
| `--pop-unvax` | int | none | Total unvaccinated population (screening/cohort) |
| `--controls-vax` | int | none | Controls among vaccinated (test-negative only) |
| `--controls-unvax` | int | none | Controls among unvaccinated (test-negative only) |

## Input CSV Formats

**Screening / cohort method:**
```csv
group,cases,population
vaccinated,150,6000
unvaccinated,200,4000
```

**Test-negative design:**
```csv
group,cases,controls
vaccinated,80,200
unvaccinated,120,150
```

Accepted `group` values: `vaccinated`, `vax`, `unvaccinated`, `unvax`.

## Output Format

```
output/
├── report.md     # VE estimate, 95% CI, attack rate/2×2 table, interpretation
└── result.json   # Machine-readable summary
```

**result.json `summary` keys:**

| Key | Description |
|-----|-------------|
| `vaccine_effectiveness` | VE as proportion (0–1) |
| `ve_lower_95ci` | Lower 95% CI of VE |
| `ve_upper_95ci` | Upper 95% CI of VE |
| `method` | `screening`, `cohort`, or `test-negative` |
| `pathogen` | Pathogen name |
| `vaccine` | Vaccine name |

**result.json `data` keys:** `method_details` (AR or OR), `2x2_table`

**VE formula:**
- Screening: VE = 1 − RR = 1 − (AR_vaccinated / AR_unvaccinated)
- Test-negative: VE = 1 − OR = 1 − (cases_vax × controls_unvax) / (cases_unvax × controls_vax)
- 95% CI computed on log(RR) or log(OR) scale (Wald), then back-transformed.

## Sample Output

Demo (screening method): 150 cases/6,000 vaccinated vs 200 cases/4,000 unvaccinated

```
| Metric              | Value                |
|---------------------|----------------------|
| Vaccine Effectiveness | 50.0%              |
| 95% CI              | (33.5%, 62.8%)       |
| Method              | screening            |

Attack Rates
| Group        | Cases | Population | Attack Rate    |
|--------------|-------|------------|----------------|
| Vaccinated   | 150   | 6,000      | 0.0250 (2.50%) |
| Unvaccinated | 200   | 4,000      | 0.0500 (5.00%) |

Interpretation: The Seasonal Flu Vaccine demonstrates 50.0% effectiveness against
Influenza (95% CI: 33.5%–62.8%). The lower confidence bound exceeds 0%, suggesting
statistically significant protection.
```

## Code Examples

```bash
# Demo: screening method
python skills/vaccine-effectiveness/vaccine_effectiveness.py \
  --method screening --demo --output /tmp/ve_demo

# Demo: test-negative design
python skills/vaccine-effectiveness/vaccine_effectiveness.py \
  --method test-negative --demo --output /tmp/ve_tnd_demo

# Screening from CSV
python skills/vaccine-effectiveness/vaccine_effectiveness.py \
  --method screening \
  --input cohort_data.csv \
  --pathogen "COVID-19" \
  --vaccine "mRNA-1273" \
  --output /tmp/ve_covid

# Test-negative from CLI counts
python skills/vaccine-effectiveness/vaccine_effectiveness.py \
  --method test-negative \
  --cases-vax 80 --cases-unvax 120 \
  --controls-vax 200 --controls-unvax 150 \
  --pathogen "Influenza" --vaccine "Flu Vax" \
  --output /tmp/ve_tnd

# ```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- `cohort` method is an alias for `screening`; both use the same RR-based formula.
- All CIs use the log(RR) or log(OR) Wald approach; Haldane correction not applied (cells must be > 0).
- Write `report.md` and `result.json`.

## Chaining

- Works well with: `epi-analyst`, `meta-analysis`, `policy-evaluator`, `epi-calculator`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `ValueError: CSV must have rows with group='vaccinated' and group='unvaccinated'` | Group labels not matching | Use exactly `vaccinated` / `unvaccinated` (or `vax`/`unvax`) in the `group` column |
| `ZeroDivisionError` during VE calculation | Zero cases or zero controls in a cell | At least 1 case and 1 control must exist in each group |
| Negative VE | Vaccinated group has higher attack rate | Review for healthy vaccinee bias or data errors; negative VE is a valid finding but check data quality |
| CI lower bound < 0 for positive VE | Wide CI due to small counts | Expected with small sample sizes; report CI as-is |
| Wrong method for study design | Using `screening` for TND data | Use `--method test-negative` when cases/controls structure is used instead of cases/population |

## Trigger Keywords

- `ve`
- `vaccine effectiveness`
- `test-negative design`
- `screening method`
- `vaccine protection`
- `waning immunity`
- `booster effectiveness`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python vaccine_effectiveness.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
