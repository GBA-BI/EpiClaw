---
name: survival-analysis
description: "Time-to-event analysis: Kaplan-Meier curves, log-rank test, Cox proportional hazards..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [survival-analysis, Kaplan-Meier, Cox-regression, time-to-event, censoring]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"⏳","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["survival","survival analysis","kaplan-meier","cox regression","time to event","censoring","hazard ratio","log-rank test","survival curve"]}}
---

# ⏳ Survival Analysis

Use this skill when the user needs time-to-event analysis: Kaplan-Meier curves, log-rank test, Cox proportional hazards regression, time-varying covariates.

## OpenClaw Routing

- Route here for: `survival`, `survival analysis`, `kaplan-meier`, `cox regression`, `time to event`, `censoring`
- Alias: `survival`
- Entrypoint: `skills/survival-analysis/survival_analysis.py`
- Expected inputs: Individual-level CSV with columns for time, event indicator (0/1), optional group, and optional covariates.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--input` | path | none | Input CSV file |
| `--output` | path | required | Output directory |
| `--demo` | flag | off | Run built-in demo cohort (6 subjects, vaccinated vs unvaccinated) |
| `--time-col` | string | `time` | Column name for time-to-event or time-to-censoring |
| `--event-col` | string | `event` | Column name for event indicator (1 = event occurred, 0 = censored) |
| `--group-col` | string | `group` | Column name for grouping variable (used in KM + log-rank) |
| `--covariates` | list | `[age]` | Space-separated covariate column names for Cox model |

**Note:** `--output` is required. `Rscript` must be available on PATH for Cox regression and exact log-rank; a Python fallback is used when R is absent.

## Input CSV Format

```csv
time,event,group,age
2,1,unvaccinated,62
3,0,vaccinated,45
4,1,unvaccinated,58
5,0,vaccinated,39
7,1,unvaccinated,54
8,0,vaccinated,48
```

- `time`: follow-up duration (days, months, or any consistent unit)
- `event`: `1` = event (death, hospitalization, etc.), `0` = censored (lost to follow-up or end of study)
- `group`: categorical grouping variable; KM curves are drawn per group
- Covariates (e.g. `age`): numeric; used in Cox model via `--covariates`

## Output Format

```
output/
├── report.md              # KM table excerpt, log-rank test, Cox model table
├── result.json            # Machine-readable summary
├── survival_table.csv     # Full KM table (time, surv, n.risk, n.event)
├── cox_results.csv        # Cox model coefficients (if covariates provided and R available)
├── logrank_test.csv       # Log-rank chi-squared and p-value
└── survival_runner.R      # Auto-generated R script (informational)
```

**survival_table.csv columns:** `time`, `surv`, `n.risk`, `n.event`

**cox_results.csv columns:** `term`, `coef`, `exp.coef.` (hazard ratio), `se.coef.`, `z`, `Pr...z..`, `ci_low`, `ci_high`

**logrank_test.csv columns:** `chisq`, `p_value`

**result.json `summary` keys:** `n_subjects`, `n_timepoints`, `n_cox_terms`, `group_col`

**result.json `data` keys:** `kaplan_meier` (list of row dicts), `cox_model` (list of row dicts), `logrank_test` (list of row dicts)

## Sample Output

Demo: 6 subjects, vaccinated vs unvaccinated, covariate = age

```
Kaplan-Meier Summary
- Time column: time
- Event column: event
- Group column: group

Survival Tail
| Time | Survival | At risk | Events |
|------|----------|---------|--------|
| 2    | 0.8333   | 6       | 1      |
| 4    | 0.6667   | 5       | 1      |
| 7    | 0.5000   | 4       | 1      |

Log-rank Test
- Chi-squared: 2.4000
- p-value: 0.1213

Cox Model
| Term | Hazard ratio | 95% CI          | p-value |
|------|-------------|-----------------|---------|
| age  | 1.0821      | 0.9201 to 1.2730 | 0.3401  |
```

Interpretation: The log-rank test (p=0.12) does not reach conventional significance in this small demo. The Cox HR for age (1.08 per year) suggests a trend toward increased risk with age, though the CI is wide.

## Code Examples

```bash
# Demo mode
python skills/survival-analysis/survival_analysis.py \
  --demo --output /tmp/survival_demo

# Real cohort with group comparison and age covariate
python skills/survival-analysis/survival_analysis.py \
  --input cohort.csv \
  --time-col follow_up_days \
  --event-col died \
  --group-col treatment_arm \
  --covariates age sex \
  --output /tmp/survival_trial

# KM only (no covariates for Cox)
python skills/survival-analysis/survival_analysis.py \
  --input cohort.csv \
  --time-col days \
  --event-col event \
  --group-col group \
  --covariates \
  --output /tmp/km_only

# ```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Rscript is required for Cox regression via the R `survival` package; Python fallback computes manual KM and approximate log-rank only.
- Cox model is skipped (empty table) if `--covariates` is empty or Rscript is unavailable.
- Write `report.md`, `result.json`, `survival_table.csv`, `cox_results.csv`, and `logrank_test.csv`.

## Chaining

- Works well with: `epi-analyst`, `meta-analysis`, `policy-evaluator`, `risk-factor-regression`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `RuntimeError: Rscript not found on PATH` | R not installed | Install R: `brew install r` or from CRAN; Python fallback handles KM and log-rank |
| `Error in coxph`: non-convergence | Covariate perfectly separates groups or too few events | Remove problematic covariates or use simpler model |
| `cox_results.csv` is empty | Rscript unavailable or `--covariates` not set | Install R or add covariate names to `--covariates` |
| KM survival stays at 1.0 | `event` column is all 0 (no events) | Check `event` column — 1 must denote the event of interest |
| Log-rank `chisq: NA` | `--group-col` not provided or column not found | Specify `--group-col` with a valid column name |

## Trigger Keywords

- `survival`
- `survival analysis`
- `kaplan-meier`
- `cox regression`
- `time to event`
- `censoring`
- `hazard ratio`
- `log-rank test`
- `survival curve`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python survival_analysis.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
