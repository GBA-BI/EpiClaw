#!/usr/bin/env python3
"""EpiClaw Meta-Analysis -- fixed and random-effects pooling with forest plot."""
from __future__ import annotations
import argparse, csv, math, sys
import sys
from pathlib import Path
import numpy as np

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "meta-analysis"


# ---------------------------------------------------------------------------
# Core pooling functions
# ---------------------------------------------------------------------------

def fixed_effects(log_effects: list[float], variances: list[float]) -> tuple[float, float, float]:
    """Inverse-variance fixed-effects pooling.

    Returns (pooled_log_effect, lower, upper) on log scale.
    """
    weights = [1.0 / v for v in variances]
    pooled = sum(w * e for w, e in zip(weights, log_effects)) / sum(weights)
    se_pooled = math.sqrt(1.0 / sum(weights))
    z = 1.959964
    return pooled, pooled - z * se_pooled, pooled + z * se_pooled


def cochrans_q(log_effects: list[float], variances: list[float]) -> tuple[float, float]:
    """Compute Cochran's Q statistic and p-value."""
    from scipy.stats import chi2
    weights = [1.0 / v for v in variances]
    w_sum = sum(weights)
    pooled = sum(w * e for w, e in zip(weights, log_effects)) / w_sum
    q = sum(w * (e - pooled) ** 2 for w, e in zip(weights, log_effects))
    k = len(log_effects)
    p_val = float(1.0 - chi2.cdf(q, df=k - 1))
    return q, p_val


def random_effects_dl(
    log_effects: list[float], variances: list[float]

):
    weights = [1.0 / v for v in variances]
    pooled_fixed = sum(w * e for w, e in zip(weights, log_effects)) / sum(weights)
    q = sum(w * (e - pooled_fixed) ** 2 for w, e in zip(weights, log_effects))
    c = sum(weights) - sum(w * w for w in weights) / sum(weights)
    tau2 = max(0.0, (q - (len(log_effects) - 1)) / c) if c > 0 else 0.0
    re_weights = [1.0 / (v + tau2) for v in variances]
    pooled = sum(w * e for w, e in zip(re_weights, log_effects)) / sum(re_weights)
    se_pooled = math.sqrt(1.0 / sum(re_weights))
    z = 1.959964
    i_sq = max(0.0, (q - (len(log_effects) - 1)) / q * 100.0) if q > 0 else 0.0
    return pooled, pooled - z * se_pooled, pooled + z * se_pooled, tau2, i_sq
# ---------------------------------------------------------------------------
# CSV input loader
# ---------------------------------------------------------------------------

def load_studies_csv(
    path: str,
    effect_measure: str = "rr",
) -> tuple[list[float], list[float], list[int], list[str]]:
    """Load study-level effect sizes from CSV.

    Supported column sets (auto-detected):
      1. log_effect, variance [, study [, n]]   — pre-computed log scale
      2. log_effect, se       [, study [, n]]   — pre-computed, SE provided
      3. effect, se           [, study [, n]]   — natural scale (log-transformed internally)
      4. effect, variance     [, study [, n]]   — natural scale

    For OR/RR: effect column expected as the ratio (>0); logged internally unless
    ``log_effect`` column used.

    Returns: (log_effects, variances, sample_sizes, labels)
    """
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    if not rows:
        raise ValueError(f"No data rows found in {path}")

    cols = set(rows[0].keys())
    log_effects: list[float] = []
    variances: list[float] = []
    sample_sizes: list[int] = []
    labels: list[str] = []

    for i, row in enumerate(rows):
        label = row.get("study", f"Study {i + 1}").strip()
        n = int(float(row["n"])) if "n" in cols and row.get("n") else 0

        if "log_effect" in cols:
            le = float(row["log_effect"])
        elif "effect" in cols:
            eff = float(row["effect"])
            if eff <= 0:
                raise ValueError(f"Row {i+1}: effect must be > 0 for log transformation (got {eff})")
            le = math.log(eff)
        else:
            raise ValueError("CSV must contain 'log_effect' or 'effect' column")

        if "variance" in cols:
            var = float(row["variance"])
        elif "se" in cols:
            var = float(row["se"]) ** 2
        else:
            raise ValueError("CSV must contain 'variance' or 'se' column")

        if var <= 0:
            raise ValueError(f"Row {i+1}: variance must be > 0 (got {var})")

        log_effects.append(le)
        variances.append(var)
        sample_sizes.append(n)
        labels.append(label)

    return log_effects, variances, sample_sizes, labels


