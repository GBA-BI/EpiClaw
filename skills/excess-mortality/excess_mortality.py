#!/usr/bin/env python3
"""EpiClaw Excess Mortality -- P-score and Z-score excess death estimation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "excess-mortality"


# ---------------------------------------------------------------------------
# Baseline computation
# ---------------------------------------------------------------------------

def compute_baseline(
    observed: np.ndarray,
    baseline_weeks: int,

):
    baseline = observed[:baseline_weeks]
    baseline_mean = float(np.mean(baseline))
    baseline_std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 1.0
    expected = np.full_like(observed, baseline_mean, dtype=float)
    return expected, baseline_mean, baseline_std or 1.0
# ---------------------------------------------------------------------------
# Excess mortality metrics
# ---------------------------------------------------------------------------

def compute_p_scores(
    observed: np.ndarray,
    expected: np.ndarray,

):
    safe = np.where(expected == 0, np.nan, expected)
    return ((observed - safe) / safe) * 100.0
def compute_z_scores(
    observed: np.ndarray,
    expected: np.ndarray,
    baseline_std: float,

):
    denom = baseline_std or 1.0
    return (observed - expected) / denom
# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _results_table(
    observed: np.ndarray,
    expected: np.ndarray,
    scores: np.ndarray,
    excess: np.ndarray,
    method: str,

):
    lines = [
        "| Week | Observed | Expected | Excess | Score |",
        "|---|---|---|---|---|",
    ]
    for idx, (obs, exp, score, ex) in enumerate(zip(observed, expected, scores, excess), start=1):
        lines.append(f"| {idx} | {obs:.1f} | {exp:.1f} | {ex:.1f} | {score:.2f} |")
    return lines
def _interpretation(
    total_excess: float,
    peak_week: int,
    peak_score: float,
    method: str,
    country: str,

):
    location = country or "the selected population"
    metric = "P-score" if method == "p-score" else "Z-score"
    return (
        f"Across {location}, total positive excess deaths were estimated at {total_excess:.0f}. "
        f"The strongest deviation occurred in week {peak_week} with {metric} {peak_score:.2f}."
    )
def generate_report(
    observed: np.ndarray,
    expected: np.ndarray,
    scores: np.ndarray,
    excess: np.ndarray,
    total_excess: float,
    peak_week: int,
    peak_score: float,
    method: str,
    country: str,
    output_path: Path,

):
    header = generate_report_header(
        title="Excess Mortality Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Method": method, "Country": country or "N/A", "Version": VERSION},
    )
    lines = [
        "## Summary",
        "",
        f"- Weeks analysed: `{len(observed)}`",
        f"- Total excess deaths: `{total_excess:.1f}`",
        f"- Peak week: `{peak_week}`",
        "",
        "## Interpretation",
        "",
        _interpretation(total_excess, peak_week, peak_score, method, country),
        "",
        "## Weekly Results",
        "",
        *_results_table(observed, expected, scores, excess, method),
        "",
        generate_report_footer(),
    ]
    output_path.write_text(header + "\n".join(lines), encoding="utf-8")
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="excess_mortality",
        description="EpiClaw Excess Mortality -- P-score and Z-score excess death estimation.",
    )
    parser.add_argument("--input", type=str, default=None, help="CSV with columns: week, deaths")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument(
        "--method",
        type=str,
        choices=["p-score", "z-score"],
        default="p-score",
        help="Excess mortality method (default: p-score)",
    )
    parser.add_argument(
        "--baseline-years",
        type=int,
        default=5,
        dest="baseline_years",
        help="Number of years for baseline (default: 5; used to compute baseline_weeks = baseline_years*52, capped at data length)",
    )
    parser.add_argument("--country", type=str, default="", help="Country name for report labeling")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo data")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.demo or args.input is None:
        observed = np.array([102, 98, 101, 99, 100, 104, 103, 98, 97, 101, 120, 132, 140, 128, 122, 115], dtype=float)
        print(f"[info] Using built-in demo data ({len(observed)} weeks).")
    else:
        import csv

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[error] Input file not found: {input_path}")
            sys.exit(1)
        deaths_list: list[float] = []
        with open(input_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                deaths_list.append(float(row["deaths"]))
        observed = np.array(deaths_list)
        print(f"[info] Loaded {len(observed)} weeks from {input_path}.")

    # Baseline period
    baseline_weeks = min(args.baseline_years * 52, len(observed))
    if baseline_weeks < 2:
        print("[error] Insufficient data for baseline estimation (need at least 2 weeks).")
        sys.exit(1)
    print(f"[info] Estimating baseline from first {baseline_weeks} weeks ...")

    expected, baseline_mean, baseline_std = compute_baseline(observed, baseline_weeks)

    # Compute scores
    print(f"[info] Computing {args.method} excess mortality ...")
    if args.method == "p-score":
        scores = compute_p_scores(observed, expected)
    else:
        scores = compute_z_scores(observed, expected, baseline_std)

    excess = observed - expected
    total_excess = float(np.sum(np.maximum(excess, 0)))

    # Peak
    valid_scores = np.where(np.isnan(scores), -np.inf, scores)
    peak_week = int(np.argmax(valid_scores)) + 1
    peak_score = float(valid_scores[peak_week - 1])

    print(f"[info] Total excess deaths: {total_excess:.0f}")
    print(f"[info] Peak week: {peak_week}, peak score: {peak_score:.1f}")

    # Report
    report_path = out / "report.md"
    generate_report(
        observed, expected, scores, excess,
        total_excess, peak_week, peak_score,
        args.method, args.country, report_path,
    )
    print(f"[info] Report written to {report_path}")

    # result.json
    write_result_json(
        output_dir=out,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "weeks_analyzed": int(len(observed)),
            "method": args.method,
            "total_excess_deaths": round(total_excess, 1),
            "peak_week": peak_week,
            "peak_p_score": round(peak_score, 2),
        },
        data={
            "observed": [float(v) for v in observed],
            "expected": [round(float(v), 2) for v in expected],
            "p_scores": [round(float(v), 4) if not np.isnan(v) else None for v in scores],
            "excess": [round(float(v), 2) for v in excess],
        },
    )
    print(f"[info] Done. Report: {out}/report.md")


if __name__ == "__main__":
    main()
