#!/usr/bin/env python3
"""EpiClaw Stochastic Modeler -- tau-leaping stochastic SIR/SEIR epidemic simulation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "stochastic-modeler"


# ---------------------------------------------------------------------------
# Tau-leaping SIR
# ---------------------------------------------------------------------------

def run_sir_tauleap(
    N: int,
    beta: float,
    gamma: float,
    days: int,
    tau: float = 0.1,
    rng: np.random.Generator | None = None,

):
    rng = rng or np.random.default_rng()
    steps = int(days / tau) + 1
    S, I, R = N - 10, 10, 0
    I_daily = np.zeros(days + 1)
    for step in range(steps):
        day = min(int(step * tau), days)
        if I > 0 and S > 0:
            inf_rate = beta * S * I / N
            rec_rate = gamma * I
            new_inf = min(S, rng.poisson(max(inf_rate * tau, 0)))
            new_rec = min(I, rng.poisson(max(rec_rate * tau, 0)))
            S -= new_inf
            I += new_inf - new_rec
            R += new_rec
        I_daily[day] = I
    return I_daily
# ---------------------------------------------------------------------------
# Tau-leaping SEIR
# ---------------------------------------------------------------------------

def run_seir_tauleap(
    N: int,
    beta: float,
    gamma: float,
    sigma: float,
    days: int,
    tau: float = 0.1,
    rng: np.random.Generator | None = None,

):
    rng = rng or np.random.default_rng()
    steps = int(days / tau) + 1
    S, E, I, R = N - 15, 5, 10, 0
    I_daily = np.zeros(days + 1)
    for step in range(steps):
        day = min(int(step * tau), days)
        inf_rate = beta * S * I / N
        prog_rate = sigma * E
        rec_rate = gamma * I
        new_inf = min(S, rng.poisson(max(inf_rate * tau, 0)))
        new_prog = min(E, rng.poisson(max(prog_rate * tau, 0)))
        new_rec = min(I, rng.poisson(max(rec_rate * tau, 0)))
        S -= new_inf
        E += new_inf - new_prog
        I += new_prog - new_rec
        R += new_rec
        I_daily[day] = I
    return I_daily
# ---------------------------------------------------------------------------
# Ensemble runner
# ---------------------------------------------------------------------------

def run_ensemble(
    model: str,
    r0: float,
    gamma: float,
    sigma: float,
    N: int,
    days: int,
    runs: int,
    k: float,
    seed: int = 0,

):
    beta = r0 * gamma
    rng = np.random.default_rng(seed)
    trajectories = []
    totals = []
    for _ in range(runs):
        sub_rng = np.random.default_rng(int(rng.integers(0, 1_000_000)))
        if model == "seir":
            traj = run_seir_tauleap(N, beta, gamma, sigma, days, rng=sub_rng)
        else:
            traj = run_sir_tauleap(N, beta, gamma, days, rng=sub_rng)
        trajectories.append(traj)
        totals.append(float(np.sum(traj)))
    I_matrix = np.vstack(trajectories)
    median = np.median(I_matrix, axis=0)
    p5 = np.percentile(I_matrix, 5, axis=0)
    p95 = np.percentile(I_matrix, 95, axis=0)
    extinction_probability = float(np.mean(np.max(I_matrix, axis=1) < 20))
    return {
        "I_matrix": I_matrix,
        "median_trajectory": median,
        "p5_trajectory": p5,
        "p95_trajectory": p95,
        "ensemble_total_cases": totals,
        "median_total_cases": float(np.median(totals)),
        "extinction_probability": extinction_probability,
        "median_peak_day": int(np.argmax(median)),
    }
# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_ensemble(
    I_matrix: np.ndarray,
    median_traj: np.ndarray,
    p5_traj: np.ndarray,
    p95_traj: np.ndarray,
    output_dir: Path,
    model: str,
    r0: float,
    N: int,

):
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    sample = I_matrix[: min(20, len(I_matrix))]
    for row in sample:
        ax.plot(row, color="#93c5fd", alpha=0.3)
    ax.plot(median_traj, color="#1d4ed8", linewidth=2, label="Median")
    ax.fill_between(np.arange(len(median_traj)), p5_traj, p95_traj, color="#bfdbfe", alpha=0.6, label="5–95%")
    ax.set_title(f"{model.upper()} stochastic ensemble (R0={r0}, N={N})")
    ax.set_xlabel("Day")
    ax.set_ylabel("Infected")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "ensemble.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(output_dir: Path, summary: dict, model: str, r0: float, runs: int) -> Path:
    header = generate_report_header(
        title="Stochastic Epidemic Model Report",
        skill_name=SKILL_NAME,
        extra_metadata={
            "Model": model.upper(),
            "R0": str(r0),
            "Ensemble runs": str(runs),
            "Version": VERSION,
        },
    )
    body = f"""## Summary

