#!/usr/bin/env python3
"""EpiClaw Wastewater Surveillance -- WBE concentration normalization and trend analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "wastewater-surveillance"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_by_pmmov(
    raw: np.ndarray,
    pmmov: np.ndarray,

):
    safe = np.where(pmmov <= 0, np.nan, pmmov)
    return raw / safe
def normalize_by_flow(
    raw: np.ndarray,
    flow: np.ndarray,

):
    safe = np.where(flow <= 0, np.nan, flow)
    return raw / safe
# ---------------------------------------------------------------------------
# Rolling average
# ---------------------------------------------------------------------------

def rolling_mean(arr: np.ndarray, window: int = 7) -> np.ndarray:
    """Compute centered rolling mean with edge padding."""
    result = np.full_like(arr, np.nan, dtype=float)
    half = window // 2
    for i in range(len(arr)):
        start = max(0, i - half)
        end = min(len(arr), i + half + 1)
        result[i] = float(np.nanmean(arr[start:end]))
    return result


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Pearson r between two arrays, ignoring NaN pairs."""
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 2:
        return float("nan")
    xm = x[mask] - np.mean(x[mask])
    ym = y[mask] - np.mean(y[mask])
    denom = np.sqrt(np.sum(xm ** 2) * np.sum(ym ** 2))
    if denom == 0:
        return float("nan")
    return float(np.sum(xm * ym) / denom)


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _data_table(
    raw: np.ndarray,
    normalized: np.ndarray,
    rolling: np.ndarray,
    clinical: np.ndarray,

):
    lines = [
        "| Week | Raw | Normalized | Rolling Avg | Clinical Cases |",
        "|---|---|---|---|---|",
    ]
    for idx, (r, n, roll, case) in enumerate(zip(raw, normalized, rolling, clinical), start=1):
        lines.append(f"| {idx} | {r:.2f} | {n:.4f} | {roll:.4f} | {case:.0f} |")
    return lines
def generate_report(
    raw: np.ndarray,
    normalized: np.ndarray,
    rolling: np.ndarray,
    clinical: np.ndarray,
    correlation: float,
    peak_week: int,
    pathogen: str,
    normalization: str,
    output_path: Path,

):
    header = generate_report_header(
        title="Wastewater Surveillance Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Pathogen": pathogen, "Normalization": normalization, "Version": VERSION},
    )
    lines = [
        "## Summary",
        "",
        f"- Weeks analysed: `{len(raw)}`",
        f"- Pearson correlation with clinical cases: `{correlation:.4f}`",
        f"- Peak wastewater signal week: `{peak_week}`",
        "",
        "## Weekly Measurements",
        "",
        *_data_table(raw, normalized, rolling, clinical),
        "",
        generate_report_footer(),
    ]
    output_path.write_text(header + "\n".join(lines), encoding="utf-8")
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wastewater_surveillance",
        description="EpiClaw Wastewater Surveillance -- WBE normalization and trend analysis.",
    )
    parser.add_argument("--input", type=str, default=None, help="CSV with columns: week, raw_concentration, pmmov, clinical_cases")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--pathogen", type=str, default="SARS-CoV-2", help="Pathogen name (default: SARS-CoV-2)")
    parser.add_argument(
        "--normalization",
        type=str,
        choices=["pmmov", "flow", "none"],
        default="pmmov",
        help="Normalization method (default: pmmov)",
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demo data")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.demo or args.input is None:
        weeks = np.arange(16, dtype=float)
        raw = np.array([120, 115, 130, 135, 142, 150, 148, 155, 170, 182, 195, 210, 205, 198, 190, 175], dtype=float)
        pmmov = 50 + 5 * np.sin(weeks / 3.0)
        flow = 100 + 10 * np.cos(weeks / 4.0)
        clinical = np.array([15, 14, 16, 18, 20, 22, 25, 28, 31, 35, 39, 42, 40, 37, 30, 26], dtype=float)
        print(f"[info] Using built-in demo data ({len(raw)} weeks).")
    else:
        import csv

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[error] Input file not found: {input_path}")
            sys.exit(1)
        raw_list, pmmov_list, flow_list, clinical_list = [], [], [], []
        with open(input_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_list.append(float(row["raw_concentration"]))
                pmmov_list.append(float(row.get("pmmov", 1.0)))
                flow_list.append(float(row.get("flow", 1.0)))
                clinical_list.append(float(row.get("clinical_cases", 0.0)))
        raw = np.array(raw_list)
        pmmov = np.array(pmmov_list)
        flow = np.array(flow_list)
        clinical = np.array(clinical_list)
        print(f"[info] Loaded {len(raw)} weeks from {input_path}.")

    # Normalization
    print(f"[info] Applying {args.normalization} normalization ...")
    if args.normalization == "pmmov":
        normalized = normalize_by_pmmov(raw, pmmov)
    elif args.normalization == "flow":
        normalized = normalize_by_flow(raw, flow)
    else:
        normalized = raw.copy().astype(float)

    # 7-day rolling average
    print("[info] Computing 7-week rolling average ...")
    rolling = rolling_mean(normalized, window=7)

    # Correlation with clinical cases
    correlation = pearson_correlation(normalized, clinical)
    print(f"[info] Pearson correlation with clinical cases: {correlation:.4f}")

    # Peak week
    peak_week = int(np.nanargmax(normalized)) + 1
    print(f"[info] Peak WBE signal at week {peak_week}.")

    # Report
    report_path = out / "report.md"
    generate_report(raw, normalized, rolling, clinical, correlation, peak_week, args.pathogen, args.normalization, report_path)
    print(f"[info] Report written to {report_path}")

    # result.json
    write_result_json(
        output_dir=out,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "weeks_analyzed": int(len(raw)),
            "pathogen": args.pathogen,
            "normalization": args.normalization,
            "correlation_with_cases": round(float(correlation), 4) if not np.isnan(correlation) else None,
            "peak_week": peak_week,
        },
        data={
            "raw_concentration": [round(float(v), 4) for v in raw],
            "normalized": [round(float(v), 6) if not np.isnan(v) else None for v in normalized],
            "rolling_avg": [round(float(v), 6) if not np.isnan(v) else None for v in rolling],
            "clinical_cases": [float(v) for v in clinical],
        },
    )
    print(f"[info] Done. Report: {out}/report.md")


if __name__ == "__main__":
    main()
