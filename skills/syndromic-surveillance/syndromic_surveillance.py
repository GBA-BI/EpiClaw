#!/usr/bin/env python3
"""EpiClaw Syndromic Surveillance -- EWMA-based ED visit aberration detection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "syndromic-surveillance"

# Syndrome-specific parameters (lambda for EWMA smoothing)
SYNDROME_PARAMS: dict[str, dict[str, Any]] = {
    "respiratory": {"lam": 0.2, "base_mean": 120.0, "amplitude": 20.0, "trend": 0.1},
    "gastrointestinal": {"lam": 0.3, "base_mean": 60.0, "amplitude": 10.0, "trend": 0.05},
    "febrile": {"lam": 0.25, "base_mean": 80.0, "amplitude": 15.0, "trend": 0.08},
}


# ---------------------------------------------------------------------------
# EWMA detection
# ---------------------------------------------------------------------------

def run_ewma(
    counts: np.ndarray,
    lam: float = 0.2,
    threshold: float = 3.0,

):
    ewma = np.zeros(len(counts), dtype=float)
    ewma[0] = float(counts[0])
    baseline = float(np.mean(counts[: min(7, len(counts))]))
    sigma = float(np.std(counts[: min(7, len(counts))])) or 1.0
    alert_days: list[int] = []
    for idx in range(1, len(counts)):
        ewma[idx] = lam * float(counts[idx]) + (1 - lam) * ewma[idx - 1]
        z = (ewma[idx] - baseline) / (sigma * np.sqrt(lam / (2 - lam)))
        if z >= threshold:
            alert_days.append(idx + 1)
    return ewma, alert_days
# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _alert_table(counts: np.ndarray, ewma: np.ndarray, alert_days: list[int]) -> list[str]:
    alert_set = set(alert_days)
    lines = [
        "| Day | Count | EWMA | Alert |",
        "|---|---|---|---|",
    ]
    for t, (cnt, ew) in enumerate(zip(counts, ewma), start=1):
        flag = "YES" if t in alert_set else ""
        lines.append(f"| {t} | {cnt:.0f} | {ew:.1f} | {flag} |")
    return lines


def generate_report(
    counts: np.ndarray,
    ewma: np.ndarray,
    alert_days: list[int],
    syndrome: str,
    output_path: Path,

):
    header = generate_report_header(
        title="Syndromic Surveillance Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Syndrome": syndrome, "Version": VERSION},
    )
    lines = [
        "## Detection Summary",
        "",
        f"- Days analysed: `{len(counts)}`",
        f"- Syndrome: `{syndrome}`",
        f"- Alerts detected: `{len(alert_days)}`",
        "",
        "## Daily Results",
        "",
        *_alert_table(counts, ewma, alert_days),
        "",
        generate_report_footer(),
    ]
    output_path.write_text(header + "\n".join(lines), encoding="utf-8")
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="syndromic_surveillance",
        description="EpiClaw Syndromic Surveillance -- EWMA ED visit aberration detection.",
    )
    parser.add_argument("--input", type=str, default=None, help="CSV with columns: day, count")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument(
        "--syndrome",
        type=str,
        choices=["respiratory", "gastrointestinal", "febrile"],
        default="respiratory",
        help="Syndrome category (default: respiratory)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="EWMA alert threshold in sigma units (default: 3.0)",
    )
    parser.add_argument(
        "--lambda-param",
        type=float,
        default=None,
        help="EWMA smoothing lambda 0 < lambda <= 1 (default: syndrome-specific)",
        dest="lam",
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demo data")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.demo or args.input is None:
        params = SYNDROME_PARAMS.get(args.syndrome, SYNDROME_PARAMS["respiratory"])
        days = np.arange(30, dtype=float)
        counts = params["base_mean"] + params["amplitude"] * np.sin(days / 5.0) + params["trend"] * days
        counts[24:27] += params["amplitude"] * 2.5
        counts = np.round(counts).astype(float)
        print(f"[info] Using built-in demo data ({len(counts)} days).")
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
        print(f"[info] Loaded {len(counts)} days from {input_path}.")

    # EWMA smoothing parameter
    params = SYNDROME_PARAMS.get(args.syndrome, SYNDROME_PARAMS["respiratory"])
    lam = args.lam if args.lam is not None else params["lam"]
    if not (0 < lam <= 1):
        print("[error] lambda must be in (0, 1]")
        sys.exit(1)

    print(f"[info] Running EWMA detection (lambda={lam}, threshold={args.threshold}) ...")
    ewma, alert_days = run_ewma(counts, lam=lam, threshold=args.threshold)

    baseline_mean = float(np.mean(counts))
    print(f"[info] Alerts detected on {len(alert_days)} day(s): {alert_days}")

    # Report
    report_path = out / "report.md"
    generate_report(counts, ewma, alert_days, args.syndrome, report_path)
    print(f"[info] Report written to {report_path}")

    # result.json
    write_result_json(
        output_dir=out,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "days_analyzed": int(len(counts)),
            "syndrome": args.syndrome,
            "alerts_detected": int(len(alert_days)),
            "baseline_mean": round(baseline_mean, 2),
        },
        data={
            "daily_counts": [float(v) for v in counts],
            "ewma": [round(float(v), 4) for v in ewma],
            "alert_days": alert_days,
        },
    )
    print(f"[info] Done. Report: {out}/report.md")


if __name__ == "__main__":
    main()
