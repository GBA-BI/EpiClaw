#!/usr/bin/env python3
"""EpiClaw AMR Surveillance -- AMR gene detection and surveillance reporting."""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from collections import Counter, defaultdict
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "amr-surveillance"
FASTA_EXTENSIONS = {".fa", ".fna", ".fasta", ".fas", ".ffn", ".faa"}
RESISTANCE_CLASS_MAP = {
    "beta-lactam": "beta-lactam",
    "cephalosporin": "beta-lactam",
    "carbapenem": "beta-lactam",
    "penam": "beta-lactam",
    "monobactam": "beta-lactam",
    "aminoglycoside": "aminoglycoside",
    "fluoroquinolone": "fluoroquinolone",
    "quinolone": "fluoroquinolone",
    "macrolide": "macrolide",
    "lincosamide": "macrolide",
    "streptogramin": "macrolide",
    "tetracycline": "tetracycline",
    "glycopeptide": "glycopeptide",
    "sulfonamide": "folate-pathway antagonist",
    "trimethoprim": "folate-pathway antagonist",
    "fosfomycin": "fosfomycin",
    "rifampin": "rifamycin",
    "rifamycin": "rifamycin",
    "phenicol": "phenicol",
    "colistin": "polymyxin",
    "polymyxin": "polymyxin",
}
DEMO_AMR_ROWS = [
    {"isolate": "iso01", "gene": "blaCTX-M-15", "subtype": "ESBL", "class": "beta-lactam", "method": "demo", "identity": "99.2", "coverage": "100"},
    {"isolate": "iso01", "gene": "aac(6')-Ib", "subtype": "", "class": "aminoglycoside", "method": "demo", "identity": "98.1", "coverage": "97"},
    {"isolate": "iso02", "gene": "tet(A)", "subtype": "", "class": "tetracycline", "method": "demo", "identity": "99.0", "coverage": "95"},
]


def _collect_fasta_inputs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in FASTA_EXTENSIONS:
            raise RuntimeError(f"AMR surveillance requires FASTA input, got: {input_path.name}")
        return [input_path]

    fasta_files = sorted(
        p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in FASTA_EXTENSIONS
    )
    if not fasta_files:
        raise RuntimeError(f"No FASTA files found under: {input_path}")
    return fasta_files


