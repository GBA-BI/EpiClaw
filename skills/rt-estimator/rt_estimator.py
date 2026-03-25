#!/usr/bin/env python3
"""EpiClaw Rt Estimator -- Real-time effective reproduction number estimation using Cori/EpiEstim or Wallinga-Teunis methods."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "rt-estimator"


# --------------------------------------------------------------------------- #
# Demo data: discretized SIR model
# --------------------------------------------------------------------------- #

def load_cases(filepath: str) -> tuple[list[str], list[int]]:
    """Load case time series from CSV (columns: date, cases)."""
    dates, cases = [], []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"].strip())
            cases.append(int(row["cases"]))
    return dates, cases


# --------------------------------------------------------------------------- #
# Serial interval distribution (discretized gamma)
# --------------------------------------------------------------------------- #

def discretize_serial_interval(mean_si: float, std_si: float, max_days: int = 30) -> np.ndarray:
    """Discretize a gamma serial interval distribution.

    Returns an array w where w[k] = P(SI = k days), k = 0, 1, ..., max_days.
    Uses scipy.stats.gamma if available; falls back to numpy-based discretization.
    """
    try:
        from scipy.stats import gamma as gamma_dist
        shape = (mean_si / std_si) ** 2
        scale = std_si ** 2 / mean_si
        days = np.arange(0, max_days + 1, dtype=float)
        # P(k) = CDF(k+0.5) - CDF(k-0.5), with k=0 pinned to 0
        cdf_upper = gamma_dist.cdf(days + 0.5, a=shape, scale=scale)
        cdf_lower = np.where(days > 0, gamma_dist.cdf(days - 0.5, a=shape, scale=scale), 0.0)
        w = cdf_upper - cdf_lower
        w[0] = 0.0  # no same-day transmission
    except ImportError:
        # Manual discretization using numpy
        shape = (mean_si / std_si) ** 2
        scale = std_si ** 2 / mean_si
        days = np.arange(1, max_days + 1, dtype=float)
        # Use normalised Poisson approximation: w[k] proportional to gamma PDF at k
        raw = (days ** (shape - 1)) * np.exp(-days / scale)
        raw /= raw.sum()
        w = np.concatenate([[0.0], raw])

    # Normalise (excluding day 0)
    total = w[1:].sum()
    if total > 0:
        w[1:] /= total
    return w


# --------------------------------------------------------------------------- #
# Cori method (EpiEstim-style)
# --------------------------------------------------------------------------- #

def estimate_rt_cori(
    cases: list[int],
    w: np.ndarray,
    window: int = 7,
    prior_a: float = 1.0,
    prior_b: float = 0.2,
):
    """Bayesian Rt estimation (Cori et al. 2013, EpiEstim method).

    Uses a Gamma conjugate prior on Rt:
      Prior:     Rt ~ Gamma(prior_a, rate=prior_b)  [default: mean=5, SD=5]
      Posterior: Rt ~ Gamma(prior_a + sum_cases, rate=prior_b + sum_infectiousness)

    95% credible interval computed from gamma quantiles (or normal approximation if scipy
    is unavailable).

    Default priors match EpiEstim R-package defaults (mean_prior=5, std_prior=5).
    """
    try:
        from scipy.stats import gamma as gamma_dist
        _has_scipy = True
    except ImportError:
        _has_scipy = False

    infectiousness = np.zeros(len(cases), dtype=float)
    rt = [float("nan")] * len(cases)
    rt_lower = [float("nan")] * len(cases)
    rt_upper = [float("nan")] * len(cases)

    for t in range(len(cases)):
        infectiousness[t] = sum(cases[t - s] * float(w[s]) for s in range(1, min(t + 1, len(w))))

    for t in range(window - 1, len(cases)):
        sum_lambda = float(sum(infectiousness[max(0, t - window + 1):t + 1]))
        if sum_lambda <= 0:
            continue
        sum_I = float(sum(cases[max(0, t - window + 1):t + 1]))

        # Gamma posterior parameters
        a_post = prior_a + sum_I
        b_post = prior_b + sum_lambda  # rate parameter (1/scale)

        rt[t] = float(a_post / b_post)  # posterior mean

        if _has_scipy:
            # 95% credible interval from gamma posterior
            scale_post = 1.0 / b_post
            rt_lower[t] = float(gamma_dist.ppf(0.025, a=a_post, scale=scale_post))
            rt_upper[t] = float(gamma_dist.ppf(0.975, a=a_post, scale=scale_post))
        else:
            # Normal approximation: posterior SD = sqrt(a_post) / b_post
            se = math.sqrt(a_post) / b_post
            rt_lower[t] = float(max(0.0, rt[t] - 1.959964 * se))
            rt_upper[t] = float(rt[t] + 1.959964 * se)

    return rt, rt_lower, rt_upper
# --------------------------------------------------------------------------- #
# Wallinga-Teunis method (simplified)
# --------------------------------------------------------------------------- #

def estimate_rt_wallinga_teunis(
    cases: list[int],
    w: np.ndarray,
    window: int = 7,
):
    """Wallinga-Teunis Rt estimation with Poisson-based confidence intervals.

    Point estimate: Rt[t] = I[t] / sum_s(I[t-s] * w[s])
    CI: Poisson approximation — SE[log(Rt)] ≈ 1/sqrt(I[t])
    """
    rt = [float("nan")] * len(cases)
    rt_lower = [float("nan")] * len(cases)
    rt_upper = [float("nan")] * len(cases)
    for t in range(1, len(cases)):
        denom = sum(cases[t - s] * float(w[s]) for s in range(1, min(window + 1, len(w), t + 1)))
        if denom <= 0 or cases[t] <= 0:
            continue
        estimate = float(cases[t]) / denom
        rt[t] = estimate
        # Poisson approximation: SE[log(Rt)] ≈ 1/sqrt(I_t)
        log_se = 1.0 / math.sqrt(float(cases[t]))
        rt_lower[t] = max(0.0, estimate * math.exp(-1.959964 * log_se))
        rt_upper[t] = estimate * math.exp(1.959964 * log_se)
    return rt, rt_lower, rt_upper
# --------------------------------------------------------------------------- #
# Figure generation
# --------------------------------------------------------------------------- #

def generate_rt_figure(
    dates: list[str],
    cases: list[int],
    rt: list[float],
    rt_lower: list[float],
    rt_upper: list[float],
    pathogen: str,
    output_path: Path,

):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.arange(len(cases))
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].bar(x, cases, color="#2563eb")
    axes[0].set_ylabel("Cases")
    axes[0].set_title(f"Rt estimation — {pathogen}")
    axes[1].plot(x, np.array(rt, dtype=float), color="#dc2626", linewidth=2)
    axes[1].fill_between(x, np.array(rt_lower, dtype=float), np.array(rt_upper, dtype=float), color="#fca5a5", alpha=0.35)
    axes[1].axhline(1.0, color="black", linestyle="--", linewidth=1)
    axes[1].set_ylabel("Rt")
    axes[1].set_xlabel("Day")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #

def generate_report(
    summary: dict[str, Any],
    data: dict[str, Any],
    pathogen: str,
    method: str,
    mean_si: float,
    std_si: float,
    output_dir: Path,

):
    lines = [
        generate_report_header(
            title="Rt Estimation Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Pathogen": pathogen, "Method": method, "Mean SI": str(mean_si), "SD SI": str(std_si), "Version": VERSION},
        ),
        "## Summary",
        "",
        f"- Days analysed: `{summary['days_analyzed']}`",
        f"- Final Rt: `{summary['final_rt']}`",
        f"- Peak Rt: `{summary['peak_rt']}` on day `{summary['peak_day']}`",
        f"- Days with Rt > 1: `{summary['days_rt_above_1']}`",
        "",
        "## Daily Estimates",
        "",
        "| Day | Date | Cases | Rt | Lower | Upper |",
        "|---|---|---|---|---|---|",
    ]
    for idx, (date, cases_value, rt_value, lo, hi) in enumerate(
        zip(data["dates"], data["cases"], data["rt"], data["rt_lower"], data["rt_upper"]),
        start=1,
    ):
        lines.append(f"| {idx} | {date} | {cases_value} | {rt_value} | {lo} | {hi} |")
    lines.append("")
    lines.append(generate_report_footer())
    return "\n".join(lines)
# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="EpiClaw Rt Estimator — real-time effective reproduction number"
    )
    parser.add_argument("--input", dest="input_path", help="Input CSV file (columns: date, cases)")
    parser.add_argument("--output", dest="output_dir", default="/tmp/epiclaw_rt_estimator", help="Output directory")
    parser.add_argument("--pathogen", default="Unknown Pathogen", help="Pathogen name")
    parser.add_argument("--method", choices=["cori", "wallingateunis"], default="cori",
                        help="Estimation method (default: cori)")
    parser.add_argument("--mean-si", type=float, default=5.0, help="Mean serial interval in days (default: 5.0)")
    parser.add_argument("--std-si", type=float, default=3.0, help="SD of serial interval in days (default: 3.0)")
    parser.add_argument("--window", type=int, default=7, help="Sliding window size in days (default: 7)")
    parser.add_argument("--prior-mean", type=float, default=5.0,
                        help="Prior mean for Rt Gamma prior (Cori method, default: 5.0)")
    parser.add_argument("--prior-sd", type=float, default=5.0,
                        help="Prior SD for Rt Gamma prior (Cori method, default: 5.0)")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo time series")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ #
    # Load data
    # ------------------------------------------------------------------ #
    if args.demo or not args.input_path:
        base_date = datetime(2025, 1, 1)
        dates = [(base_date + timedelta(days=idx)).strftime("%Y-%m-%d") for idx in range(21)]
        cases = [3, 4, 5, 7, 8, 10, 13, 16, 18, 20, 19, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5]
        pathogen = args.pathogen
        print(f"[info] Using built-in demo time series ({len(cases)} days).")
    elif args.input_path:
        print(f"[info] Loading case time series from: {args.input_path}")
        dates, cases = load_cases(args.input_path)
        pathogen = args.pathogen
    else:
        parser.error("Provide --input <file>.")

    print(f"[info] Loaded {len(cases)} days of case data; total cases = {sum(cases)}")

    # ------------------------------------------------------------------ #
    # Serial interval discretization
    # ------------------------------------------------------------------ #
    print(f"[info] Discretizing serial interval (mean={args.mean_si}d, SD={args.std_si}d)...")
    w = discretize_serial_interval(args.mean_si, args.std_si, max_days=30)

    # ------------------------------------------------------------------ #
    # Rt estimation
    # ------------------------------------------------------------------ #
    print(f"[info] Estimating Rₜ using method={args.method}, window={args.window}d...")
    if args.method == "cori":
        # Convert prior mean/SD to gamma shape/rate
        prior_a = (args.prior_mean / args.prior_sd) ** 2
        prior_b = args.prior_mean / (args.prior_sd ** 2)
        rt, rt_lower, rt_upper = estimate_rt_cori(
            cases, w, window=args.window, prior_a=prior_a, prior_b=prior_b
        )
    else:
        rt, rt_lower, rt_upper = estimate_rt_wallinga_teunis(
            cases, w, window=args.window
        )

    # ------------------------------------------------------------------ #
    # Summary statistics
    # ------------------------------------------------------------------ #
    valid_rt = [(i, v) for i, v in enumerate(rt) if not (isinstance(v, float) and v != v)]
    days_analyzed = len(valid_rt)
    days_above_1 = sum(1 for _, v in valid_rt if v > 1.0)

    if valid_rt:
        peak_idx, peak_val = max(valid_rt, key=lambda x: x[1])
        final_rt = valid_rt[-1][1]
    else:
        peak_idx, peak_val, final_rt = 0, 0.0, 0.0

    summary: dict[str, Any] = {
        "days_analyzed": days_analyzed,
        "method": args.method,
        "mean_si": args.mean_si,
        "final_rt": round(final_rt, 4),
        "days_rt_above_1": days_above_1,
        "peak_rt": round(float(peak_val), 4),
        "peak_day": int(peak_idx),
    }

    data: dict[str, Any] = {
        "dates": dates,
        "cases": cases,
        "rt": [round(v, 4) if not (isinstance(v, float) and v != v) else None for v in rt],
        "rt_lower": [round(v, 4) if not (isinstance(v, float) and v != v) else None for v in rt_lower],
        "rt_upper": [round(v, 4) if not (isinstance(v, float) and v != v) else None for v in rt_upper],
    }

    # ------------------------------------------------------------------ #
    # Figure
    # ------------------------------------------------------------------ #
    print("[info] Generating Rt curve figure...")
    try:
        fig_path = figures_dir / "rt_curve.png"
        generate_rt_figure(dates, cases, rt, rt_lower, rt_upper, pathogen, fig_path)
        print(f"[info] Figure saved: {fig_path}")
    except Exception as e:
        print(f"[warn] Figure generation failed: {e}")

    # ------------------------------------------------------------------ #
    # Report + JSON
    # ------------------------------------------------------------------ #
    print("[info] Writing report...")
    report_md = generate_report(summary, data, pathogen, args.method, args.mean_si, args.std_si, output_dir)
    report_path = output_dir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary=summary,
        data=data,
    )

    print(f"[info] Report: {report_path}")
    print(f"[info] Result JSON: {result_path}")
    print(f"[info] Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
