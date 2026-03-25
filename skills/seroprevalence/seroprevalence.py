#!/usr/bin/env python3
"""EpiClaw Seroprevalence -- survey adjustment and IFR estimation."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "seroprevalence"
DEMO_ROWS = [
    {"region": "Metro A", "positive_tests": 42, "total_tested": 500, "population": 1200000, "deaths": 210},
    {"region": "Metro B", "positive_tests": 28, "total_tested": 360, "population": 860000, "deaths": 96},
]


def _wilson_interval(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        raise RuntimeError("total_tested must be > 0")
    phat = x / n
    denom = 1 + (z * z / n)
    center = (phat + (z * z / (2 * n))) / denom
    margin = z * math.sqrt((phat * (1 - phat) / n) + (z * z / (4 * n * n))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def _rogan_gladen(obs: float, sensitivity: float, specificity: float) -> float:
    denom = sensitivity + specificity - 1
    if denom <= 0:
        raise RuntimeError("Rogan-Gladen correction requires sensitivity + specificity > 1.")
    corrected = (obs - (1 - specificity)) / denom
    return min(1.0, max(0.0, corrected))


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _analyze_rows(rows: list[dict[str, str]], args: argparse.Namespace) -> tuple[list[dict[str, object]], dict[str, object]]:
    output_rows: list[dict[str, object]] = []
    for idx, row in enumerate(rows, start=1):
        positives = int(row.get("positive_tests") or row.get("positives") or 0)
        tested = int(row.get("total_tested") or row.get("tested") or 0)
        population = int(row.get("population") or args.population or 0)
        deaths = int(row.get("deaths") or args.deaths or 0)
        region = row.get("region") or row.get("country") or f"survey_{idx}"
        observed = positives / tested
        observed_lo, observed_hi = _wilson_interval(positives, tested)
        corrected = _rogan_gladen(observed, args.sensitivity, args.specificity)
        corrected_lo = _rogan_gladen(observed_lo, args.sensitivity, args.specificity)
        corrected_hi = _rogan_gladen(observed_hi, args.sensitivity, args.specificity)
        infected_estimate = corrected * population if population else None
        ifr = (deaths / infected_estimate) if deaths and infected_estimate else None
        hit = (1 - 1 / args.r0) if args.r0 else None
        immunity_gap = (hit - corrected) if hit is not None else None
        output_rows.append(
            {
                "region": region,
                "positive_tests": positives,
                "total_tested": tested,
                "observed_prevalence": round(observed, 6),
                "observed_ci_low": round(observed_lo, 6),
                "observed_ci_high": round(observed_hi, 6),
                "corrected_prevalence": round(corrected, 6),
                "corrected_ci_low": round(corrected_lo, 6),
                "corrected_ci_high": round(corrected_hi, 6),
                "population": population or None,
                "deaths": deaths or None,
                "ifr": round(ifr, 8) if ifr is not None else None,
                "herd_immunity_threshold": round(hit, 6) if hit is not None else None,
                "immunity_gap": round(immunity_gap, 6) if immunity_gap is not None else None,
            }
        )
    corrected_values = [row["corrected_prevalence"] for row in output_rows]
    summary = {
        "n_surveys": len(output_rows),
        "mean_corrected_prevalence": round(sum(corrected_values) / len(corrected_values), 6),
        "max_corrected_prevalence": max(corrected_values),
        "min_corrected_prevalence": min(corrected_values),
        "sensitivity": args.sensitivity,
        "specificity": args.specificity,
        "r0": args.r0,
    }
    return output_rows, summary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_report(output_path: Path, rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    header = generate_report_header(title="Seroprevalence Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION})
    lines = [
        "## Survey Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Surveys analyzed | {summary['n_surveys']} |",
        f"| Mean corrected prevalence | {summary['mean_corrected_prevalence']:.4f} |",
        f"| Sensitivity | {summary['sensitivity']} |",
        f"| Specificity | {summary['specificity']} |",
        "",
        "## Survey Estimates",
        "",
        "| Region | Corrected prevalence | 95% CI | IFR |",
        "|---|---|---|---|",
    ]
    for row in rows:
        ifr_text = f"{row['ifr']:.6f}" if row["ifr"] is not None else "NA"
        lines.append(
            f"| {row['region']} | {row['corrected_prevalence']:.4f} | {row['corrected_ci_low']:.4f} to {row['corrected_ci_high']:.4f} | {ifr_text} |"
        )
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Seroprevalence -- Rogan-Gladen adjustment and IFR estimation.")
    parser.add_argument("--input", default=None, help="CSV with positive_tests,total_tested and optional population,deaths")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo serosurvey")
    parser.add_argument("--sensitivity", type=float, default=0.93)
    parser.add_argument("--specificity", type=float, default=0.99)
    parser.add_argument("--deaths", type=int, default=None)
    parser.add_argument("--population", type=int, default=None)
    parser.add_argument("--r0", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        input_path = output_dir / "demo_serosurvey.csv"
        _write_csv(input_path, DEMO_ROWS)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
    rows = _load_rows(input_path)
    analyzed_rows, summary = _analyze_rows(rows, args)
    summary_csv = output_dir / "seroprevalence_summary.csv"
    _write_csv(summary_csv, analyzed_rows)
    report_path = output_dir / "report.md"
    generate_report(report_path, analyzed_rows, summary)
    summary["adjusted_prevalence"] = summary["mean_corrected_prevalence"]
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data={"surveys": analyzed_rows, "summary_csv": str(summary_csv)})
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