| Metric | Value |
|--------|-------|
| Model | {summary['model'].upper()} |
| R0 | {summary['r0']} |
| Ensemble runs | {summary['runs']} |
| Median total cases | {summary['median_total_cases']:,.1f} |
| Extinction probability | {summary['extinction_probability']:.1%} |
| Median peak day | Day {summary['median_peak_day']} |

## Figure

![Ensemble trajectories](figures/ensemble.png)

"""
    footer = generate_report_footer()
    report_path = output_dir / "report.md"
    report_path.write_text(header + body + footer)
    return report_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stochastic_modeler",
        description="EpiClaw Stochastic Modeler: tau-leaping SIR/SEIR ensemble simulation.",
    )
    p.add_argument("--output", type=Path, default=Path("output/stochastic-modeler"))
    p.add_argument("--model", choices=["sir", "seir"], default="sir")
    p.add_argument("--r0", type=float, default=2.5)
    p.add_argument("--gamma", type=float, default=0.1)
    p.add_argument("--sigma", type=float, default=0.2)
    p.add_argument("--population", type=int, default=10000)
    p.add_argument("--days", type=int, default=180)
    p.add_argument("--runs", type=int, default=100)
    p.add_argument("--k", type=float, default=0.5, help="Negative-binomial dispersion parameter.")
    p.add_argument("--demo", action="store_true", help="Run demo mode")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.demo:
        print("[info] No --input required for stochastic modeler; using provided parameters.")

    print(f"[info] Model: {args.model.upper()} | R0={args.r0} | N={args.population:,} | "
          f"runs={args.runs} | days={args.days}")
    print("[info] Running stochastic ensemble (tau-leaping)...")

    results = run_ensemble(
        model=args.model,
        r0=args.r0,
        gamma=args.gamma,
        sigma=args.sigma,
        N=args.population,
        days=args.days,
        runs=args.runs,
        k=args.k,
    )

    summary = {
        "model": args.model,
        "r0": args.r0,
        "runs": args.runs,
        "median_total_cases": results["median_total_cases"],
        "extinction_probability": results["extinction_probability"],
        "median_peak_day": results["median_peak_day"],
    }

    data = {
        "ensemble_total_cases": results["ensemble_total_cases"],
        "median_trajectory": results["median_trajectory"].tolist(),
        "p5_trajectory": results["p5_trajectory"].tolist(),
        "p95_trajectory": results["p95_trajectory"].tolist(),
    }

    print("[info] Generating ensemble figure...")
    plot_ensemble(
        results["I_matrix"],
        results["median_trajectory"],
        results["p5_trajectory"],
        results["p95_trajectory"],
        output_dir,
        args.model,
        args.r0,
        args.population,
    )

    print("[info] Writing report and result JSON...")
    write_report(output_dir, summary, args.model, args.r0, args.runs)
    write_result_json(output_dir, SKILL_NAME, VERSION, summary, data)

    print(f"[info] Done. Output written to: {output_dir.resolve()}")
    print(f"[info] Median total cases: {results['median_total_cases']:,.1f} | "
          f"Extinction prob: {results['extinction_probability']:.1%} | "
          f"Median peak day: {results['median_peak_day']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
