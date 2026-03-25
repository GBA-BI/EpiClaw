#!/usr/bin/env python3
"""EpiClaw Within-Host Modeler -- target-cell limited viral dynamics (TCL / TCL-immune)."""
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
SKILL_NAME = "within-host-modeler"

# Default TCL parameters (influenza-like, Perelson lab-derived)
_TCL_DEFAULTS = dict(
    T0=4e8,    # target cells at t=0
    I0_init=0.0,
    V0=100.0,  # initial viral load (copies/mL)
    beta=2.4e-8,  # infection rate
    delta=1.0,    # infected cell clearance rate (per day)
    p=1.6,        # virus production rate (per infected cell per day)
    c=13.0,       # virus clearance rate (per day)
)

# Additional immune parameters for TCL-immune
_IMMUNE_DEFAULTS = dict(
    E0=1.0,       # initial effector cells
    q=1e-4,       # effector expansion rate
    delta_E=0.5,  # effector death rate
    k=1e-3,       # effector-mediated virus killing rate
)


# ---------------------------------------------------------------------------
# ODE systems
# ---------------------------------------------------------------------------

def tcl_odes(
    y: list[float],
    _t: float,
    beta: float,
    delta: float,
    p: float,
    c: float,

):
    T, I, V = y
    dT = -beta * T * V
    dI = beta * T * V - delta * I
    dV = p * I - c * V
    return [dT, dI, dV]
def tcl_immune_odes(
    y: list[float],
    _t: float,
    beta: float,
    delta: float,
    p: float,
    c: float,
    q: float,
    delta_E: float,
    k: float,

):
    T, I, V, E = y
    dT = -beta * T * V
    dI = beta * T * V - delta * I
    dV = p * I - c * V - k * E * V
    dE = q * V - delta_E * E
    return [dT, dI, dV, dE]
# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_tcl(days: int, params: dict) -> dict:
    """Run standard TCL model."""
    T0 = params["T0"]
    I0_init = params["I0_init"]
    V0 = params["V0"]
    beta = params["beta"]
    delta = params["delta"]
    p = params["p"]
    c = params["c"]

    t = np.linspace(0, days, days * 100 + 1)  # fine time grid
    y0 = [T0, I0_init, V0]
    sol = odeint(tcl_odes, y0, t, args=(beta, delta, p, c), mxstep=10000)

    T_arr, I_arr, V_arr = sol[:, 0], sol[:, 1], sol[:, 2]
    T_arr = np.maximum(T_arr, 0.0)
    I_arr = np.maximum(I_arr, 0.0)
    V_arr = np.maximum(V_arr, 1e-30)

    return {"t": t, "T": T_arr, "I": I_arr, "V": V_arr, "E": None}


