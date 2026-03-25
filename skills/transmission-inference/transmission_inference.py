#!/usr/bin/env python3
"""EpiClaw Transmission Inference -- pairwise genomic-temporal link scoring."""
from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from itertools import permutations
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "transmission-inference"
DEMO_FASTA = """>case01
ATGCTAGCTAGCTAACGTTACGAT
>case02
ATGCTAGCTAGCTAACGTTACGTT
>case03
ATGCTAGCTAGCTAACGTCACGTT
>case04
ATGCTAGCTAGCTAACGTCACGTA
"""
DEMO_LINELIST = [
    {"case_id": "case01", "symptom_onset_date": "2025-01-02"},
    {"case_id": "case02", "symptom_onset_date": "2025-01-05"},
    {"case_id": "case03", "symptom_onset_date": "2025-01-08"},
    {"case_id": "case04", "symptom_onset_date": "2025-01-12"},
]


def _read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, list[str]] = {}
    current = None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                current = line[1:].split()[0]
                records[current] = []
            elif current is not None:
                records[current].append(line.upper())
    return {name: "".join(parts) for name, parts in records.items()}


def _parse_date(text: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m"):
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt in {"%Y-%m", "%Y/%m"}:
                parsed = parsed.replace(day=1)
            return parsed
        except ValueError:
            continue
    raise RuntimeError(f"Unrecognized date format: {text}")


def _distance(a: str, b: str) -> int:
    length = min(len(a), len(b))
    return sum(1 for i in range(length) if a[i] != b[i]) + abs(len(a) - len(b))


def run_analysis(fasta_path: Path, linelist_path: Path, mean_gen_time: float) -> tuple[dict, dict]:
    seqs = _read_fasta(fasta_path)
    if not seqs:
        raise RuntimeError("Transmission inference FASTA is empty.")
    with linelist_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("Linelist is empty.")
    meta = {}
    for row in rows:
        case_id = row.get("case_id") or row.get("sample_id") or row.get("id")
        if not case_id:
            continue
        date_text = row.get("symptom_onset_date") or row.get("collection_date")
        if not date_text:
            raise RuntimeError(f"Missing onset/collection date for case: {case_id}")
        meta[case_id] = _parse_date(date_text)
    common = sorted(set(seqs) & set(meta))
    if len(common) < 2:
        raise RuntimeError("Need at least 2 overlapping case IDs between FASTA headers and linelist.")

    links: list[dict[str, object]] = []
    for donor, recipient in permutations(common, 2):
        delta_days = (meta[recipient] - meta[donor]).days
        if delta_days <= 0:
            continue
        dist = _distance(seqs[donor], seqs[recipient])
        score = math.exp(-dist / 2.0) * math.exp(-abs(delta_days - mean_gen_time) / max(mean_gen_time, 1e-6))
        links.append(
            {
                "donor": donor,
                "recipient": recipient,
                "genetic_distance": dist,
                "serial_interval_days": delta_days,
                "score": round(score, 8),
            }
        )
    links.sort(key=lambda row: row["score"], reverse=True)
    best_by_recipient: dict[str, dict[str, object]] = {}
    for row in links:
        best_by_recipient.setdefault(str(row["recipient"]), row)
    best_links = list(best_by_recipient.values())
    summary = {
        "n_cases": len(common),
        "n_candidate_links": len(links),
        "mean_generation_time": mean_gen_time,
        "n_best_links": len(best_links),
    }
    data = {"candidate_links": links, "best_links": best_links, "cases": common}
    return summary, data


def _write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def generate_report(output_path: Path, summary: dict, data: dict) -> None:
    header = generate_report_header(title="Transmission Inference Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION})
    lines = [
        "## Pairwise Transmission Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Cases | {summary['n_cases']} |",
        f"| Candidate links | {summary['n_candidate_links']} |",
        f"| Mean generation time | {summary['mean_generation_time']} |",
        f"| Best links retained | {summary['n_best_links']} |",
        "",
        "## Top Ranked Links",
        "",
        "| Donor | Recipient | Genetic distance | Interval (days) | Score |",
        "|---|---|---|---|---|",
    ]
    for row in data["best_links"][:20]:
        lines.append(f"| {row['donor']} | {row['recipient']} | {row['genetic_distance']} | {row['serial_interval_days']} | {row['score']} |")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Transmission Inference -- pairwise genomic-temporal scoring.")
    parser.add_argument("--input", default=None, help="Alignment FASTA")
    parser.add_argument("--linelist", default=None, help="Linelist CSV with case_id and dates")
    parser.add_argument("--output", required=True)
    parser.add_argument("--demo", action="store_true", help="Run built-in demo outbreak cluster")
    parser.add_argument("--mean-gen-time", type=float, default=5.0)
    return parser


def _write_demo_inputs(output_dir: Path) -> tuple[Path, Path]:
    fasta_path = output_dir / "demo_alignment.fasta"
    fasta_path.write_text(DEMO_FASTA, encoding="utf-8")
    linelist_path = output_dir / "demo_linelist.csv"
    with linelist_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "symptom_onset_date"])
        writer.writeheader()
        writer.writerows(DEMO_LINELIST)
    return fasta_path, linelist_path


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input or not args.linelist:
        fasta_path, linelist_path = _write_demo_inputs(output_dir)
    else:
        fasta_path = Path(args.input)
        linelist_path = Path(args.linelist)
        if not fasta_path.exists():
            raise SystemExit(f"[error] Input FASTA not found: {fasta_path}")
        if not linelist_path.exists():
            raise SystemExit(f"[error] Linelist not found: {linelist_path}")
    summary, data = run_analysis(fasta_path, linelist_path, args.mean_gen_time)
    candidate_tsv = output_dir / "candidate_links.tsv"
    best_tsv = output_dir / "most_likely_network.tsv"
    _write_tsv(candidate_tsv, data["candidate_links"])
    _write_tsv(best_tsv, data["best_links"])
    data["candidate_links_tsv"] = str(candidate_tsv)
    data["best_links_tsv"] = str(best_tsv)
    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
