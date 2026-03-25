#!/usr/bin/env python3
"""EpiClaw Disease Modeler -- compartmental ODE epidemic simulation.

Implements SIR, SEIR, and SEIRS models with parameter estimation,
WHO data retrieval, and standardized reporting.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import odeint
from scipy.optimize import minimize

from reporting import (
        generate_report_footer,
        generate_report_header,
        write_result_json,
    )

VERSION = "0.1.0"
SKILL_NAME = "disease-modeler"


# ---------------------------------------------------------------------------
# ODE systems
# ---------------------------------------------------------------------------

def sir_odes(y: list[float], _t: float, N: float, beta: float, gamma: float) -> list[float]:
    """SIR model differential equations."""
    S, I, R = y
    dSdt = -beta * S * I / N
    dIdt = beta * S * I / N - gamma * I
    dRdt = gamma * I
    return [dSdt, dIdt, dRdt]


def seir_odes(
    y: list[float], _t: float, N: float, beta: float, gamma: float, sigma: float,

):
    S, E, I, R = y
    force = beta * S * I / N
    dSdt = -force
    dEdt = force - sigma * E
    dIdt = sigma * E - gamma * I
    dRdt = gamma * I
    return [dSdt, dEdt, dIdt, dRdt]
def seirs_odes(
    y: list[float],
    _t: float,
    N: float,
    beta: float,
    gamma: float,
    sigma: float,
    xi: float,

):
    S, E, I, R = y
    force = beta * S * I / N
    dSdt = -force + xi * R
    dEdt = force - sigma * E
    dIdt = sigma * E - gamma * I
    dRdt = gamma * I - xi * R
    return [dSdt, dEdt, dIdt, dRdt]
# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_sir(
    N: float, beta: float, gamma: float, I0: float, days: int,

):
    R0_init = 0.0
    S0 = N - I0 - R0_init
    t = np.arange(days + 1)
    sol = odeint(sir_odes, [S0, I0, R0_init], t, args=(N, beta, gamma))
    return {"t": t, "S": sol[:, 0], "I": sol[:, 1], "R": sol[:, 2]}
def run_seir(
    N: float, beta: float, gamma: float, sigma: float, I0: float, days: int,

):
    E0 = max(I0 * 0.5, 1.0)
    R0_init = 0.0
    S0 = N - E0 - I0 - R0_init
    t = np.arange(days + 1)
    sol = odeint(seir_odes, [S0, E0, I0, R0_init], t, args=(N, beta, gamma, sigma))
    return {"t": t, "S": sol[:, 0], "E": sol[:, 1], "I": sol[:, 2], "R": sol[:, 3]}
def run_seirs(
    N: float,
    beta: float,
    gamma: float,
    sigma: float,
    xi: float,
    I0: float,
    days: int,

):
    E0 = max(I0 * 0.5, 1.0)
    R0_init = 0.0
    S0 = N - E0 - I0 - R0_init
    t = np.arange(days + 1)
    sol = odeint(seirs_odes, [S0, E0, I0, R0_init], t, args=(N, beta, gamma, sigma, xi))
    return {"t": t, "S": sol[:, 0], "E": sol[:, 1], "I": sol[:, 2], "R": sol[:, 3]}
# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_new_cases(sim: dict[str, np.ndarray]) -> np.ndarray:
    """Derive daily new cases from the change in susceptibles."""
    dS = -np.diff(sim["S"])
    return np.maximum(dS, 0)


def compute_metrics(
    sim: dict[str, np.ndarray], N: float, r0: float,

):
    new_cases = compute_new_cases(sim)
    infected = sim["I"]
    peak_idx = int(np.argmax(infected))
    final_size = float((N - sim["S"][-1]) / N)
    return {
        "peak_infected": round(float(infected[peak_idx]), 2),
        "peak_day": int(sim["t"][peak_idx]),
        "attack_rate": round(final_size, 4),
        "final_recovered": round(float(sim["R"][-1]), 2),
        "R0": round(float(r0), 4),
        "Rt": [round(float(r0 * (s / N)), 4) for s in sim["S"]],
        "total_new_cases": round(float(np.sum(new_cases)), 2),
    }
# ---------------------------------------------------------------------------
# Parameter estimation
# ---------------------------------------------------------------------------

def fit_sir_to_data(
    dates: np.ndarray,
    cases: np.ndarray,
    N: float,

):
    days = len(cases) - 1
    I0 = max(float(cases[0]), 1.0)

    def objective(theta: np.ndarray) -> float:
        beta, gamma = theta
        if beta < 0 or gamma <= 0:
            return 1e12
        sim = run_sir(N, float(beta), float(gamma), I0, days)
        pred = compute_new_cases(sim)[: len(cases)]
        return float(np.sum((pred - cases[: len(pred)]) ** 2))

    result = minimize(objective, x0=np.array([0.25, 0.1]), method="Nelder-Mead")
    beta, gamma = result.x
    return {
        "beta": round(float(beta), 6),
        "gamma": round(float(gamma), 6),
        "R0": round(float(beta / gamma), 6) if gamma > 0 else None,
        "rss": round(float(result.fun), 4),
        "success": bool(result.success),
    }
# ---------------------------------------------------------------------------
# WHO data retrieval
# ---------------------------------------------------------------------------

def fetch_who_data(pathogen: str, country: str) -> list[dict[str, Any]] | None:
    """Attempt to retrieve case data via epiclaw WHO connector.

    Returns None if the connector is unavailable or the query fails.
    """
    try:
        from who_gho_connector import WHOClient

        client = WHOClient()
        indicators = client.search_indicators(pathogen, max_results=5)
        if not indicators:
            print(f"[info] No WHO indicators found for '{pathogen}'.")
            return None
        code = indicators[0]["code"]
        data = client.get_country_data(code, country)
        if not data:
            print(f"[info] No WHO data for indicator {code} in {country}.")
            return None
        return data
    except Exception as exc:  # noqa: BLE001
        print(f"[info] WHO connector unavailable ({exc}); proceeding without WHO data.")
        return None


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_compartments(
    sim: dict[str, np.ndarray],
    model_name: str,
    output_path: Path,

):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(sim["t"], sim["S"], label="S")
    if "E" in sim:
        ax.plot(sim["t"], sim["E"], label="E")
    ax.plot(sim["t"], sim["I"], label="I")
    ax.plot(sim["t"], sim["R"], label="R")
    ax.set_title(f"{model_name.upper()} compartments")
    ax.set_xlabel("Day")
    ax.set_ylabel("Population")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
def plot_epi_curve(
    sim: dict[str, np.ndarray],
    model_name: str,
    output_path: Path,

):
    new_cases = compute_new_cases(sim)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(np.arange(len(new_cases)), new_cases, color="#2563eb")
    ax.set_title(f"{model_name.upper()} epidemic curve")
    ax.set_xlabel("Day")
    ax.set_ylabel("New cases")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    model_name: str,
    params: dict[str, Any],
    metrics: dict[str, Any],
    fit_results: dict[str, Any] | None,
    figures_dir: Path,
    output_path: Path,

):
    lines = [
        generate_report_header(
            title="Disease Modeler Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Version": VERSION, **{k: str(v) for k, v in params.items()}},
        ),
        "## Summary",
        "",
        f"- Peak infected: `{metrics['peak_infected']}` on day `{metrics['peak_day']}`",
        f"- Attack rate: `{metrics['attack_rate']}`",
        f"- Final recovered: `{metrics['final_recovered']}`",
        f"- Total new cases: `{metrics['total_new_cases']}`",
        "",
    ]
    if fit_results:
        lines.extend(
            [
                "## Parameter Fit",
                "",
                f"- Fitted beta: `{fit_results['beta']}`",
                f"- Fitted gamma: `{fit_results['gamma']}`",
                f"- RSS: `{fit_results['rss']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Figures",
            "",
            f"- Compartments: `{figures_dir / 'compartments.png'}`",
            f"- Epidemic curve: `{figures_dir / 'epi_curve.png'}`",
            "",
            generate_report_footer(),
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="disease_modeler",
        description="EpiClaw Disease Modeler -- compartmental ODE epidemic simulation.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input CSV with columns: date, cases",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for report, results, and figures",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo mode (SIR, R0=2.5, gamma=1/10, N=100000, 180 days)",
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["sir", "seir", "seirs"],
        default="sir",
        help="Compartmental model type (default: sir)",
    )
    parser.add_argument("--r0", type=float, default=None, help="Basic reproduction number")
    parser.add_argument("--beta", type=float, default=None, help="Transmission rate")
    parser.add_argument("--gamma", type=float, default=None, help="Recovery rate (1/infectious period)")
    parser.add_argument("--sigma", type=float, default=None, help="Incubation rate (1/latent period)")
    parser.add_argument("--population", type=float, default=100000, help="Total population size")
    parser.add_argument("--initial-infected", type=float, default=10, help="Initial number of infected")
    parser.add_argument("--days", type=int, default=180, help="Simulation duration in days")
    parser.add_argument("--pathogen", type=str, default=None, help="Pathogen name for WHO data retrieval")
    parser.add_argument("--country", type=str, default=None, help="ISO3 country code for WHO data retrieval")
    return parser


def resolve_parameters(args: argparse.Namespace) -> dict[str, float]:
    """Resolve beta/gamma from R0 or direct specification."""
    gamma = args.gamma if args.gamma is not None else 1.0 / 10.0
    beta = args.beta
    r0 = args.r0

    if beta is not None and r0 is not None:
        # Both specified; beta takes precedence, recompute R0
        r0 = beta / gamma
    elif r0 is not None and beta is None:
        beta = r0 * gamma
    elif beta is not None and r0 is None:
        r0 = beta / gamma
    else:
        # Neither specified; default R0=2.5
        r0 = 2.5
        beta = r0 * gamma

    sigma = args.sigma if args.sigma is not None else 1.0 / 5.0
    xi = 0.0  # Default: no waning; user can extend later

    return {
        "beta": beta,
        "gamma": gamma,
        "r0": r0,
        "sigma": sigma,
        "xi": xi,
        "N": args.population,
        "I0": args.initial_infected,
        "days": args.days,
    }


def validate_parameters(params: dict[str, float]) -> None:
    """Validate model parameters and raise ValueError for invalid inputs."""
    if params["N"] <= 0:
        raise ValueError("population must be > 0")
    if params["days"] <= 0:
        raise ValueError("days must be > 0")
    if params["I0"] < 0:
        raise ValueError("initial-infected must be >= 0")
    if params["I0"] > params["N"]:
        raise ValueError("initial-infected must be <= population")
    if params["gamma"] <= 0:
        raise ValueError("gamma must be > 0")
    if params["beta"] < 0:
        raise ValueError("beta must be >= 0")
    if params["sigma"] <= 0:
        raise ValueError("sigma must be > 0")
    if params["r0"] < 0:
        raise ValueError("r0 must be >= 0")


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # WHO data retrieval (optional)
    who_data = None
    if args.pathogen and args.country:
        who_data = fetch_who_data(args.pathogen, args.country)
        if who_data:
            print(f"[info] Retrieved {len(who_data)} WHO data points.")

    # Parameter resolution
    params = resolve_parameters(args)
    try:
        validate_parameters(params)
    except ValueError as exc:
        print(f"[error] Invalid model parameters: {exc}")
        sys.exit(1)
    model_name =args.model

    # Input data for parameter fitting
    fit_results = None
    if args.input:
        import csv
        from datetime import datetime as _dt

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[error] Input file not found: {input_path}")
            sys.exit(1)

        dates = []
        cases = []
        with open(input_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dates.append(row["date"])
                cases.append(float(row["cases"]))
        cases_arr = np.array(cases)

        print(f"[info] Fitting {model_name.upper()} to {len(cases)} data points ...")
        fit_results = fit_sir_to_data(np.array(dates), cases_arr, params["N"])
        print(f"[info] Fitted R0={fit_results['R0']}, beta={fit_results['beta']}, "
              f"gamma={fit_results['gamma']}, RSS={fit_results['rss']}")

        # Use fitted parameters for simulation
        params["beta"] = fit_results["beta"]
        params["gamma"] = fit_results["gamma"]
        params["r0"] = fit_results["R0"]

    # Run simulation
    if model_name == "sir":
        sim = run_sir(params["N"], params["beta"], params["gamma"], params["I0"], params["days"])
    elif model_name == "seir":
        sim = run_seir(
            params["N"], params["beta"], params["gamma"], params["sigma"],
            params["I0"], params["days"],
        )
    elif model_name == "seirs":
        sim = run_seirs(
            params["N"], params["beta"], params["gamma"], params["sigma"],
            params["xi"], params["I0"], params["days"],
        )
    else:
        print(f"[error] Unknown model: {model_name}")
        sys.exit(1)

    # Compute metrics
    metrics = compute_metrics(sim, params["N"], params["r0"])

    # Plot
    plot_compartments(sim, model_name, figures_dir / "compartments.png")
    plot_epi_curve(sim, model_name, figures_dir / "epi_curve.png")
    print(f"[info] Figures saved to {figures_dir}/")

    # Report
    report_params = {
        "Model": model_name.upper(),
        "R0": params["r0"],
        "beta": round(params["beta"], 6),
        "gamma": round(params["gamma"], 6),
        "Population (N)": int(params["N"]),
        "Initial infected": int(params["I0"]),
        "Days": params["days"],
    }
    if model_name in ("seir", "seirs"):
        report_params["sigma"] = round(params["sigma"], 6)
    if model_name == "seirs":
        report_params["xi"] = round(params["xi"], 6)

    report_path = output_dir / "report.md"
    generate_report(model_name, report_params, metrics, fit_results, figures_dir, report_path)
    print(f"[info] Report written to {report_path}")

    # result.json
    metrics_json = {k: v for k, v in metrics.items() if k != "Rt"}
    input_checksum = ""
    if args.input:
        from checksums import sha256_file

        input_checksum = sha256_file(args.input)

    write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary=metrics_json,
        data={
            "parameters": {k: v for k, v in params.items() if k != "days"},
            "model": model_name,
            "days": params["days"],
            "fit": fit_results,
            "who_data_points": len(who_data) if who_data else 0,
        },
        input_checksum=input_checksum,
    )
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
