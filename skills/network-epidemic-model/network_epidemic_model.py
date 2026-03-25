#!/usr/bin/env python3
"""EpiClaw Network Epidemic Model -- discrete-time SIR/SIS on contact networks."""
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
SKILL_NAME = "network-epidemic-model"

# Try to import networkx; use numpy fallback if unavailable
try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:  # pragma: no cover
    _HAS_NETWORKX = False
    nx = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Network generation
# ---------------------------------------------------------------------------

def build_network_numpy(
    network_type: str, nodes: int, rng: np.random.Generator

):
    adj = [[] for _ in range(nodes)]
    if network_type == "erdos":
        p = min(6 / max(nodes - 1, 1), 0.05)
        for i in range(nodes):
            for j in range(i + 1, nodes):
                if rng.random() < p:
                    adj[i].append(j)
                    adj[j].append(i)
    elif network_type == "barabasi":
        degrees = [0] * nodes
        for new_node in range(2, nodes):
            targets = sorted(set(rng.choice(np.arange(new_node), size=min(2, new_node), replace=False)))
            for target in targets:
                adj[new_node].append(int(target))
                adj[int(target)].append(new_node)
                degrees[new_node] += 1
                degrees[int(target)] += 1
    else:
        k = 4
        for i in range(nodes):
            for offset in range(1, k // 2 + 1):
                j = (i + offset) % nodes
                adj[i].append(j)
                adj[j].append(i)
    return adj
def build_network_nx(
    network_type: str, nodes: int, seed: int

):
    if network_type == "erdos":
        G = nx.erdos_renyi_graph(nodes, min(6 / max(nodes - 1, 1), 0.05), seed=seed)
    elif network_type == "barabasi":
        G = nx.barabasi_albert_graph(nodes, 2, seed=seed)
    else:
        G = nx.watts_strogatz_graph(nodes, 4, 0.15, seed=seed)
    return [list(G.neighbors(node)) for node in range(nodes)]
# ---------------------------------------------------------------------------
# Discrete-time SIR on network
# ---------------------------------------------------------------------------

STATE_S, STATE_I, STATE_R = 0, 1, 2


def run_network_sir(
    adj: list[list[int]],
    n: int,
    beta: float,
    gamma: float,
    days: int,
    rng: np.random.Generator,

):
    states = np.full(n, STATE_S, dtype=int)
    patient_zero = int(rng.integers(0, n))
    states[patient_zero] = STATE_I
    S, I, R = np.zeros(days + 1), np.zeros(days + 1), np.zeros(days + 1)
    for day in range(days + 1):
        S[day] = np.sum(states == STATE_S)
        I[day] = np.sum(states == STATE_I)
        R[day] = np.sum(states == STATE_R)
        new_states = states.copy()
        for node in range(n):
            if states[node] == STATE_I:
                for nb in adj[node]:
                    if states[nb] == STATE_S and rng.random() < beta / max(len(adj[node]), 1):
                        new_states[nb] = STATE_I
                if rng.random() < gamma:
                    new_states[node] = STATE_R
        states = new_states
    return S / n, I / n, R / n
def run_network_sis(
    adj: list[list[int]],
    n: int,
    beta: float,
    gamma: float,
    days: int,
    rng: np.random.Generator,

):
    states = np.zeros(n, dtype=int)
    patient_zero = int(rng.integers(0, n))
    states[patient_zero] = STATE_I
    S, I, R = np.zeros(days + 1), np.zeros(days + 1), np.zeros(days + 1)
    for day in range(days + 1):
        S[day] = np.sum(states == STATE_S)
        I[day] = np.sum(states == STATE_I)
        new_states = states.copy()
        for node in range(n):
            if states[node] == STATE_I:
                for nb in adj[node]:
                    if states[nb] == STATE_S and rng.random() < beta / max(len(adj[node]), 1):
                        new_states[nb] = STATE_I
                if rng.random() < gamma:
                    new_states[node] = STATE_S
        states = new_states
    return S / n, I / n, R / n
# ---------------------------------------------------------------------------
# Main simulation dispatcher
# ---------------------------------------------------------------------------

def run_simulation(
    model: str,
    network_type: str,
    r0: float,
    gamma: float,
    nodes: int,
    days: int,
    seed: int = 42,

):
    rng = np.random.default_rng(seed)
    adj = build_network_nx(network_type, nodes, seed) if _HAS_NETWORKX else build_network_numpy(network_type, nodes, rng)
    mean_degree = float(np.mean([len(x) for x in adj]))
    beta = r0 * gamma / max(mean_degree, 1e-6)
    if model == "sis":
        S, I, R = run_network_sis(adj, nodes, beta, gamma, days, rng)
    else:
        S, I, R = run_network_sir(adj, nodes, beta, gamma, days, rng)
    return {
        "S": S,
        "I": I,
        "R": R,
        "mean_degree": mean_degree,
        "network_r0": float(beta * mean_degree / gamma) if gamma > 0 else 0.0,
        "final_size_fraction": float(1 - S[-1]),
        "peak_infected_fraction": float(np.max(I)),
        "peak_day": int(np.argmax(I)),
    }
# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_network_curves(
    S: np.ndarray,
    I: np.ndarray,
    R: np.ndarray,
    output_dir: Path,
    model: str,
    network_type: str,
    nodes: int,
    r0: float,

):
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(S, label="S")
    ax.plot(I, label="I")
    if model == "sir":
        ax.plot(R, label="R")
    ax.set_title(f"{model.upper()} on {network_type} network (N={nodes}, R0={r0})")
    ax.set_xlabel("Day")
    ax.set_ylabel("Fraction of population")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "network_curve.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(output_dir: Path, summary: dict) -> Path:
    header = generate_report_header(
        title="Network Epidemic Model Report",
        skill_name=SKILL_NAME,
        extra_metadata={
            "Model": summary["model"].upper(),  # type: ignore[index]
            "Network type": summary["network_type"],  # type: ignore[index]
            "Nodes": str(summary["nodes"]),  # type: ignore[index]
            "R0 (input)": str(summary.get("r0_input", "N/A")),
            "Version": VERSION,
        },
    )
    body = f"""## Summary

| Metric | Value |
|--------|-------|
| Network type | {summary['network_type']} |
| Nodes | {summary['nodes']:,} |
| Mean degree | {summary['mean_degree']:.2f} |
| Network R0 | {summary['network_r0']:.3f} |
| Final epidemic size | {summary['final_size_fraction']:.1%} |
| Peak infected fraction | {summary['peak_infected_fraction']:.1%} |
| Peak day | Day {summary['peak_day']} |

## Figure

![Network SIR curves](figures/network_curve.png)

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
        prog="network_epidemic_model",
        description="EpiClaw Network Epidemic Model: discrete-time SIR/SIS on contact networks.",
    )
    p.add_argument("--output", type=Path, default=Path("output/network-epidemic-model"))
    p.add_argument("--model", choices=["sir", "sis"], default="sir")
    p.add_argument("--network-type", choices=["erdos", "barabasi", "smallworld"],
                   default="barabasi", dest="network_type")
    p.add_argument("--r0", type=float, default=2.5)
    p.add_argument("--gamma", type=float, default=0.1)
    p.add_argument("--nodes", type=int, default=1000)
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--demo", action="store_true", help="Run demo mode")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] Network epidemic model: {args.model.upper()} on {args.network_type} network")
    print(f"[info] Nodes={args.nodes} | R0={args.r0} | gamma={args.gamma} | days={args.days}")

    results = run_simulation(
        model=args.model,
        network_type=args.network_type,
        r0=args.r0,
        gamma=args.gamma,
        nodes=args.nodes,
        days=args.days,
    )

    summary = {
        "model": args.model,
        "network_type": args.network_type,
        "nodes": args.nodes,
        "r0_input": args.r0,
        "mean_degree": results["mean_degree"],
        "network_r0": results["network_r0"],
        "final_size_fraction": results["final_size_fraction"],
        "peak_infected_fraction": results["peak_infected_fraction"],
        "peak_day": results["peak_day"],
    }

    data = {
        "susceptible": results["S"].tolist(),
        "infected": results["I"].tolist(),
        "recovered": results["R"].tolist(),
    }

    print("[info] Generating network SIR curve figure...")
    plot_network_curves(
        results["S"], results["I"], results["R"],
        output_dir, args.model, args.network_type, args.nodes, args.r0,
    )

    print("[info] Writing report and result JSON...")
    write_report(output_dir, summary)
    write_result_json(output_dir, SKILL_NAME, VERSION, summary, data)

    print(f"[info] Done. Output written to: {output_dir.resolve()}")
    print(f"[info] Network R0: {results['network_r0']:.3f} | "
          f"Final size: {results['final_size_fraction']:.1%} | "
          f"Peak infected: {results['peak_infected_fraction']:.1%} on day {results['peak_day']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
