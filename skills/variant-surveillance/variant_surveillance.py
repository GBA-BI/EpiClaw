#!/usr/bin/env python3
"""EpiClaw Variant Surveillance -- viral lineage classification and prevalence tracking."""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from collections import Counter
import sys
from pathlib import Path

import numpy as np

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "variant-surveillance"

# ---------------------------------------------------------------------------
# Demo simulation
# ---------------------------------------------------------------------------

_DEMO_LINEAGE_COUNTS: dict[str, int] = {
    "B.1.1.7": 45,
    "B.1.617.2": 80,
    "BA.1": 60,
    "BA.2": 15,
}

_TREND_OPTIONS = ["increasing", "decreasing", "stable"]

# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    summary: dict,
    data: dict,
    tool_used: str,
    output_path: Path,

):
    header = generate_report_header(
        title="Variant Surveillance Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Tool": tool_used, "Version": VERSION},
    )
    lines = [
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Sequences classified | {summary['n_sequences']} |",
        f"| Lineages observed | {summary['n_lineages']} |",
        f"| Dominant lineage | {summary['dominant_lineage']} |",
        f"| Dominant prevalence (%) | {summary['dominant_prevalence']} |",
        "",
        "## Lineage Prevalence",
        "",
        "| Lineage | Count | Prevalence (%) | Trend |",
        "|---|---|---|---|",
    ]
    counts = data.get("lineage_counts", {})
    prevalence = data.get("lineage_prevalence", {})
    trends = data.get("trend", {})
    for lineage, count in counts.items():
        lines.append(f"| {lineage} | {count} | {prevalence.get(lineage, 0)} | {trends.get(lineage, 'stable')} |")
    output_path.write_text("\n".join([header] + lines + [generate_report_footer()]) + "\n", encoding="utf-8")
# ---------------------------------------------------------------------------
# Real-mode tool dispatch
# ---------------------------------------------------------------------------

def check_tool(tool: str) -> str | None:
    """Return resolved path to tool binary, or None."""
    return shutil.which(tool)


def _extract_lineage(row: dict[str, str]) -> str | None:
    for key in ("lineage", "pangoLineage", "Nextclade_pango", "clade"):
        value = row.get(key, "").strip()
        if value:
            return value
    return None


def _summarize_lineages(lineages: list[str], pathogen: str, country: str) -> tuple[dict, dict]:
    counts = dict(Counter(lineages))
    n_sequences = int(sum(counts.values()))
    if n_sequences == 0:
        raise RuntimeError("No classified sequences were returned by the selected tool.")

    lineage_prevalence = {
        lineage: round((count / n_sequences) * 100.0, 1)
        for lineage, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    }
    dominant_lineage = max(counts, key=counts.get)

    summary = {
        "n_sequences": n_sequences,
        "n_lineages": len(counts),
        "dominant_lineage": dominant_lineage,
        "dominant_prevalence": lineage_prevalence[dominant_lineage],
        "pathogen": pathogen,
        "country": country,
    }

    data = {
        "lineage_counts": counts,
        "lineage_prevalence": lineage_prevalence,
        "trend": {lineage: "stable" for lineage in counts},
        "immune_escape_scores": {lineage: 0.0 for lineage in counts},
    }
    return summary, data


