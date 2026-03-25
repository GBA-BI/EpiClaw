---
name: disease-modeler
description: "Deterministic SIR/SEIR/SEIRS compartmental ODE models; fit β and γ from case data; R₀..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [SIR, SEIR, compartmental-model, R0, epidemic-dynamics, disease-modeling]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"\ud83d\udcc8","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"uv","package":"requests","bins":[]}],"trigger_keywords":["modeler","disease modeler","sir model","seir model","compartmental model","r0","reproduction number","herd immunity","epidemic dynamics","disease modeling"]}}
---

# 📈 Disease Modeler

Use this skill when the user needs deterministic SIR/SEIR/SEIRS compartmental ODE models; fit β and γ from case data; R₀ and Rₜ estimation; scenario comparison.

## OpenClaw Routing

- Route here for: `modeler`, `disease modeler`, `sir model`, `seir model`, `compartmental model`, `r0`
- Alias: `modeler`
- Entrypoint: `skills/disease-modeler/disease_modeler.py`
- Expected inputs: Case time series CSV with columns `date`, `cases` (for fitting), or direct parameter specification via CLI flags.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--input` | path | none | CSV with columns `date`, `cases` — triggers parameter fitting via Nelder-Mead |
| `--output` | path | required | Output directory for report, figures, and JSON |
| `--demo` | flag | off | Run demo: SIR, R₀=2.5, γ=1/10, N=100,000, 180 days |
| `--model` | choice | `sir` | Compartmental model: `sir`, `seir`, or `seirs` |
| `--r0` | float | `2.5` | Basic reproduction number (used if `--beta` not given) |
| `--beta` | float | none | Transmission rate β (overrides `--r0` if both given) |
| `--gamma` | float | `0.1` | Recovery rate γ = 1 / infectious_period_days |
| `--sigma` | float | `0.2` | Incubation rate σ = 1 / latent_period_days (SEIR/SEIRS only) |
| `--population` | float | `100000` | Total population size N |
| `--initial-infected` | float | `10` | Initial infected count I₀ |
| `--days` | int | `180` | Simulation duration in days |
| `--pathogen` | string | none | Pathogen name for optional WHO data retrieval |
| `--country` | string | none | ISO3 country code for optional WHO data retrieval |

**Parameter resolution:** If `--r0` is given, β = R₀ × γ. If `--beta` is given, R₀ = β / γ. If neither, R₀ = 2.5 (default).

## Output Format

```
output/
├── report.md                  # Summary metrics, fitted parameters, figure paths
├── result.json                # Machine-readable summary envelope
└── figures/
    ├── compartments.png       # S/E/I/R trajectories over time
    └── epi_curve.png          # Daily new cases bar chart
```

**result.json `summary` keys:**

| Key | Description |
|-----|-------------|
| `peak_infected` | Maximum simultaneous infected count |
| `peak_day` | Day of peak infection |
| `attack_rate` | Final proportion of population infected (0–1) |
| `final_recovered` | Number recovered/removed at end of simulation |
| `R0` | Basic reproduction number used in simulation |
| `total_new_cases` | Total incident cases over simulation period |

**result.json `data` keys:** `parameters`, `model`, `days`, `fit` (null if no `--input`), `who_data_points`

## Sample Output

Demo: SIR, N=100,000, R₀=2.5, γ=0.1, 180 days

```
Summary
- Peak infected: 14,231 on day 77
- Attack rate: 0.8923 (89.2% of population)
- Final recovered: 89,230
- Total new cases: 89,230
- R₀: 2.5

Parameter Fit (if --input provided)
- Fitted beta: 0.252140
- Fitted gamma: 0.098311
- RSS: 1823.4
```

## Code Examples

```bash
# Demo mode
python skills/disease-modeler/disease_modeler.py --demo --output /tmp/modeler_demo

# SIR with R0=3 (COVID-like)
python skills/disease-modeler/disease_modeler.py \
  --model sir --r0 3.0 --gamma 0.1 \
  --population 500000 --initial-infected 5 \
  --days 200 --output /tmp/sir_covid

# SEIR model with explicit latent period (5 days mean)
python skills/disease-modeler/disease_modeler.py \
  --model seir --r0 2.5 --gamma 0.1 --sigma 0.2 \
  --population 1000000 --output /tmp/seir_out

# Fit to observed case data (estimates beta and gamma from data)
python skills/disease-modeler/disease_modeler.py \
  --input observed_cases.csv \
  --model sir \
  --population 250000 \
  --output /tmp/sir_fit

# SEIRS with waning immunity scenario
python skills/disease-modeler/disease_modeler.py \
  --model seirs --r0 2.0 --gamma 0.1 --sigma 0.2 \
  --days 365 --output /tmp/seirs_out

# ```

**Input CSV format (for parameter fitting):**
```
date,cases
2025-01-01,5
2025-01-02,8
2025-01-03,14
```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Parameter fitting uses Nelder-Mead optimization (scipy.optimize.minimize); fit quality is indicated by RSS.
- SEIR/SEIRS models require `--sigma`; default is 0.2 (5-day latent period).
- WHO data retrieval via `--pathogen` and `--country` is optional and supplements context but does not override direct parameter inputs.
- Write `report.md`, `result.json`, `figures/compartments.png`, and `figures/epi_curve.png`.

## Downstream Skill Chains

```bash
# Modeler → stochastic ensemble comparison
python skills/disease-modeler/disease_modeler.py \
  --model seir --r0 2.5 --output /tmp/det
python skills/stochastic-modeler/stochastic_modeler.py \
  --r0 2.5 --output /tmp/stoch

# Fetch data → fit model → Rt comparison
python skills/epi-data-fetcher/epi_data_fetcher.py --disease covid-19 --source owid --country DEU
python skills/disease-modeler/disease_modeler.py --input output/data.csv --model seir --output /tmp/fitted
```

## Chaining

- Works well with: `disease-forecaster`, `stochastic-modeler`, `rt-estimator`, `epi-data-fetcher`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `ValueError: gamma must be > 0` | `--gamma 0` or negative value | Use reciprocal of infectious period, e.g. `--gamma 0.1` for 10-day period |
| `ValueError: initial-infected must be <= population` | I₀ > N | Reduce `--initial-infected` |
| Attack rate near 100% with low R₀ | Very high initial-infected fraction | Check `--initial-infected` relative to `--population` |
| Fitting RSS very large | Data not matching model structure | Try `--model seir` instead of `sir`; check for multi-wave data |
| `[info] WHO connector unavailable` | epiclaw connectors not installed or network offline | Normal; model runs with explicit parameters without WHO data |

## Trigger Keywords

- `modeler`
- `disease modeler`
- `sir model`
- `seir model`
- `compartmental model`
- `r0`
- `reproduction number`
- `herd immunity`
- `epidemic dynamics`
- `disease modeling`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python disease_modeler.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
