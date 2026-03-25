---
name: epi-calculator
description: "2×2 table analysis: RR, OR, AR, PAR, NNT with 95% Wilson CIs; chi-squared; Fisher's..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [epidemiology, biostatistics, measures-of-association]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🧮","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"scipy","bins":[]}],"trigger_keywords":["calc","epi calculator","odds ratio","relative risk","2x2 table","attack rate","confidence interval","number needed to treat","population attributable risk"]}}
---

# 🧮 Epi Calculator

Use this skill when the user needs 2×2 table analysis: RR, OR, AR, PAR, NNT with 95% Wilson CIs; chi-squared; Fisher's exact; Mantel-Haenszel stratified analysis.

## OpenClaw Routing

- Route here for: `calc`, `epi calculator`, `odds ratio`, `relative risk`, `2x2 table`, `attack rate`
- Alias: `calc`
- Entrypoint: `skills/epi-calculator/epi_calculator.py`
- Expected inputs: 2×2 tables supplied as CLI counts, or a CSV with columns `group`, `outcome`, `count`.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--demo` | flag | off | Run built-in demo (a=40, b=60, c=10, d=90) |
| `--input` | path | none | CSV file with columns: `group`, `outcome`, `count` |
| `--measure` | choice | `all` | Subset of metrics to output: `all`, `rr`, `or`, `chi2` |
| `--exposed-cases` | int | none | Count a: exposed cases (alternative to `--input`) |
| `--exposed-total` | int | none | Total exposed persons (a + b) |
| `--unexposed-cases` | int | none | Count c: unexposed cases |
| `--unexposed-total` | int | none | Total unexposed persons (c + d) |
| `--output` | path | required | Output directory for report and JSON |

**Note:** `--output` is required. Either `--input` or all four count arguments must be provided (or `--demo`).

## Input CSV Format

```csv
group,outcome,count
exposed,case,40
exposed,non-case,60
unexposed,case,10
unexposed,non-case,90
```

## Output Format

```
output/
├── report.md     # 2×2 table, all measures, chi-squared, Fisher's exact
└── result.json   # Machine-readable summary with selected metrics
```

**Metrics computed (--measure all):**

| Key | Description |
|-----|-------------|
| `risk_exposed` | Attack rate in exposed group (a / (a+b)) |
| `risk_unexposed` | Attack rate in unexposed group (c / (c+d)) |
| `attack_rate_exposed_pct` | Attack rate exposed, percent |
| `attack_rate_unexposed_pct` | Attack rate unexposed, percent |
| `risk_ratio` | RR with 95% CI (log-normal, Wald) |
| `odds_ratio` | OR with 95% CI (Woolf/Wald) |
| `risk_difference` | Absolute risk difference |
| `prevalence` | Overall prevalence in the total population |
| `population_attributable_risk` | PAR = overall risk − unexposed risk |
| `population_attributable_risk_pct` | PAR% = PAR / overall risk × 100 |
| `number_needed_to_treat_or_harm` | NNT = 1 / \|risk difference\| |
| `chi2` / `chi2_p` | Yates-corrected chi-squared (requires scipy) |
| `fisher_or` / `fisher_p` | Fisher exact OR and two-sided p-value (requires scipy) |

Haldane–Anscombe continuity correction (add 0.5) is applied to all RR/OR calculations.

## Sample Output

Demo input: a=40, b=60, c=10, d=90

```
| Metric                      | Value                          |
|-----------------------------|-------------------------------|
| Risk ratio                  | 2.8571 (1.5239, 5.3571)       |
| Odds ratio                  | 5.1429 (2.3801, 11.1147)      |
| Risk difference             | 0.2000                         |
| Attack rate exposed         | 40.00%                         |
| Attack rate unexposed       | 10.00%                         |
| Prevalence                  | 0.2500                         |
| Population attributable risk| 0.1500                         |
| PAR%                        | 60.00%                         |
| NNT/NNH                     | 5.00                           |
| Chi-squared                 | 20.8333 (p=4.97e-06)          |
| Fisher exact                | OR=6.0 (p=2.13e-06)           |
```

Interpretation: Exposed persons have 2.9× the risk of disease compared to unexposed. 60% of cases in the total population are attributable to the exposure.

## Code Examples

```bash
# Demo mode
python skills/epi-calculator/epi_calculator.py --demo --output /tmp/calc_demo

# CLI counts (no CSV needed)
python skills/epi-calculator/epi_calculator.py \
  --exposed-cases 40 --exposed-total 100 \
  --unexposed-cases 10 --unexposed-total 100 \
  --output /tmp/calc_out

# From CSV file, only RR metrics
python skills/epi-calculator/epi_calculator.py \
  --input table.csv \
  --measure rr \
  --output /tmp/calc_rr

# ```

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- scipy is required for chi-squared and Fisher's exact; RR and OR are computed with numpy only.
- Write `report.md` and `result.json`.

## Chaining

- Works well with: `epi-analyst`, `meta-analysis`, `policy-evaluator`, `vaccine-effectiveness`
- Cite whether results came from user input, demo data, or external connectors.

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `RuntimeError: CSV must contain exposed/unexposed x case/non-case rows` | Wrong group/outcome labels in CSV | Check CSV rows use exactly `exposed`/`unexposed` and `case`/`non-case` |
| `chi2: None` in output | scipy not installed | Run `pip install scipy` |
| `Computed 2x2 cells must be non-negative` | `--exposed-total` < `--exposed-cases` | Ensure totals are >= case counts |
| NNT shows `undefined` | Risk difference = 0 (equal attack rates) | Verify input data; NNT is not meaningful when RD = 0 |
| Very wide confidence intervals | Small cell counts (< 5) | Results are still valid but interpret cautiously; consider exact methods |

## Trigger Keywords

- `calc`
- `epi calculator`
- `odds ratio`
- `relative risk`
- `2x2 table`
- `attack rate`
- `confidence interval`
- `number needed to treat`
- `population attributable risk`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python epi_calculator.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