def _run_pangolin(binary: str, input_path: Path, output_dir: Path) -> list[str]:
    output_csv = output_dir / "pangolin_lineages.csv"
    cmd = [binary, str(input_path), "--outfile", str(output_csv)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Pangolin failed: {proc.stderr.strip() or proc.stdout.strip()}")
    if not output_csv.exists():
        raise RuntimeError("Pangolin completed but no output CSV was produced.")

    lineages: list[str] = []
    with output_csv.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            lineage = _extract_lineage(row)
            if lineage:
                lineages.append(lineage)
    return lineages


def _run_nextclade(binary: str, input_path: Path, output_dir: Path, dataset: str) -> list[str]:
    output_csv = output_dir / "nextclade_results.csv"
    cmd = [
        binary,
        "run",
        "--input-dataset",
        dataset,
        "--input-fasta",
        str(input_path),
        "--output-csv",
        str(output_csv),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Nextclade failed. "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    if not output_csv.exists():
        raise RuntimeError("Nextclade completed but no output CSV was produced.")

    lineages: list[str] = []
    with output_csv.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            lineage = _extract_lineage(row)
            if lineage:
                lineages.append(lineage)
    return lineages


def execute_pipeline(
    args: argparse.Namespace,
    output_dir: Path,

):
    selected_tool = args.tool
    if selected_tool == "auto":
        selected_tool = "nextclade" if check_tool("nextclade") else "pangolin" if check_tool("pangolin") else ""
    if not selected_tool:
        raise RuntimeError("Neither nextclade nor pangolin is available.")
    if not args.input:
        raise RuntimeError("No input FASTA provided for real execution.")
    input_path = Path(args.input)
    if not input_path.exists():
        raise RuntimeError(f"Input FASTA not found: {input_path}")

    if selected_tool == "pangolin":
        binary = check_tool("pangolin")
        if not binary:
            raise RuntimeError("pangolin not found on PATH.")
        lineages = _run_pangolin(binary, input_path, output_dir)
        tool_used = "pangolin"
    else:
        binary = check_tool("nextclade")
        if not binary:
            raise RuntimeError("nextclade not found on PATH.")
        lineages = _run_nextclade(binary, input_path, output_dir, args.nextclade_dataset)
        tool_used = "nextclade"
    summary, data = _summarize_lineages(lineages, args.pathogen, args.country)
    return summary, data, tool_used
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="variant_surveillance",
        description="EpiClaw Variant Surveillance -- viral lineage classification and prevalence tracking.",
    )
    parser.add_argument("--input", type=str, default=None, help="Path to input FASTA file")
    parser.add_argument("--output", type=str, default="output/variant-surveillance", help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--pathogen", type=str, default="SARS-CoV-2", help="Pathogen name (default: SARS-CoV-2)")
    parser.add_argument("--country", type=str, default="Global", help="Country or region (default: Global)")
    parser.add_argument(
        "--tool",
        choices=["nextclade", "pangolin", "auto"],
        default="auto",
        help="Classification tool to use (default: auto)",
    )
    parser.add_argument(
        "--nextclade-dataset",
        type=str,
        default="sars-cov-2",
        help="Dataset slug passed to Nextclade (default: sars-cov-2)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    fallback_reason = ""
    tool_used = "nextclade (simulated)"
    if args.demo or not args.input:
        counts = dict(_DEMO_LINEAGE_COUNTS)
        n_sequences = int(sum(counts.values()))
        dominant = max(counts, key=counts.get)
        summary = {
            "n_sequences": n_sequences,
            "n_lineages": len(counts),
            "dominant_lineage": dominant,
            "dominant_prevalence": round((counts[dominant] / n_sequences) * 100.0, 1),
            "pathogen": args.pathogen,
            "country": args.country,
        }
        data = {
            "lineage_counts": counts,
            "lineage_prevalence": {
                lineage: round((count / n_sequences) * 100.0, 1) for lineage, count in counts.items()
            },
            "trend": {
                lineage: _TREND_OPTIONS[index % len(_TREND_OPTIONS)]
                for index, lineage in enumerate(counts)
            },
            "immune_escape_scores": {
                lineage: round(0.2 + index * 0.15, 2) for index, lineage in enumerate(counts)
            },
        }
    else:
        try:
            summary, data, tool_used = execute_pipeline(args, output_dir)
            print(f"[info] Running variant surveillance in REAL mode via {tool_used}.")
        except RuntimeError as err:
            fallback_reason = str(err)
            print(f"[warn] {fallback_reason}")
            counts = dict(_DEMO_LINEAGE_COUNTS)
            n_sequences = int(sum(counts.values()))
            dominant = max(counts, key=counts.get)
            summary = {
                "n_sequences": n_sequences,
                "n_lineages": len(counts),
                "dominant_lineage": dominant,
                "dominant_prevalence": round((counts[dominant] / n_sequences) * 100.0, 1),
                "pathogen": args.pathogen,
                "country": args.country,
            }
            data = {
                "lineage_counts": counts,
                "lineage_prevalence": {
                    lineage: round((count / n_sequences) * 100.0, 1) for lineage, count in counts.items()
                },
                "trend": {lineage: "stable" for lineage in counts},
                "immune_escape_scores": {lineage: 0.0 for lineage in counts},
                "fallback_reason": fallback_reason,
            }
            tool_used = f"{tool_used} (demo fallback)"

    print(f"[info] Classified {summary['n_sequences']} sequences into {summary['n_lineages']} lineages")
    print(f"[info] Dominant lineage: {summary['dominant_lineage']} ({summary['dominant_prevalence']}%)")

    report_path = output_dir / "report.md"
    generate_report(summary, data, tool_used=tool_used, output_path=report_path)
    print(f"[info] Report written to {report_path}")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary=summary,
        data=data,
    )
    print(f"[info] Result JSON written to {result_path}")


if __name__ == "__main__":
    main()
