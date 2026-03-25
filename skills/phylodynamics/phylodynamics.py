#!/usr/bin/env python3
"""EpiClaw Phylodynamics -- alignment, tree inference, and temporal dating pipeline."""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from datetime import date, datetime
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "phylodynamics"
FASTA_EXTENSIONS = {".fa", ".fna", ".fasta", ".fas", ".aln"}
TREE_EXTENSIONS = {".nwk", ".tree", ".newick"}
DEMO_ALIGNMENT = """>sample01|2025-01-01
ATGCGTACGTAGCTAGCTAGCTAG
>sample02|2025-01-08
ATGCGTACGTAGCTAGCTAGCTAA
>sample03|2025-01-15
ATGCGTACGTAGCTAGCTAGTTAA
"""
DEMO_TREE = "(sample01:0.01,sample02:0.02,sample03:0.03);"


def _run_command(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{message}")
    return proc


def _resolve_input_bundle(input_path: Path, tree: str | None, dates: str | None) -> tuple[Path, Path | None, Path | None]:
    if input_path.is_file():
        suffix = input_path.suffix.lower()
        if suffix not in FASTA_EXTENSIONS:
            raise RuntimeError(f"Phylodynamics requires FASTA/alignment input, got: {input_path.name}")
        tree_path = Path(tree) if tree else None
        dates_path = Path(dates) if dates else None
        return input_path, tree_path, dates_path

    fasta = None
    tree_path = Path(tree) if tree else None
    dates_path = Path(dates) if dates else None
    for candidate in sorted(input_path.iterdir()):
        if candidate.is_file() and candidate.suffix.lower() in FASTA_EXTENSIONS and fasta is None:
            fasta = candidate
        elif candidate.is_file() and candidate.suffix.lower() in TREE_EXTENSIONS and tree_path is None:
            tree_path = candidate
        elif candidate.is_file() and candidate.suffix.lower() in {".csv", ".tsv"} and dates_path is None:
            dates_path = candidate
    if fasta is None:
        raise RuntimeError(f"No FASTA alignment found under: {input_path}")
    return fasta, tree_path, dates_path


def _parse_header_dates(alignment_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with alignment_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line.startswith(">"):
                continue
            header = line[1:]
            tokens = header.replace("|", " ").replace("/", " ").split()
            sample_date = next((token for token in tokens if _is_iso_date(token)), None)
            if sample_date:
                rows.append({"name": header.split()[0], "date": sample_date})
    return rows


def _is_iso_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _load_dates(date_path: Path | None, alignment_path: Path, output_dir: Path) -> Path:
    rows: list[dict[str, str]] = []
    if date_path:
        delimiter = "\t" if date_path.suffix.lower() == ".tsv" else ","
        with date_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            for row in reader:
                name = row.get("name") or row.get("strain") or row.get("sample")
                sample_date = row.get("date") or row.get("collection_date")
                if name and sample_date and _is_iso_date(sample_date):
                    rows.append({"name": name, "date": sample_date})
    else:
        rows = _parse_header_dates(alignment_path)

    if not rows:
        raise RuntimeError("No valid sample dates found. Provide --dates TSV/CSV or embed ISO dates in FASTA headers.")

    dates_tsv = output_dir / "dates.tsv"
    with dates_tsv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "date"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return dates_tsv


def _run_mafft(input_fasta: Path, output_dir: Path) -> Path:
    binary = shutil.which("mafft")
    if not binary:
        return input_fasta
    aln_path = output_dir / "alignment.fasta"
    proc = _run_command([binary, "--auto", str(input_fasta)])
    aln_path.write_text(proc.stdout, encoding="utf-8")
    return aln_path


def _run_iqtree(alignment_path: Path, output_dir: Path) -> Path:
    iqtree = shutil.which("iqtree2") or shutil.which("iqtree")
    if not iqtree:
        raise RuntimeError("No tree file provided and iqtree2/iqtree is not available on PATH.")
    run_dir = output_dir / "iqtree"
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [iqtree, "-s", str(alignment_path), "-nt", "AUTO", "-pre", str(run_dir / "phylo")]
    _run_command(cmd)
    treefile = run_dir / "phylo.treefile"
    if not treefile.exists():
        raise RuntimeError(f"IQ-TREE completed without expected tree output: {treefile}")
    return treefile


def _run_treetime(alignment_path: Path, tree_path: Path, dates_tsv: Path, output_dir: Path, clock_rate: str | None) -> dict:
    binary = shutil.which("treetime")
    if not binary:
        raise RuntimeError("treetime not found on PATH.")
    run_dir = output_dir / "treetime"
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [binary, "timetree", "--aln", str(alignment_path), "--tree", str(tree_path), "--dates", str(dates_tsv), "--outdir", str(run_dir)]
    if clock_rate:
        cmd.extend(["--clock-rate", str(clock_rate)])
    _run_command(cmd)

    candidate_tree = next((p for p in run_dir.rglob("*.nwk") if p.is_file()), None)
    if candidate_tree is None:
        candidate_tree = next((p for p in run_dir.rglob("*.nexus") if p.is_file()), None)
    if candidate_tree is None:
        raise RuntimeError("TreeTime completed but no dated tree output was found.")

    dates = _read_dates_table(dates_tsv)
    root_date = min(dates) if dates else None
    max_date = max(dates) if dates else None
    timespan_days = (max_date - root_date).days if root_date and max_date else None
    return {
        "tool": "treetime",
        "dated_tree": str(candidate_tree),
        "dates_tsv": str(dates_tsv),
        "date_range": {
            "start": root_date.isoformat() if root_date else None,
            "end": max_date.isoformat() if max_date else None,
            "span_days": timespan_days,
        },
    }


def _run_beast(alignment_path: Path, output_dir: Path) -> dict:
    binary = shutil.which("beast") or shutil.which("beast2")
    if not binary:
        raise RuntimeError("beast/beast2 not found on PATH.")
    raise RuntimeError(
        "BEAST2 execution requires an XML model configuration. Provide TreeTime via --tool treetime or extend this skill with a BEAUti XML template."
    )


def _read_dates_table(dates_tsv: Path) -> list[date]:
    dates: list[date] = []
    with dates_tsv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            sample_date = row.get("date")
            if sample_date and _is_iso_date(sample_date):
                dates.append(datetime.strptime(sample_date, "%Y-%m-%d").date())
    return dates


def generate_report(output_path: Path, summary: dict, data: dict) -> None:
    header = generate_report_header(
        title="Phylodynamics Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Tool": data["tool"], "Version": VERSION},
    )
    lines = [
        "## Temporal Phylogeny Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Sequences dated | {summary['n_dated_tips']} |",
        f"| Analysis tool | {data['tool']} |",
        f"| Date range start | {summary['date_range_start'] or 'unknown'} |",
        f"| Date range end | {summary['date_range_end'] or 'unknown'} |",
        f"| Sampling span (days) | {summary['sampling_span_days'] if summary['sampling_span_days'] is not None else 'unknown'} |",
        f"| Dated tree | {data['dated_tree']} |",
    ]
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phylodynamics",
        description="EpiClaw Phylodynamics -- MAFFT/IQ-TREE/TreeTime execution chain.",
    )
    parser.add_argument("--input", default=None, help="Alignment FASTA or directory containing FASTA/tree/dates files")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo alignment")
    parser.add_argument("--tool", choices=["auto", "treetime", "beast2"], default="auto")
    parser.add_argument("--tree", default=None, help="Optional rooted or unrooted Newick tree")
    parser.add_argument("--dates", default=None, help="Optional sample dates TSV/CSV with name,date columns")
    parser.add_argument("--clock-rate", default=None, help="Optional fixed clock rate for TreeTime")
    return parser


