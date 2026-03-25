---
name: rt-estimator
description: "Real-time effective reproduction number Rₜ estimation (Cori/EpiEstim, Wallinga-..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [reproduction-number, Rt, EpiEstim, Cori, epidemic-dynamics, transmission]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"📡","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["rt","rt estimator","reproduction number","rₜ","r effective","epiestim","cori method","transmission rate","epidemic growth","epidemic control"]}}
---

# 📡 Rt Estimator

Use this skill when the user needs real-time effective reproduction number Rₜ estimation (Cori/EpiEstim, Wallinga-Teunis); uncertainty intervals; trend analysis.

## OpenClaw Routing

- Route here for: `rt`, `rt estimator`, `reproduction number`, `rₜ`, `r effective`, `epiestim`
- Alias: `rt`
- Entrypoint: `skills/rt-estimator/rt_estimator.py`
- Expected inputs: Daily case time series CSV with columns `date` (YYYY-MM-DD) and `cases` (integer counts).

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--input` | path | none | Input CSV file with columns: `date`, `cases` |
| `--output` | path | `/tmp/epiclaw_rt_estimator` | Output directory for report, figures, and JSON |
| `--pathogen` | string | `"Unknown Pathogen"` | Pathogen name used in report title and figure labels |
| `--method` | choice | `cori` | Estimation method: `cori` (Bayesian, EpiEstim-style) or `wallingateunis` (Poisson-based) |
| `--mean-si` | float | `5.0` | Mean serial interval in days |
| `--std-si` | float | `3.0` | Standard deviation of serial interval in days |
| `--window` | int | `7` | Sliding estimation window size in days |
| `--prior-mean` | float | `5.0` | Prior mean for Gamma prior on Rt (Cori method only) |
| `--prior-sd` | float | `5.0` | Prior SD for Gamma prior on Rt (Cori method only) |
| `--demo` | flag | off | Run built-in 21-day synthetic epidemic time series |

## Output Format

```
output/
├── report.md              # Narrative summary with daily Rt table
├── result.json            # Machine-readable summary envelope
└── figures/
    └── rt_curve.png       # Two-panel plot: case bars + Rt ribbon with 95% CI
```

**result.json structure:**
- `summary.days_analyzed` — number of days with valid Rt estimates
- `summary.final_rt` — Rt on the last day
- `summary.peak_rt` — maximum Rt observed
- `summary.peak_day` — day index of peak Rt
- `summary.days_rt_above_1` — count of days where Rt > 1.0
- `data.dates` — list of date strings
- `data.cases` — list of integer case counts
- `data.rt` — list of point estimates (null where window not yet full)
- `data.rt_lower` — lower 95% credible/confidence interval
- `data.rt_upper` — upper 95% credible/confidence interval

**report.md table columns:** `Day | Date | Cases | Rt | Lower | Upper`

## Sample Output

```
Summary
- Days analysed: 15
- Final Rt: 0.7823
- Peak Rt: 2.1041 on day 6
- Days with Rt > 1: 8

Daily Estimates (excerpt)
| Day | Date       | Cases | Rt     | Lower  | Upper  |
|-----|------------|-------|--------|--------|--------|
| 7   | 2025-01-07 | 13    | 2.1041 | 1.4823 | 2.9312 |
| 14  | 2025-01-14 | 10    | 1.0214 | 0.6901 | 1.4582 |
| 21  | 2025-01-21 | 5     | 0.7823 | 0.4901 | 1.1801 |
```

Interpretation: Rt crossed below 1.0 on day ~14, indicating the epidemic is declining. Sustained Rt < 1 for the final week confirms epidemic control.

## Code Examples

```bash
# Demo mode (no input required)
python skills/rt-estimator/rt_estimator.py --demo --output /tmp/rt_demo

# Real data: COVID-19 with SARS-CoV-2 serial interval
python skills/rt-estimator/rt_estimator.py \
  --input cases.csv \
  --pathogen "COVID-19" \
  --mean-si 5.2 \
  --std-si 4.9 \
  --method cori \
  --window 7 \
  --output /tmp/rt_covid

# Influenza with shorter serial interval and narrower prior
python skills/rt-estimator/rt_estimator.py \
  --input flu_cases.csv \
  --pathogen "Influenza A" \
  --mean-si 2.6 \
  --std-si 1.5 \
  --prior-mean 2.0 \
  --prior-sd 2.0 \
  --output /tmp/rt_flu

# Wallinga-Teunis method
python skills/rt-estimator/rt_estimator.py \
  --input cases.csv \
  --method wallingateunis \
  --output /tmp/rt_wt

# ```

**Input CSV format:**
```
date,cases
2025-01-01,3
2025-01-02,4
2025-01-03,7
```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- scipy is used for exact Gamma quantiles (95% CI); a normal approximation is used if scipy is absent.
- The Cori method returns `null` for the first `window - 1` days (insufficient data to estimate).
- Write `report.md` and `result.json`, plus the `figures/rt_curve.png` panel plot.

## Downstream Skill Chains

```bash
# Fetch WHO data → Rt estimation
python skills/epi-data-fetcher/epi_data_fetcher.py \
  --disease covid-19 --source owid --country USA --output /tmp/data
python skills/rt-estimator/rt_estimator.py \
  --input /tmp/data/data.csv --pathogen "COVID-19" --output /tmp/rt

# Rt → dashboard display
python skills/rt-estimator/rt_estimator.py --input cases.csv --output /tmp/rt
python skills/multi-pathogen-dashboard/dashboard.py --rt-dir /tmp/rt
```

## Chaining

- Works well with: `epi-data-fetcher`, `contact-tracing`, `early-warning-system`, `disease-modeler`, `epi-orchestrator`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `Rt is null for all days` | Window larger than dataset | Reduce `--window` or provide more data days |
| `KeyError: 'date'` or `'cases'` | CSV column name mismatch | Rename columns to `date` and `cases` exactly |
| `scipy not found` warning | scipy not installed | Run `pip install scipy`; normal approximation CI used as fallback |
| Peak Rt unexpectedly high | Very small case counts in early window | Use `--prior-mean` closer to expected Rt; increase `--window` |
| Figure not generated | matplotlib missing | Run `pip install matplotlib`; report still written without figure |

## Trigger Keywords

- `rt`
- `rt estimator`
- `reproduction number`
- `rₜ`
- `r effective`
- `epiestim`
- `cori method`
- `transmission rate`
- `epidemic growth`
- `epidemic control`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python rt_estimator.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
