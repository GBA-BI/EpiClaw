#!/usr/bin/env python3
"""EpiClaw Early Warning System -- statistical aberration detection for weekly case counts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "early-warning-system"


# ---------------------------------------------------------------------------
# Detection algorithms
# ---------------------------------------------------------------------------

def run_cusum(
    counts: np.ndarray,
    threshold: float = 3.0,

):
    baseline = float(np.mean(counts[: min(8, len(counts))]))
    sigma = float(np.std(counts[: min(8, len(counts))])) or 1.0
    statistic = np.zeros(len(counts), dtype=float)
    alert_weeks: list[int] = []
    drift = 0.5 * sigma
    for idx, value in enumerate(counts):
        prev = statistic[idx - 1] if idx > 0 else 0.0
        statistic[idx] = max(0.0, prev + (float(value) - baseline - drift) / sigma)
        if statistic[idx] >= threshold:
            alert_weeks.append(idx + 1)
    return statistic, alert_weeks
def run_ears(
    counts: np.ndarray,
    threshold: float = 3.0,

):
    statistic = np.zeros(len(counts), dtype=float)
    alert_weeks: list[int] = []
    for idx, value in enumerate(counts):
        start = max(0, idx - 7)
        baseline = counts[start:idx] if idx > 0 else counts[:1]
        mean = float(np.mean(baseline))
        sigma = float(np.std(baseline)) or 1.0
        statistic[idx] = (float(value) - mean) / sigma
        if idx >= 2 and statistic[idx] >= threshold:
            alert_weeks.append(idx + 1)
    return statistic, alert_weeks
def run_farrington(
    counts: np.ndarray,
    threshold: float = 3.0,

):
    expected = np.zeros(len(counts), dtype=float)
    statistic = np.zeros(len(counts), dtype=float)
    alert_weeks: list[int] = []
    for idx, value in enumerate(counts):
        start = max(0, idx - 6)
        window = counts[start:idx] if idx > 0 else counts[:1]
        mean = float(np.mean(window))
        variance = max(mean, float(np.var(window)), 1.0)
        expected[idx] = mean
        statistic[idx] = (float(value) - mean) / np.sqrt(variance)
        if idx >= 4 and statistic[idx] >= threshold:
            alert_weeks.append(idx + 1)
    return statistic, alert_weeks
# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

def _alert_table(counts: np.ndarray, statistic: np.ndarray, alert_weeks: list[int]) -> list[str]:
    """Build a markdown table of all weeks with alert flag."""
    lines = [
        "| Week | Count | Statistic | Alert |",
        "|---|---|---|---|",
    ]
    alert_set = set(alert_weeks)
    for t, (cnt, stat) in enumerate(zip(counts, statistic), start=1):
        flag = "YES" if t in alert_set else ""
        lines.append(f"| {t} | {cnt:.0f} | {stat:.2f} | {flag} |")
    return lines


def generate_report(
    counts: np.ndarray,
    statistic: np.ndarray,
    alert_weeks: list[int],
    method: str,
    threshold: float,
    pathogen: str,
    output_path: Path,

):
    header = generate_report_header(
        title="Early Warning System Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Method": method, "Threshold": str(threshold), "Pathogen": pathogen, "Version": VERSION},
    )
    lines = [
        "## Detection Summary",
        "",
        f"- Weeks analysed: `{len(counts)}`",
        f"- Alerts detected: `{len(alert_weeks)}`",
        f"- Alert weeks: `{alert_weeks}`",
        "",
        "## Weekly Results",
        "",
        *_alert_table(counts, statistic, alert_weeks),
        "",
        generate_report_footer(),
    ]
    output_path.write_text(header + "\n".join(lines), encoding="utf-8")
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="early_warning",
        description="EpiClaw Early Warning System -- statistical aberration detection.",
    )
    parser.add_argument("--input", type=str, default=None, help="CSV with columns: week, count")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument(
        "--method",
        type=str,
        choices=["cusum", "ears", "farrington"],
        default="cusum",
        help="Detection method (default: cusum)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Alert threshold multiplier (default: 3.0)",
    )
    parser.add_argument("--pathogen", type=str, default="Unknown", help="Pathogen name")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo data")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.demo or args.input is None:
        counts = np.array([12, 15, 14, 13, 16, 15, 14, 18, 17, 16, 20, 19, 22, 25, 41, 38], dtype=float)
        print(f"[info] Using built-in demo data ({len(counts)} weeks).")
    else:
        import csv

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[error] Input file not found: {input_path}")
            sys.exit(1)
        counts_list: list[float] = []
        with open(input_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                counts_list.append(float(row["count"]))
        counts = np.array(counts_list)
        print(f"[info] Loaded {len(counts)} weeks from {input_path}.")

    print(f"[info] Running {args.method.upper()} detection (threshold={args.threshold}) ...")

    if args.method == "cusum":
        statistic, alert_weeks = run_cusum(counts, args.threshold)
    elif args.method == "ears":
        statistic, alert_weeks = run_ears(counts, args.threshold)
    else:  # farrington
        statistic, alert_weeks = run_farrington(counts, args.threshold)

    print(f"[info] Alerts detected in {len(alert_weeks)} week(s): {alert_weeks}")

    # Report
    report_path = out / "report.md"
    generate_report(counts, statistic, alert_weeks, args.method, args.threshold, args.pathogen, report_path)
    print(f"[info] Report written to {report_path}")

    # result.json
    write_result_json(
        output_dir=out,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "weeks_analyzed": int(len(counts)),
            "alerts_detected": int(len(alert_weeks)),
            "method": args.method,
            "threshold": float(args.threshold),
        },
        data={
            "counts": [float(v) for v in counts],
            "cusum": [round(float(v), 4) for v in statistic],
            "alert_weeks": alert_weeks,
        },
    )
    print(f"[info] Done. Report: {out}/report.md")


if __name__ == "__main__":
    main()