def run_tcl_immune(days: int, params: dict, immune_params: dict) -> dict:
    """Run TCL model with immune effectors."""
    T0 = params["T0"]
    I0_init = params["I0_init"]
    V0 = params["V0"]
    beta = params["beta"]
    delta = params["delta"]
    p = params["p"]
    c = params["c"]
    E0 = immune_params["E0"]
    q = immune_params["q"]
    delta_E = immune_params["delta_E"]
    k = immune_params["k"]

    t = np.linspace(0, days, days * 100 + 1)
    y0 = [T0, I0_init, V0, E0]
    sol = odeint(
        tcl_immune_odes, y0, t,
        args=(beta, delta, p, c, q, delta_E, k),
        mxstep=10000,
    )

    T_arr, I_arr, V_arr, E_arr = sol[:, 0], sol[:, 1], sol[:, 2], sol[:, 3]
    T_arr = np.maximum(T_arr, 0.0)
    I_arr = np.maximum(I_arr, 0.0)
    V_arr = np.maximum(V_arr, 1e-30)
    E_arr = np.maximum(E_arr, 0.0)

    return {"t": t, "T": T_arr, "I": I_arr, "V": V_arr, "E": E_arr}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_summary_metrics(results: dict, days: int) -> dict:
    """Compute viral dynamics summary metrics."""
    t = results["t"]
    V = results["V"]
    I = results["I"]  # noqa: E741

    V_log10 = np.log10(V)
    peak_idx_v = int(np.argmax(V_log10))
    peak_day_v = float(t[peak_idx_v])
    peak_vl_log10 = float(V_log10[peak_idx_v])

    # Clearance day: first day V drops below 1 copy/mL after peak
    clearance_day = days  # default: not cleared
    for idx in range(peak_idx_v, len(t)):
        if V[idx] < 1.0:
            clearance_day = int(t[idx])
            break

    # Total infected cells (trapezoidal integration)
    total_infected = float(np.trapz(I, t))

    return {
        "peak_viral_load_log10": round(peak_vl_log10, 3),
        "peak_day": round(peak_day_v, 2),
        "clearance_day": clearance_day,
        "total_infected_cells": round(total_infected, 2),
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_viral_dynamics(results: dict, output_dir: Path, model: str, days: int) -> Path:
    """Plot log10 viral load + infected cells over time."""
    t = results["t"]
    V = results["V"]
    I = results["I"]  # noqa: E741
    E = results["E"]

    V_log10 = np.log10(np.maximum(V, 1e-30))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Panel 1: Viral load
    ax1.plot(t, V_log10, color="crimson", linewidth=2, label="Viral load (log10)")
    ax1.set_ylabel("Viral load (log10 copies/mL)")
    ax1.set_title(f"Within-Host Viral Dynamics — {model.upper()} model")
    ax1.legend(loc="upper right")
    ax1.axhline(y=0, color="gray", linestyle=":", linewidth=0.8)

    # Panel 2: Infected cells (and effectors if immune model)
    ax2.plot(t, I, color="darkorange", linewidth=2, label="Infected cells")
    if E is not None:
        ax2_twin = ax2.twinx()
        ax2_twin.plot(t, E, color="purple", linewidth=1.5, linestyle="--", label="Effectors")
        ax2_twin.set_ylabel("Effector cells", color="purple")
        ax2_twin.tick_params(axis="y", labelcolor="purple")
        ax2_twin.legend(loc="upper right")
    ax2.set_xlabel("Day")
    ax2.set_ylabel("Infected cells")
    ax2.legend(loc="upper left")

    plt.tight_layout()

    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / "viral_dynamics.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    return fig_path


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(output_dir: Path, summary: dict, model: str, days: int) -> Path:
    header = generate_report_header(
        title="Within-Host Viral Dynamics Report",
        skill_name=SKILL_NAME,
        extra_metadata={
            "Model": model.upper(),
            "Simulation days": str(days),
            "Version": VERSION,
        },
    )
    body = f"""## Summary

| Metric | Value |
|--------|-------|
| Model | {summary['model'].upper()} |
| Days simulated | {summary['days']} |
| Peak viral load | {summary['peak_viral_load_log10']:.2f} log10 copies/mL |
| Peak day | Day {summary['peak_day']:.1f} |
| Clearance day | Day {summary['clearance_day']} |
| Total infected cells | {summary['total_infected_cells']:,.0f} |

## Figure

![Viral dynamics](figures/viral_dynamics.png)

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
        prog="within_host_modeler",
        description="EpiClaw Within-Host Modeler: target-cell limited viral dynamics.",
    )
    p.add_argument("--output", type=Path, default=Path("output/within-host-modeler"))
    p.add_argument("--model", choices=["tcl", "tcl-immune"], default="tcl")
    p.add_argument("--days", type=int, default=21)
    p.add_argument("--demo", action="store_true", help="Run demo mode")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    params = dict(_TCL_DEFAULTS)
    immune_params = dict(_IMMUNE_DEFAULTS)

    print(f"[info] Within-host model: {args.model.upper()} | days={args.days}")
    print(f"[info] Parameters: T0={params['T0']:.2e} | V0={params['V0']} | "
          f"beta={params['beta']:.2e} | delta={params['delta']} | "
          f"p={params['p']} | c={params['c']}")

    print("[info] Running ODE simulation...")
    if args.model == "tcl-immune":
        results = run_tcl_immune(args.days, params, immune_params)
    else:
        results = run_tcl(args.days, params)

    metrics = compute_summary_metrics(results, args.days)

    summary = {
        "model": args.model,
        "days": args.days,
        **metrics,
    }

    # Downsample to daily for JSON output
    t_fine = results["t"]
    V_fine = results["V"]
    I_fine = results["I"]  # noqa: E741
    day_indices = np.searchsorted(t_fine, np.arange(args.days + 1))
    day_indices = np.clip(day_indices, 0, len(t_fine) - 1)
    t_daily = t_fine[day_indices].tolist()
    T_daily = results["T"][day_indices].tolist()
    I_daily = I_fine[day_indices].tolist()
    V_log10_daily = np.log10(np.maximum(V_fine[day_indices], 1e-30)).tolist()

    data = {
        "t": t_daily,
        "T": T_daily,
        "I": I_daily,
        "V_log10": V_log10_daily,
    }

    print("[info] Generating viral dynamics figure...")
    plot_viral_dynamics(results, output_dir, args.model, args.days)

    print("[info] Writing report and result JSON...")
    write_report(output_dir, summary, args.model, args.days)
    write_result_json(output_dir, SKILL_NAME, VERSION, summary, data)

    print(f"[info] Done. Output written to: {output_dir.resolve()}")
    print(f"[info] Peak viral load: {metrics['peak_viral_load_log10']:.2f} log10 on day "
          f"{metrics['peak_day']:.1f} | Clearance day: {metrics['clearance_day']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