# ---------------------------------------------------------------------------
# Demo data generation
# ---------------------------------------------------------------------------

def generate_demo_studies(seed: int = 42) -> tuple[list[float], list[float], list[int], list[str]]:
    """8 studies with random log(RR) ~ N(-0.3, 0.3), SE from random sample sizes."""
    import numpy as np
    rng = np.random.default_rng(seed)
    k = 8
    log_rr = rng.normal(-0.3, 0.3, k).tolist()
    ns = rng.integers(50, 500, k).tolist()
    # Approximate SE: sqrt(4/n) for two-arm proportion data
    ses = [math.sqrt(4.0 / n) for n in ns]
    variances = [s ** 2 for s in ses]
    labels = [f"Study {i + 1}" for i in range(k)]
    return log_rr, variances, [int(n) for n in ns], labels


# ---------------------------------------------------------------------------
# Forest plot
# ---------------------------------------------------------------------------

def plot_forest(
    log_effects: list[float],
    variances: list[float],
    pooled_log: float,
    pooled_lower: float,
    pooled_upper: float,
    weights: list[float],
    effect_measure: str,
    out_dir: Path,
    study_labels: list[str] | None = None,

):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = study_labels or [f"Study {idx + 1}" for idx in range(len(log_effects))]
    effects = [math.exp(v) for v in log_effects]
    ci_lowers = [math.exp(e - 1.959964 * math.sqrt(v)) for e, v in zip(log_effects, variances)]
    ci_uppers = [math.exp(e + 1.959964 * math.sqrt(v)) for e, v in zip(log_effects, variances)]
    pooled_effect = math.exp(pooled_log)
    pooled_lower_eff = math.exp(pooled_lower)
    pooled_upper_eff = math.exp(pooled_upper)
    y = list(range(len(labels), 0, -1))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(effects, y, xerr=[np.array(effects) - np.array(ci_lowers), np.array(ci_uppers) - np.array(effects)], fmt="o")
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1)
    ax.scatter([pooled_effect], [0], marker="D", color="red", s=60)
    ax.hlines(0, pooled_lower_eff, pooled_upper_eff, color="red", linewidth=2)
    ax.set_yticks(y + [0])
    ax.set_yticklabels(labels + ["Pooled"])
    ax.set_xlabel(effect_measure)
    ax.set_title("Forest plot")
    fig.tight_layout()
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / "forest_plot.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig_path
# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(
    k: int, method: str, pooled: float, lower: float, upper: float,
    i_sq: float, q_p: float, effect_measure: str,
    log_effects: list[float], variances: list[float],
    fig_path: Path | None,
    study_labels: list[str] | None = None,
):
    labels = study_labels or [f"Study {idx + 1}" for idx in range(len(log_effects))]
    lines = [
        generate_report_header(
            title="Meta-Analysis Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Method": method, "Effect measure": effect_measure, "Version": VERSION},
        ),
        "## Summary",
        "",
        f"- Studies pooled: `{k}`",
        f"- Pooled {effect_measure}: `{pooled:.3f}` ({lower:.3f}–{upper:.3f})",
        f"- I²: `{i_sq:.1f}%`",
        f"- Heterogeneity p-value: `{q_p:.4f}`",
        "",
        "## Study Inputs",
        "",
        "| Study | Effect | Variance |",
        "|---|---|---|",
    ]
    for label, effect, variance in zip(labels, log_effects, variances):
        lines.append(f"| {label} | {math.exp(effect):.3f} | {variance:.4f} |")
    if fig_path:
        lines.extend(["", f"Forest plot: `{fig_path}`", ""])
    lines.append(generate_report_footer())
    return "\n".join(lines)
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Meta-analysis with fixed/random effects")
    parser.add_argument("--input", default=None)
    parser.add_argument("--effect-measure", choices=["rr", "or", "rd"], default="rr")
    parser.add_argument("--method", choices=["fixed", "random"], default="random")
    parser.add_argument("--output", default="output/meta-analysis")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    args = parser.parse_args(argv)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw {SKILL_NAME} v{VERSION}")
    print(f"[info] Effect measure: {args.effect_measure}, Method: {args.method}")

    study_labels: list[str] | None = None
    if args.demo or not args.input:
        log_effects, variances, ns, _ = generate_demo_studies()
        print(f"[info] Using built-in demo studies (n=8).")
    else:
        print(f"[info] Loading studies from: {args.input}")
        log_effects, variances, ns, study_labels = load_studies_csv(args.input, args.effect_measure)
    k = len(log_effects)
    print(f"[info] {k} studies loaded.")

    q, q_p = cochrans_q(log_effects, variances)
    print(f"[info] Cochran's Q={q:.3f}, p={q_p:.4f}")

    if args.method == "fixed":
        pooled_log, lower_log, upper_log = fixed_effects(log_effects, variances)
        tau2, i_sq = 0.0, max(0.0, (q - (k - 1)) / q * 100.0) if q > 0 else 0.0
        weights = [1.0 / v for v in variances]
    else:
        pooled_log, lower_log, upper_log, tau2, i_sq = random_effects_dl(log_effects, variances)
        weights = [1.0 / (v + tau2) for v in variances]

    # Exponentiate to get RR/OR/RD scale
    pooled = math.exp(pooled_log)
    lower = math.exp(lower_log)
    upper = math.exp(upper_log)
    print(f"[info] Pooled {args.effect_measure.upper()}={pooled:.3f} (95% CI: {lower:.3f}–{upper:.3f})")
    print(f"[info] I²={i_sq:.1f}%, τ²={tau2:.4f}")

    fig_path: Path | None = None
    try:
        fig_path = plot_forest(
            log_effects, variances, pooled_log, lower_log, upper_log,
            weights, args.effect_measure.upper(), out_dir,
            study_labels=study_labels,
        )
    except Exception as exc:
        print(f"[warn] Could not generate forest plot: {exc}")

    report_md = build_report(
        k, args.method, pooled, lower, upper, i_sq, q_p,
        args.effect_measure.upper(), log_effects, variances, fig_path,
        study_labels=study_labels,
    )
    report_path = out_dir / "report.md"
    report_path.write_text(report_md)
    print(f"[info] Report written to {report_path}")

    summary = {
        "n_studies": k,
        "method": args.method,
        "pooled_effect": round(pooled, 4),
        "pooled_lower": round(lower, 4),
        "pooled_upper": round(upper, 4),
        "i_squared": round(i_sq, 2),
        "heterogeneity_p": round(q_p, 6),
        "effect_measure": args.effect_measure.upper(),
    }
    ci_lowers = [math.exp(e - 1.959964 * math.sqrt(v)) for e, v in zip(log_effects, variances)]
    ci_uppers = [math.exp(e + 1.959964 * math.sqrt(v)) for e, v in zip(log_effects, variances)]
    w_sum = sum(weights)
    resolved_labels = study_labels or [f"Study {i + 1}" for i in range(k)]
    data = {
        "study_labels": resolved_labels,
        "study_effects": [round(math.exp(e), 4) for e in log_effects],
        "study_ci_lower": [round(v, 4) for v in ci_lowers],
        "study_ci_upper": [round(v, 4) for v in ci_uppers],
        "study_weights": [round(w / w_sum * 100, 2) for w in weights],
        "tau2": round(tau2, 6),
        "cochrans_q": round(q, 4),
        "sample_sizes": ns,
    }
    result_path = write_result_json(out_dir, SKILL_NAME, VERSION, summary, data)
    print(f"[info] Result JSON written to {result_path}")
    print("[info] Done.")


if __name__ == "__main__":
    main()
