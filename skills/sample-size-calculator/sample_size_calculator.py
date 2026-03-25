#!/usr/bin/env python3
"""EpiClaw Sample-Size-Calculator -- power and sample size for epidemiological study designs."""
from __future__ import annotations
import argparse, math, sys
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "sample-size-calculator"


# ---------------------------------------------------------------------------
# Core formulas
# ---------------------------------------------------------------------------

def _z(p: float) -> float:
    from scipy.stats import norm
    return float(norm.ppf(p))


def sample_size_cohort_rct(p1: float, p2: float, alpha: float, power: float) -> int:
    """Two-proportions z-test (one-sided alpha/2).

    n = (z_alpha*sqrt(2*p_bar*(1-p_bar)) + z_beta*sqrt(p1*(1-p1)+p2*(1-p2)))^2 / (p1-p2)^2
    """
    z_alpha = _z(1.0 - alpha / 2.0)
    z_beta = _z(power)
    p_bar = (p1 + p2) / 2.0
    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denom = (p1 - p2) ** 2
    return math.ceil(numerator / denom)


def sample_size_case_control_kelsey(
    p_case: float, or_target: float, alpha: float, power: float, ratio: float

):
    p_control = p_case
    odds = (or_target * p_control) / max(1 - p_control + or_target * p_control, 1e-9)
    p_exposed = odds
    z_alpha = _z(1.0 - alpha / 2.0)
    z_beta = _z(power)
    p_bar = (p_exposed + ratio * p_control) / (1 + ratio)
    numerator = (z_alpha * math.sqrt((1 + 1 / ratio) * p_bar * (1 - p_bar)) + z_beta * math.sqrt(p_exposed * (1 - p_exposed) + (p_control * (1 - p_control) / ratio))) ** 2
    denom = (p_exposed - p_control) ** 2
    n_case = max(1, math.ceil(numerator / denom))
    n_ctrl = math.ceil(n_case * ratio)
    return n_case, n_ctrl
def sample_size_cross_sectional(p: float, alpha: float, margin_of_error: float = 0.05) -> int:
    """Simple proportion estimate sample size."""
    z = _z(1.0 - alpha / 2.0)
    return math.ceil(z ** 2 * p * (1 - p) / margin_of_error ** 2)


def compute_power_curve(
    p1: float, p2: float, alpha: float, ns: list[int]

):
    z_alpha = _z(1.0 - alpha / 2.0)
    powers = []
    for n in ns:
        se = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / max(n, 1))
        z_effect = abs(p1 - p2) / max(se, 1e-9)
        power_val = 0.5 * (1 + math.erf((z_effect - z_alpha) / math.sqrt(2)))
        powers.append(round(max(0.0, min(1.0, power_val)), 4))
    return powers
# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_power_curve(ns: list[int], powers: list[float], target_n: int, out_dir: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ns, powers, color="steelblue", lw=2)
    ax.axhline(0.8, color="tomato", ls="--", label="Power = 0.80")
    ax.axvline(target_n, color="green", ls=":", label=f"Required n = {target_n}")
    ax.set_xlabel("Sample size per group (n)")
    ax.set_ylabel("Power")
    ax.set_title("Power Curve")
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    fig_path = fig_dir / "power_curve.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[info] Power curve saved to {fig_path}")
    return fig_path


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(
    design: str, alpha: float, power: float,
    p1: float, p2: float, n_per_group: int, n_total: int,
    detectable_rr: float, fig_path: Path | None,

):
    lines = [
        generate_report_header(
            title="Sample Size Calculation Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Design": design, "Version": VERSION},
        ),
        "## Summary",
        "",
        f"- Alpha: `{alpha}`",
        f"- Target power: `{power}`",
        f"- Baseline risk p1: `{p1}`",
        f"- Comparator risk p2: `{p2}`",
        f"- Required n per group: `{n_per_group}`",
        f"- Total sample size: `{n_total}`",
        f"- Detectable RR: `{detectable_rr:.3f}`",
        "",
    ]
    if fig_path:
        lines.append(f"Power curve: `{fig_path}`")
        lines.append("")
    lines.append(generate_report_footer())
    return "\n".join(lines)
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sample size and power calculation")
    parser.add_argument("--design", choices=["cohort", "case-control", "rct", "cross-sectional"], default="cohort")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.8)
    parser.add_argument("--p1", type=float, default=0.1, help="Event rate in exposed/treated group")
    parser.add_argument("--p2", type=float, default=0.05, help="Event rate in unexposed/control group")
    parser.add_argument("--ratio", type=float, default=1.0, help="n_control / n_case")
    parser.add_argument("--output", default="output/sample-size-calculator")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    args = parser.parse_args(argv)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw {SKILL_NAME} v{VERSION}")
    print(f"[info] Design={args.design}, alpha={args.alpha}, power={args.power}, p1={args.p1}, p2={args.p2}")

    if args.design in ("cohort", "rct"):
        n_per = sample_size_cohort_rct(args.p1, args.p2, args.alpha, args.power)
        n_total = n_per * 2
        n_per_group = n_per
    elif args.design == "case-control":
        or_target = (args.p1 / (1 - args.p1)) / (args.p2 / (1 - args.p2))
        n_case, n_ctrl = sample_size_case_control_kelsey(args.p2, or_target, args.alpha, args.power, args.ratio)
        n_per_group = n_case
        n_total = n_case + n_ctrl
    else:  # cross-sectional
        n_per_group = sample_size_cross_sectional(args.p1, args.alpha)
        n_total = n_per_group

    detectable_rr = args.p1 / args.p2 if args.p2 > 0 else float("inf")
    print(f"[info] Required n per group: {n_per_group}, total: {n_total}")

    # Power curve
    import numpy as np
    ns_range = list(range(10, max(n_per_group * 3, 300), max(1, n_per_group // 50)))
    powers_curve = compute_power_curve(args.p1, args.p2, args.alpha, ns_range)

    fig_path: Path | None = None
    try:
        fig_path = plot_power_curve(ns_range, powers_curve, n_per_group, out_dir)
    except Exception as exc:
        print(f"[warn] Could not generate plot: {exc}")

    report_md = build_report(
        args.design, args.alpha, args.power, args.p1, args.p2,
        n_per_group, n_total, detectable_rr, fig_path
    )
    report_path = out_dir / "report.md"
    report_path.write_text(report_md)
    print(f"[info] Report written to {report_path}")

    summary = {
        "design": args.design,
        "alpha": args.alpha,
        "power": args.power,
        "p1": args.p1,
        "p2": args.p2,
        "n_per_group": n_per_group,
        "n_total": n_total,
        "detectable_rr": round(detectable_rr, 4),
    }
    data = {
        "power_curve": {
            "sample_sizes": ns_range,
            "powers": powers_curve,
        }
    }
    result_path = write_result_json(out_dir, SKILL_NAME, VERSION, summary, data)
    print(f"[info] Result JSON written to {result_path}")
    print("[info] Done.")


if __name__ == "__main__":
    main()
