#!/usr/bin/env python3
"""EpiClaw Policy-Evaluator -- health economic evaluation of public health interventions."""
from __future__ import annotations
import argparse, math, sys
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "policy-evaluator"


# ---------------------------------------------------------------------------
# Core: cost-effectiveness calculation
# ---------------------------------------------------------------------------

def evaluate_vaccination_coverage(
    population: int,
    coverage: float,
    cost_per_dose: float,
    ve: float,
    attack_rate: float,
    cfr: float,
    daly_per_death: float,
    daly_per_case: float,
    n_doses: int = 1,

):
    doses = population * coverage * n_doses
    cost = doses * cost_per_dose
    cases_without = population * attack_rate
    cases_averted = cases_without * coverage * ve
    deaths_averted = cases_averted * cfr
    dalys_averted = deaths_averted * daly_per_death + cases_averted * daly_per_case
    icer = cost / dalys_averted if dalys_averted > 0 else float("inf")
    return {
        "coverage": coverage,
        "cost": round(cost, 2),
        "cases_averted": round(cases_averted, 2),
        "deaths_averted": round(deaths_averted, 2),
        "dalys_averted": round(dalys_averted, 2),
        "icer": round(icer, 2) if math.isfinite(icer) else float("inf"),
    }
# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_cost_effectiveness(
    coverage_results: list[dict],
    gdp_per_capita: float,
    optimal_coverage: float,
    budget: float,
    out_dir: Path,

):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    xs = [row["cost"] for row in coverage_results]
    ys = [row["dalys_averted"] for row in coverage_results]
    labels = [f"{int(row['coverage'] * 100)}%" for row in coverage_results]
    ax.scatter(xs, ys, color="#2563eb")
    for x, y, label in zip(xs, ys, labels):
        ax.text(x, y, label)
    ax.axvline(budget, color="red", linestyle="--", label="Budget")
    ax.set_xlabel("Cost")
    ax.set_ylabel("DALYs averted")
    ax.set_title("Cost-effectiveness frontier")
    ax.legend()
    fig.tight_layout()
    fig_path = fig_dir / "cost_effectiveness.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig_path
# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(
    intervention: str,
    country: str,
    budget: float,
    optimal: dict,
    coverage_results: list[dict],
    gdp_per_capita: float,
    fig_path: Path | None,

):
    lines = [
        generate_report_header(
            title="Policy Evaluation Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Intervention": intervention, "Country": country, "Version": VERSION},
        ),
        "## Optimal Strategy",
        "",
        f"- Optimal coverage within budget `${budget:,.0f}`: `{optimal['coverage']:.0%}`",
        f"- DALYs averted: `{optimal['dalys_averted']}`",
        f"- Total cost: `${optimal['cost']:,.0f}`",
        f"- ICER: `${optimal['icer']:,.0f}` per DALY",
        f"- WHO-style threshold (3x GDP per capita): `${3.0 * gdp_per_capita:,.0f}`",
        "",
        "## Coverage Options",
        "",
        "| Coverage | Cost | DALYs averted | ICER |",
        "|---|---|---|---|",
    ]
    for row in coverage_results:
        lines.append(f"| {row['coverage']:.0%} | ${row['cost']:,.0f} | {row['dalys_averted']} | ${row['icer']:,.0f} |")
    if fig_path:
        lines.extend(["", f"Figure: `{fig_path}`", ""])
    lines.append(generate_report_footer())
    return "\n".join(lines)
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Public health policy evaluation")
    parser.add_argument("--intervention", choices=["vaccination", "treatment", "npi"], default="vaccination")
    parser.add_argument("--country", default="Demo Country")
    parser.add_argument("--budget", type=float, default=1_000_000.0)
    parser.add_argument("--output", default="output/policy-evaluator")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    args = parser.parse_args(argv)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw {SKILL_NAME} v{VERSION}")
    print(f"[info] Intervention: {args.intervention}, Country: {args.country}, Budget: ${args.budget:,.0f}")

    # Demo parameters
    population = 100_000
    coverage_options = [0.3, 0.5, 0.7, 0.9]
    cost_per_dose = 5.0
    ve = 0.70
    attack_rate_without = 0.40
    cfr = 0.01
    daly_per_death = 30.0
    daly_per_case = 0.1
    gdp_per_capita = 5000.0

    print(f"[info] Population={population:,}, VE={ve:.0%}, AR={attack_rate_without:.0%}, CFR={cfr:.2%}")
    print(f"[info] Cost per dose=${cost_per_dose}, GDP per capita=${gdp_per_capita:,}")

    coverage_results = []
    for cov in coverage_options:
        res = evaluate_vaccination_coverage(
            population, cov, cost_per_dose, ve,
            attack_rate_without, cfr, daly_per_death, daly_per_case
        )
        coverage_results.append(res)
        print(f"[info]   Coverage {cov*100:.0f}%: cost=${res['cost']:,.0f}, DALYs={res['dalys_averted']:,.1f}, ICER=${res['icer']:,.0f}")

    # Find optimal: highest DALYs averted within budget
    affordable = [r for r in coverage_results if r["cost"] <= args.budget]
    if affordable:
        optimal = max(affordable, key=lambda r: r["dalys_averted"])
    else:
        optimal = min(coverage_results, key=lambda r: r["cost"])
    print(f"[info] Optimal coverage: {optimal['coverage']*100:.0f}% (ICER=${optimal['icer']:,.0f}/DALY)")

    threshold = 3.0 * gdp_per_capita
    cost_effective = optimal["icer"] <= threshold

    fig_path: Path | None = None
    try:
        fig_path = plot_cost_effectiveness(
            coverage_results, gdp_per_capita, optimal["coverage"], args.budget, out_dir
        )
    except Exception as exc:
        print(f"[warn] Could not generate plot: {exc}")

    report_md = build_report(
        args.intervention, args.country, args.budget,
        optimal, coverage_results, gdp_per_capita, fig_path
    )
    report_path = out_dir / "report.md"
    report_path.write_text(report_md)
    print(f"[info] Report written to {report_path}")

    summary = {
        "intervention": args.intervention,
        "optimal_coverage": optimal["coverage"],
        "dalys_averted": optimal["dalys_averted"],
        "total_cost": optimal["cost"],
        "icer": optimal["icer"],
        "cost_effective": cost_effective,
    }
    data = {
        "coverage_analysis": coverage_results,
        "who_threshold_3x_gdp": threshold,
        "parameters": {
            "population": population,
            "ve": ve,
            "attack_rate_without_intervention": attack_rate_without,
            "cfr": cfr,
            "cost_per_dose": cost_per_dose,
            "daly_per_death": daly_per_death,
            "daly_per_case": daly_per_case,
            "gdp_per_capita": gdp_per_capita,
        },
    }
    result_path = write_result_json(out_dir, SKILL_NAME, VERSION, summary, data)
    print(f"[info] Result JSON written to {result_path}")
    print("[info] Done.")


if __name__ == "__main__":
    main()
