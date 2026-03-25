#!/usr/bin/env python3
"""EpiClaw Epi Calculator -- 2x2 epidemiological measure calculator."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "epi-calculator"


def _load_table_from_csv(path: Path) -> tuple[int, int, int, int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise RuntimeError("2x2 input CSV is empty.")

    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        group = str(row.get("group", "")).strip().lower()
        outcome = str(row.get("outcome", "")).strip().lower()
        count = int(row.get("count", 0))
        counts[(group, outcome)] = count
    try:
        a = counts[("exposed", "case")]
        b = counts[("exposed", "non-case")]
        c = counts[("unexposed", "case")]
        d = counts[("unexposed", "non-case")]
    except KeyError as exc:
        raise RuntimeError("CSV must contain exposed/unexposed x case/non-case rows.") from exc
    return a, b, c, d


def _load_table(args: argparse.Namespace) -> tuple[int, int, int, int]:
    if args.input:
        return _load_table_from_csv(Path(args.input))
    required = [args.exposed_cases, args.exposed_total, args.unexposed_cases, args.unexposed_total]
    if any(value is None for value in required):
        raise RuntimeError("Provide either --input or all four 2x2 count arguments.")
    a = int(args.exposed_cases)
    b = int(args.exposed_total) - a
    c = int(args.unexposed_cases)
    d = int(args.unexposed_total) - c
    if min(a, b, c, d) < 0:
        raise RuntimeError("Computed 2x2 cells must be non-negative.")
    return a, b, c, d


def _safe_div(num: float, den: float) -> float:
    return num / den if den else float("nan")


def _rr_or_ci(a: int, b: int, c: int, d: int) -> dict[str, float]:
    aa, bb, cc, dd = [value + 0.5 for value in (a, b, c, d)]
    risk_e = aa / (aa + bb)
    risk_u = cc / (cc + dd)
    rr = risk_e / risk_u
    rr_se = math.sqrt((1 / aa) - (1 / (aa + bb)) + (1 / cc) - (1 / (cc + dd)))
    rr_lo = math.exp(math.log(rr) - 1.96 * rr_se)
    rr_hi = math.exp(math.log(rr) + 1.96 * rr_se)

    odds_ratio = (aa * dd) / (bb * cc)
    or_se = math.sqrt((1 / aa) + (1 / bb) + (1 / cc) + (1 / dd))
    or_lo = math.exp(math.log(odds_ratio) - 1.96 * or_se)
    or_hi = math.exp(math.log(odds_ratio) + 1.96 * or_se)
    return {
        "risk_ratio": rr,
        "risk_ratio_ci_low": rr_lo,
        "risk_ratio_ci_high": rr_hi,
        "odds_ratio": odds_ratio,
        "odds_ratio_ci_low": or_lo,
        "odds_ratio_ci_high": or_hi,
    }


def _chi2_and_fisher(a: int, b: int, c: int, d: int) -> dict[str, float | None]:
    try:
        from scipy.stats import chi2_contingency, fisher_exact
    except ImportError:
        return {"chi2": None, "chi2_p": None, "fisher_or": None, "fisher_p": None}
    table = [[a, b], [c, d]]
    chi2, p_value, _dof, _expected = chi2_contingency(table, correction=True)
    fisher_or, fisher_p = fisher_exact(table)
    return {"chi2": float(chi2), "chi2_p": float(p_value), "fisher_or": float(fisher_or), "fisher_p": float(fisher_p)}


def _calculate_measures(a: int, b: int, c: int, d: int) -> dict[str, float | int | None]:
    exposed_total = a + b
    unexposed_total = c + d
    total = exposed_total + unexposed_total
    risk_e = _safe_div(a, exposed_total)
    risk_u = _safe_div(c, unexposed_total)
    risk_all = _safe_div(a + c, total)
    risk_difference = risk_e - risk_u
    par = risk_all - risk_u
    nnt = (1 / abs(risk_difference)) if risk_difference not in {0, float("nan")} and not math.isnan(risk_difference) else None

    result = {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "risk_exposed": risk_e,
        "risk_unexposed": risk_u,
        "attack_rate_exposed_pct": risk_e * 100,
        "attack_rate_unexposed_pct": risk_u * 100,
        "prevalence": risk_all,
        "risk_difference": risk_difference,
        "population_attributable_risk": par,
        "population_attributable_risk_pct": _safe_div(par, risk_all) * 100 if risk_all else None,
        "number_needed_to_treat_or_harm": nnt,
    }
    result.update(_rr_or_ci(a, b, c, d))
    result.update(_chi2_and_fisher(a, b, c, d))
    return result


def _select_output(metrics: dict[str, float | int | None], measure: str) -> dict[str, float | int | None]:
    groups = {
        "all": set(metrics.keys()),
        "rr": {"risk_ratio", "risk_ratio_ci_low", "risk_ratio_ci_high", "risk_difference"},
        "or": {"odds_ratio", "odds_ratio_ci_low", "odds_ratio_ci_high"},
        "chi2": {"chi2", "chi2_p", "fisher_or", "fisher_p"},
    }
    keep = groups[measure]
    return {key: value for key, value in metrics.items() if key in keep}


def generate_report(output_path: Path, metrics: dict[str, float | int | None]) -> None:
    header = generate_report_header(
        title="Epi Calculator Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Version": VERSION},
    )
    lines = [
        "## 2x2 Table",
        "",
        "| Cell | Count |",
        "|---|---|",
        f"| Exposed cases (a) | {metrics['a']} |",
        f"| Exposed non-cases (b) | {metrics['b']} |",
        f"| Unexposed cases (c) | {metrics['c']} |",
        f"| Unexposed non-cases (d) | {metrics['d']} |",
        "",
        "## Measures",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Risk ratio | {metrics['risk_ratio']:.4f} ({metrics['risk_ratio_ci_low']:.4f}, {metrics['risk_ratio_ci_high']:.4f}) |",
        f"| Odds ratio | {metrics['odds_ratio']:.4f} ({metrics['odds_ratio_ci_low']:.4f}, {metrics['odds_ratio_ci_high']:.4f}) |",
        f"| Risk difference | {metrics['risk_difference']:.4f} |",
        f"| Attack rate exposed | {metrics['attack_rate_exposed_pct']:.2f}% |",
        f"| Attack rate unexposed | {metrics['attack_rate_unexposed_pct']:.2f}% |",
        f"| Prevalence | {metrics['prevalence']:.4f} |",
        f"| Population attributable risk | {metrics['population_attributable_risk']:.4f} |",
        f"| PAR% | {metrics['population_attributable_risk_pct']:.2f}% |" if metrics['population_attributable_risk_pct'] is not None else "| PAR% | unavailable |",
        f"| NNT/NNH | {metrics['number_needed_to_treat_or_harm']:.2f} |" if metrics['number_needed_to_treat_or_harm'] is not None else "| NNT/NNH | undefined |",
    ]
    if metrics["chi2"] is not None:
        lines.extend(
            [
                f"| Chi-squared | {metrics['chi2']:.4f} (p={metrics['chi2_p']:.4g}) |",
                f"| Fisher exact | OR={metrics['fisher_or']:.4f} (p={metrics['fisher_p']:.4g}) |",
            ]
        )
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Epi Calculator -- 2x2 epidemiological measures.")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo 2x2 table")
    parser.add_argument("--input", default=None, help="CSV file with group,outcome,count rows")
    parser.add_argument("--measure", choices=["all", "rr", "or", "chi2"], default="all")
    parser.add_argument("--exposed-cases", type=int, default=None)
    parser.add_argument("--exposed-total", type=int, default=None)
    parser.add_argument("--unexposed-cases", type=int, default=None)
    parser.add_argument("--unexposed-total", type=int, default=None)
    parser.add_argument("--output", required=True, help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo and not args.input:
        a, b, c, d = 40, 60, 10, 90
    else:
        a, b, c, d = _load_table(args)
    metrics = _calculate_measures(a, b, c, d)
    selected_metrics = _select_output(metrics, args.measure)
    report_path = output_dir / "report.md"
    generate_report(report_path, metrics)
    write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={"measure": args.measure, **selected_metrics},
        data=selected_metrics,
    )
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
