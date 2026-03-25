#!/usr/bin/env python3
"""EpiClaw Age-Structured Modeler -- age-structured SEIR with POLYMOD-style contact matrix."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import odeint

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "age-structured-modeler"

# Age-specific case-fatality ratios (reference values for 5 groups)
_CFR_5 = [0.001, 0.005, 0.02, 0.08, 0.15]


# ---------------------------------------------------------------------------
# Contact matrix
# ---------------------------------------------------------------------------

def build_contact_matrix(n: int) -> np.ndarray:
    """Build synthetic POLYMOD-style contact matrix (n x n).

    Diagonal = 8 (within-age-group mixing),
    off-diagonal[i,j] = 2 / |i - j|.
    Matrix is symmetrized and left un-normalised (contacts are absolute).
    """
    C = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                C[i, j] = 8.0
            else:
                C[i, j] = 2.0 / abs(i - j)
    # Symmetrize
    C = 0.5 * (C + C.T)
    return C


def get_age_cfr(n: int) -> np.ndarray:
    """Interpolate CFR for n age groups from the 5-group reference."""
    if n == 5:
        return np.array(_CFR_5)
    x_ref = np.linspace(0, 1, 5)
    x_new = np.linspace(0, 1, n)
    return np.interp(x_new, x_ref, _CFR_5)


# ---------------------------------------------------------------------------
# Age-structured SEIR ODE
# ---------------------------------------------------------------------------

def age_seir_odes(
    y: np.ndarray,
    _t: float,
    n: int,
    N_groups: np.ndarray,
    beta: float,
    gamma: float,
    sigma: float,
    C: np.ndarray,

):
    S = y[0:n]
    E = y[n:2 * n]
    I = y[2 * n:3 * n]
    R = y[3 * n:4 * n]
    lambda_vec = beta * (C @ (I / np.maximum(N_groups, 1)))
    dS = -lambda_vec * S
    dE = lambda_vec * S - sigma * E
    dI = sigma * E - gamma * I
    dR = gamma * I
    return np.concatenate([dS, dE, dI, dR])
def run_age_seir(
    n: int,
    r0: float,
    gamma: float,
    sigma: float,
    days: int,
    total_N: int = 100_000,

):
    weights = np.linspace(1.4, 0.6, n)
    weights /= weights.sum()
    N_groups = total_N * weights
    C = build_contact_matrix(n)
    beta = r0 * gamma / max(np.mean(C), 1.0)
    I0 = np.zeros(n)
    I0[0] = 10
    E0 = np.zeros(n)
    E0[0] = 5
    R0_init = np.zeros(n)
    S0 = N_groups - E0 - I0
    y0 = np.concatenate([S0, E0, I0, R0_init])
    t = np.arange(days + 1)
    sol = odeint(age_seir_odes, y0, t, args=(n, N_groups, beta, gamma, sigma, C))
    S = sol[:, 0:n]
    R = sol[:, 3 * n:4 * n]
    attack_rates = (N_groups - S[-1]) / N_groups
    return {"t": t, "sol": sol, "N_groups": N_groups, "C": C, "attack_rates": attack_rates, "total_cases": float(np.sum(N_groups - S[-1])), "R": R}
# ---------------------------------------------------------------------------
# Elderly vaccination scenario
# ---------------------------------------------------------------------------

def compute_deaths_averted_elderly_vax(
    results: dict,
    cfr: np.ndarray,
    n: int,
    vax_coverage: float = 0.8,

):
    infections = results["N_groups"] * results["attack_rates"]
    baseline_deaths = infections * cfr
    vaccinated_deaths = baseline_deaths.copy()
    vaccinated_deaths[-1] *= max(0.0, 1 - vax_coverage)
    return round(float(np.sum(baseline_deaths - vaccinated_deaths)), 2)
# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_age_attack_rates(
    attack_rates: np.ndarray,
    n: int,
    output_dir: Path,
    r0: float,

):
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(np.arange(1, n + 1), attack_rates * 100, color="#0ea5e9")
    ax.set_xlabel("Age group")
    ax.set_ylabel("Attack rate (%)")
    ax.set_title(f"Age-specific attack rates (R0={r0})")
    fig.tight_layout()
    fig.savefig(fig_dir / "age_attack_rates.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(output_dir: Path, summary: dict, n: int, r0: float) -> Path:
    header = generate_report_header(
        title="Age-Structured SEIR Model Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Age groups": str(n), "R0": str(r0), "Version": VERSION},
    )
    ar_rows = ""
    for i, ar in enumerate(summary.get("_attack_rates_raw", [])):
        ar_rows += f"| Age group {i + 1} | {ar * 100:.2f}% |\n"

    body = f"""## Summary

| Metric | Value |
|--------|-------|
| Age groups | {summary['age_groups']} |
| R0 | {summary['r0']} |
| Total cases | {summary['total_cases']:,.0f} |
| Deaths averted (80% elderly vax) | {summary['deaths_averted_if_elderly_vaccinated']:,.2f} |

## Attack Rates by Age Group

| Age Group | Attack Rate |
|-----------|-------------|
{ar_rows}
## Figure

![Age-group attack rates](figures/age_attack_rates.png)

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
        prog="age_structured_modeler",
        description="EpiClaw Age-Structured Modeler: SEIR with contact matrix and age-specific CFR.",
    )
    p.add_argument("--output", type=Path, default=Path("output/age-structured-modeler"))
    p.add_argument("--r0", type=float, default=2.5)
    p.add_argument("--gamma", type=float, default=0.1)
    p.add_argument("--sigma", type=float, default=0.2)
    p.add_argument("--days", type=int, default=180)
    p.add_argument("--age-groups", type=int, default=5, dest="age_groups")
    p.add_argument("--demo", action="store_true", help="Run demo mode")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    n = args.age_groups
    print(f"[info] Age-structured SEIR | R0={args.r0} | {n} age groups | {args.days} days")
    print("[info] Building POLYMOD-style contact matrix...")
    print("[info] Running ODE simulation...")

    results = run_age_seir(
        n=n,
        r0=args.r0,
        gamma=args.gamma,
        sigma=args.sigma,
        days=args.days,
    )

    cfr = get_age_cfr(n)
    deaths_averted = compute_deaths_averted_elderly_vax(results, cfr, n)

    attack_rates = results["attack_rates"]
    age_cases = (results["N_groups"] * attack_rates).tolist()

    summary = {
        "age_groups": n,
        "r0": args.r0,
        "total_cases": round(results["total_cases"], 1),
        "deaths_averted_if_elderly_vaccinated": deaths_averted,
        "_attack_rates_raw": attack_rates.tolist(),  # internal for report; not in public summary
    }

    # Public summary (without internal key)
    public_summary = {k: v for k, v in summary.items() if not k.startswith("_")}

    data = {
        "age_group_attack_rates": attack_rates.tolist(),
        "age_group_cases": age_cases,
        "contact_matrix": results["C"].tolist(),
    }

    print("[info] Generating age attack rates figure...")
    plot_age_attack_rates(attack_rates, n, output_dir, args.r0)

    print("[info] Writing report and result JSON...")
    write_report(output_dir, summary, n, args.r0)
    write_result_json(output_dir, SKILL_NAME, VERSION, public_summary, data)

    print(f"[info] Done. Output written to: {output_dir.resolve()}")
    print(f"[info] Total cases: {results['total_cases']:,.0f} | Deaths averted (80% elderly vax): {deaths_averted:,.2f}")
    for i, ar in enumerate(attack_rates):
        print(f"[info]   Age group {i + 1}: attack rate {ar * 100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