def _write_demo_bundle(output_dir: Path) -> tuple[Path, Path]:
    alignment = output_dir / "demo_alignment.fasta"
    alignment.write_text(DEMO_ALIGNMENT, encoding="utf-8")
    tree = output_dir / "demo_tree.nwk"
    tree.write_text(DEMO_TREE, encoding="utf-8")
    return alignment, tree


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        alignment_path, tree_path = _write_demo_bundle(output_dir)
        dates_tsv = _load_dates(None, alignment_path, output_dir)
        data = {
            "tool": "treetime (simulated)",
            "dated_tree": str(tree_path),
            "dates_tsv": str(dates_tsv),
            "date_range": {"start": "2025-01-01", "end": "2025-01-15", "span_days": 14},
        }
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        fasta_path, tree_path, date_path = _resolve_input_bundle(input_path, args.tree, args.dates)
        alignment_path = _run_mafft(fasta_path, output_dir)
        dates_tsv = _load_dates(date_path, alignment_path, output_dir)
        if tree_path is None:
            tree_path = _run_iqtree(alignment_path, output_dir)
        selected_tool = args.tool
        if selected_tool == "auto":
            selected_tool = "treetime"
        if selected_tool == "treetime":
            data = _run_treetime(alignment_path, tree_path, dates_tsv, output_dir, args.clock_rate)
        else:
            data = _run_beast(alignment_path, output_dir)

    date_values = _read_dates_table(dates_tsv)
    summary = {
        "n_sequences": len(date_values),
        "n_dated_tips": len(date_values),
        "date_range_start": min(date_values).isoformat() if date_values else None,
        "date_range_end": max(date_values).isoformat() if date_values else None,
        "sampling_span_days": (max(date_values) - min(date_values)).days if len(date_values) >= 2 else 0,
    }
    data.update(
        {
            "alignment": str(alignment_path),
            "input_tree": str(tree_path),
        }
    )

    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)

    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