def _run_command(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{message}")
    return proc


def _resolve_tool(tool: str) -> tuple[str, str]:
    amr_bin = shutil.which("amrfinder") or shutil.which("amrfinderplus")
    resfinder_bin = shutil.which("run_resfinder.py") or shutil.which("resfinder")
    if tool == "auto":
        if amr_bin:
            return "amrfinder", amr_bin
        if resfinder_bin:
            return "resfinder", resfinder_bin
        raise RuntimeError("No supported AMR caller found on PATH (amrfinder/amrfinderplus or run_resfinder.py/resfinder).")
    if tool == "amrfinder":
        if not amr_bin:
            raise RuntimeError("Requested tool 'amrfinder' but amrfinder/amrfinderplus is not available on PATH.")
        return "amrfinder", amr_bin
    if tool == "resfinder":
        if not resfinder_bin:
            raise RuntimeError("Requested tool 'resfinder' but run_resfinder.py/resfinder is not available on PATH.")
        return "resfinder", resfinder_bin
    raise RuntimeError(f"Unsupported tool: {tool}")


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _first_present(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _normalize_class(raw_value: str) -> str:
    text = raw_value.strip().lower()
    if not text:
        return "unknown"
    for needle, normalized in RESISTANCE_CLASS_MAP.items():
        if needle in text:
            return normalized
    return raw_value.strip()


def _run_amrfinder(
    fasta_files: list[Path],
    output_dir: Path,
    organism: str | None,
    point_mutations: bool,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    binary = shutil.which("amrfinder") or shutil.which("amrfinderplus")
    if not binary:
        raise RuntimeError("amrfinder/amrfinderplus not found on PATH.")

    results_dir = output_dir / "amrfinder"
    results_dir.mkdir(parents=True, exist_ok=True)
    combined_rows: list[dict[str, str]] = []

    version_proc = subprocess.run([binary, "--version"], capture_output=True, text=True)
    version_line = (version_proc.stdout.strip() or version_proc.stderr.strip()).splitlines()
    tool_info = {
        "tool": "amrfinder",
        "binary": binary,
        "version": version_line[0] if version_line else "unknown",
    }

    for fasta in fasta_files:
        isolate = fasta.stem
        out_tsv = results_dir / f"{isolate}.tsv"
        cmd = [binary, "-n", str(fasta), "-o", str(out_tsv)]
        if organism:
            cmd.extend(["-O", organism])
        if point_mutations:
            cmd.append("--plus")
        _run_command(cmd)
        if not out_tsv.exists():
            raise RuntimeError(f"AMRFinder completed without expected output: {out_tsv}")
        for row in _read_tsv(out_tsv):
            row["isolate"] = isolate
            combined_rows.append(row)

    return combined_rows, tool_info


def _find_resfinder_tab(output_dir: Path) -> Path | None:
    candidates = sorted(output_dir.rglob("*.txt")) + sorted(output_dir.rglob("*.tsv"))
    for candidate in candidates:
        try:
            header = candidate.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        except IndexError:
            continue
        if "Resistance gene" in header or "Resistance gene" in candidate.name:
            return candidate
    return None


def _run_resfinder(
    fasta_files: list[Path],
    output_dir: Path,
    point_mutations: bool,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    binary = shutil.which("run_resfinder.py") or shutil.which("resfinder")
    if not binary:
        raise RuntimeError("run_resfinder.py/resfinder not found on PATH.")

    results_dir = output_dir / "resfinder"
    results_dir.mkdir(parents=True, exist_ok=True)
    combined_rows: list[dict[str, str]] = []

    version_proc = subprocess.run([binary, "--help"], capture_output=True, text=True)
    help_text = version_proc.stdout or version_proc.stderr or ""
    tool_info = {
        "tool": "resfinder",
        "binary": binary,
        "version": help_text.splitlines()[0] if help_text.splitlines() else "unknown",
    }

    for fasta in fasta_files:
        isolate = fasta.stem
        isolate_dir = results_dir / isolate
        isolate_dir.mkdir(parents=True, exist_ok=True)
        cmd = [binary, "-ifa", str(fasta), "-o", str(isolate_dir)]
        if point_mutations:
            cmd.append("--point")
        _run_command(cmd)
        result_tab = _find_resfinder_tab(isolate_dir)
        if result_tab is None:
            raise RuntimeError(f"ResFinder finished but no tabular gene report was found in: {isolate_dir}")
        delimiter = "\t" if result_tab.suffix == ".tsv" else None
        with result_tab.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter or "\t")
            rows = list(reader)
        if not rows:
            continue
        for row in rows:
            row["isolate"] = isolate
            combined_rows.append(row)

    return combined_rows, tool_info


def _build_amr_summary(rows: list[dict[str, str]]) -> tuple[dict, dict]:
    isolates: dict[str, list[dict[str, str]]] = defaultdict(list)
    class_counts: Counter[str] = Counter()
    gene_counts: Counter[str] = Counter()
    isolate_classes: dict[str, set[str]] = defaultdict(set)

    normalized_hits: list[dict[str, str]] = []
    for row in rows:
        isolate = row.get("isolate", "unknown")
        gene = _first_present(row, ["Gene symbol", "Gene symbol(s)", "Gene", "Resistance gene", "gene"])
        subtype = _first_present(row, ["Subtype", "Element subtype", "Accession of closest sequence"])
        amr_class = _normalize_class(
            _first_present(
                row,
                [
                    "Class",
                    "Subclass",
                    "Drug Class",
                    "Antimicrobial class",
                    "Phenotype",
                    "Class of resistance",
                ],
            )
        )
        method = _first_present(row, ["Method", "Element type", "Element subtype", "Sequence name"])
        identity = _first_present(row, ["% Identity to reference sequence", "Identity", "%Identity"])
        coverage = _first_present(row, ["% Coverage of reference sequence", "Alignment Length/Gene Length", "Coverage"])
        record = {
            "isolate": isolate,
            "gene": gene or subtype or "unknown",
            "subtype": subtype,
            "class": amr_class,
            "method": method,
            "identity": identity,
            "coverage": coverage,
        }
        normalized_hits.append(record)
        isolates[isolate].append(record)
        gene_counts[record["gene"]] += 1
        class_counts[record["class"]] += 1
        if record["class"] != "unknown":
            isolate_classes[isolate].add(record["class"])

    isolate_summary: list[dict[str, object]] = []
    mdr_counts = {"MDR": 0, "non-MDR": 0}
    for isolate, hits in sorted(isolates.items()):
        classes = sorted(isolate_classes.get(isolate, set()))
        resistance_category_count = len(classes)
        classification = "MDR" if resistance_category_count >= 3 else "non-MDR"
        mdr_counts[classification] += 1
        isolate_summary.append(
            {
                "isolate": isolate,
                "n_hits": len(hits),
                "resistance_classes": classes,
                "classification": classification,
            }
        )

    summary = {
        "n_isolates": len(isolates),
        "n_detected_hits": len(normalized_hits),
        "top_resistance_genes": [{"gene": gene, "count": count} for gene, count in gene_counts.most_common(10)],
        "resistance_class_counts": dict(class_counts),
        "mdr_summary": mdr_counts,
    }
    data = {
        "hits": normalized_hits,
        "isolates": isolate_summary,
    }
    return summary, data


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_report(output_path: Path, summary: dict, data: dict, tool_info: dict) -> None:
    header = generate_report_header(
        title="AMR Surveillance Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Tool": tool_info["tool"], "Version": VERSION, "CLI": tool_info.get("version", "unknown")},
    )
    lines = [
        "## Cohort Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Isolates processed | {summary['n_isolates']} |",
        f"| AMR hits detected | {summary['n_detected_hits']} |",
        f"| MDR isolates | {summary['mdr_summary'].get('MDR', 0)} |",
        f"| Non-MDR isolates | {summary['mdr_summary'].get('non-MDR', 0)} |",
        "",
        "## Top Resistance Genes",
        "",
        "| Gene | Count |",
        "|---|---|",
    ]
    for row in summary["top_resistance_genes"]:
        lines.append(f"| {row['gene']} | {row['count']} |")
    lines.extend([
        "",
        "## Resistance Classes",
        "",
        "| Class | Count |",
        "|---|---|",
    ])
    for klass, count in sorted(summary["resistance_class_counts"].items()):
        lines.append(f"| {klass} | {count} |")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="amr_surveillance",
        description="EpiClaw AMR Surveillance -- AMRFinder/ResFinder execution chain.",
    )
    parser.add_argument("--input", default=None, help="Genome FASTA file or directory of FASTA files")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo AMR cohort")
    parser.add_argument("--tool", choices=["auto", "amrfinder", "resfinder"], default="auto")
    parser.add_argument("--organism", default=None, help="Organism label for AMRFinder when supported")
    parser.add_argument("--point-mutations", action="store_true", help="Enable point mutation calling when supported")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        rows = DEMO_AMR_ROWS
        tool_info = {"tool": "amrfinder (simulated)", "version": "demo"}
        fasta_files = []
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        fasta_files = _collect_fasta_inputs(input_path)
        selected_tool, _binary = _resolve_tool(args.tool)
        if selected_tool == "amrfinder":
            rows, tool_info = _run_amrfinder(fasta_files, output_dir, args.organism, args.point_mutations)
        else:
            rows, tool_info = _run_resfinder(fasta_files, output_dir, args.point_mutations)

    summary, data = _build_amr_summary(rows)

    hits_csv = output_dir / "resistance_gene_table.csv"
    isolate_csv = output_dir / "mdr_classification.csv"
    _write_csv(hits_csv, data["hits"], ["isolate", "gene", "subtype", "class", "method", "identity", "coverage"])
    _write_csv(isolate_csv, data["isolates"], ["isolate", "n_hits", "resistance_classes", "classification"])

    data.update(
        {
            "input_files": [str(path) for path in fasta_files],
            "tool_info": tool_info,
            "resistance_gene_table": str(hits_csv),
            "mdr_classification": str(isolate_csv),
        }
    )

    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data, tool_info)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)

    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
