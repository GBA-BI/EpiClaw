---
name: meta-analysis
description: "Systematic review meta-analysis: fixed/random effects pooling, forest plots, funnel..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [meta-analysis, systematic-review, forest-plot, heterogeneity, DerSimonian-Laird]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"📋","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["meta","meta analysis","meta-analysis","systematic review","forest plot","pooled effect","i-squared","heterogeneity","dersimonian-laird","publication bias"]}}
---

# 📋 Meta Analysis

Use this skill when the user needs systematic review meta-analysis: fixed/random effects pooling, forest plots, funnel plots, I² heterogeneity, Egger's test.

## OpenClaw Routing

- Route here for: `meta`, `meta analysis`, `meta-analysis`, `systematic review`, `forest plot`, `pooled effect`
- Alias: `meta`
- Entrypoint: `skills/meta-analysis/meta_analysis.py`
- Expected inputs: Study-level effect size CSV, or raw 2×2 tables for multiple studies.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--input` | path | none | CSV file with study-level effect sizes (see format below) |
| `--effect-measure` | choice | `rr` | Effect measure: `rr` (risk ratio), `or` (odds ratio), `rd` (risk difference) |
| `--method` | choice | `random` | Pooling method: `random` (DerSimonian-Laird) or `fixed` (inverse-variance) |
| `--output` | path | `output/meta-analysis` | Output directory |
| `--demo` | flag | off | Run built-in demo with 8 synthetic studies |

## Input CSV Format

The CSV auto-detects the column layout. Supported combinations:

```csv
# Format 1: pre-computed log scale
study,log_effect,variance,n
Smith 2020,-0.357,0.0156,250
Jones 2021,-0.182,0.0089,412

# Format 2: pre-computed with SE
study,log_effect,se,n
Smith 2020,-0.357,0.1249,250

# Format 3: natural scale effect + SE (logged internally)
study,effect,se,n
Smith 2020,0.700,0.1249,250

# Format 4: natural scale effect + variance
study,effect,variance,n
Smith 2020,0.700,0.0156,250
```

**Rules:** `effect` must be > 0 (used as ratio; logged internally). `variance` must be > 0. `study` and `n` columns are optional.

## Output Format

```
output/
├── report.md               # Pooled estimate, I², heterogeneity table, study inputs
├── result.json             # Machine-readable summary + per-study data
└── figures/
    └── forest_plot.png     # Forest plot with per-study CIs and pooled diamond
```

**result.json `summary` keys:**

| Key | Description |
|-----|-------------|
| `n_studies` | Number of studies pooled |
| `method` | `fixed` or `random` |
| `pooled_effect` | Exponentiated pooled estimate (RR/OR scale) |
| `pooled_lower` | Lower 95% CI |
| `pooled_upper` | Upper 95% CI |
| `i_squared` | I² heterogeneity statistic (%) |
| `heterogeneity_p` | Cochran's Q p-value |
| `effect_measure` | `RR`, `OR`, or `RD` |

**result.json `data` keys:** `study_labels`, `study_effects`, `study_ci_lower`, `study_ci_upper`, `study_weights` (%), `tau2`, `cochrans_q`, `sample_sizes`

## Sample Output

Demo: 8 studies, random effects, effect measure = RR

```
Summary
- Studies pooled: 8
- Pooled RR: 0.742 (0.618–0.891)
- I²: 31.4%
- Heterogeneity p-value: 0.1823

Study Inputs
| Study   | Effect | Variance |
|---------|--------|----------|
| Study 1 | 0.681  | 0.0312   |
| Study 2 | 0.751  | 0.0189   |
| Study 3 | 0.812  | 0.0241   |
...
```

Interpretation: The pooled RR of 0.74 (95% CI 0.62–0.89) suggests a 26% risk reduction. Moderate heterogeneity (I²=31%) does not preclude pooling under random effects.

## Code Examples

```bash
# Demo mode (8 synthetic studies)
python skills/meta-analysis/meta_analysis.py --demo --output /tmp/meta_demo

# Random effects (default) from CSV
python skills/meta-analysis/meta_analysis.py \
  --input studies.csv \
  --effect-measure rr \
  --method random \
  --output /tmp/meta_rr

# Fixed effects for OR
python skills/meta-analysis/meta_analysis.py \
  --input studies.csv \
  --effect-measure or \
  --method fixed \
  --output /tmp/meta_or_fixed

# ```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- scipy is required for Cochran's Q p-value computation.
- The DerSimonian-Laird τ² estimator is used for random effects; τ² is floored at 0.
- Forest plot is generated via matplotlib; report is written regardless.
- Write `report.md`, `result.json`, and `figures/forest_plot.png`.

## Chaining

- Works well with: `epi-analyst`, `policy-evaluator`, `epi-calculator`, `lit-reviewer`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `ValueError: CSV must contain 'log_effect' or 'effect' column` | Column named differently | Rename to `effect` or `log_effect` as appropriate |
| `ValueError: effect must be > 0` | Negative or zero effect value | For RR/OR, the effect column should be the ratio (not log); use `log_effect` column for pre-logged values |
| `ValueError: variance must be > 0` | Zero or missing variance | Ensure all `variance` or `se` values are positive numbers |
| I² = 0% but Q p < 0.05 | Low k (few studies) | Q test has low power with k < 5; I² of 0 is a lower bound, not a definitive result |
| Forest plot not generated | matplotlib missing | Run `pip install matplotlib`; report and JSON still written |

## Trigger Keywords

- `meta`
- `meta analysis`
- `meta-analysis`
- `systematic review`
- `forest plot`
- `pooled effect`
- `i-squared`
- `heterogeneity`
- `dersimonian-laird`
- `publication bias`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python meta_analysis.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
