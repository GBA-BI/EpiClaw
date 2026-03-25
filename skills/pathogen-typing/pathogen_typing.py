#!/usr/bin/env python3
"""EpiClaw Pathogen Typing -- MLST and cgMLST execution chain."""
from __future__ import annotations

import argparse
import csv
import math
import shutil
import subprocess
from collections import Counter
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "pathogen-typing"
FASTA_EXTENSIONS = {".fa", ".fna", ".fasta", ".fas", ".ffn"}
DEMO_FASTAS = {
    "iso01.fasta": ">iso01\nATGCGTACGTAGCTAGCTAGCTAGC\n",
    "iso02.fasta": ">iso02\nATGCGTACGTAGCTAGCTAGCTTGC\n",
    "iso03.fasta": ">iso03\nATGCGTACGTAGCTAGCTGGCTTGC\n",
}


def _collect_fasta_inputs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in FASTA_EXTENSIONS:
            raise RuntimeError(f"Pathogen typing requires FASTA input, got: {input_path.name}")
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


def _simpsons_diversity(values: list[str]) -> float:
    if len(values) <= 1:
        return 0.0
    counts = Counter(values)
    total = len(values)
    numerator = sum(count * (count - 1) for count in counts.values())
    denominator = total * (total - 1)
    return round(1.0 - (numerator / denominator), 4)


def _run_mlst(fasta_files: list[Path], output_dir: Path) -> tuple[dict, dict]:
    binary = shutil.which("mlst")
    if not binary:
        raise RuntimeError("mlst not found on PATH.")

    mlst_tsv = output_dir / "sequence_types.tsv"
    cmd = [binary, "--csv", *[str(path) for path in fasta_files]]
    proc = _run_command(cmd)
    mlst_tsv.write_text(proc.stdout, encoding="utf-8")

    rows: list[dict[str, object]] = []
    reader = csv.reader(proc.stdout.splitlines())
    header = next(reader, None)
    if not header:
        raise RuntimeError("mlst produced no output.")
    allele_profiles: list[dict[str, object]] = []
    st_values: list[str] = []
    for parts in reader:
        if len(parts) < 3:
            continue
        filename = parts[0]
        scheme = parts[1]
        sequence_type = parts[2]
        alleles = parts[3:]
        isolate = Path(filename).stem
        allele_profile = ":".join(alleles)
        rows.append(
            {
                "isolate": isolate,
                "scheme": scheme,
                "sequence_type": sequence_type,
                "allele_profile": allele_profile,
            }
        )
        allele_profiles.append(
            {
                "isolate": isolate,
                "scheme": scheme,
                **{f"locus_{idx + 1}": value for idx, value in enumerate(alleles)},
            }
        )
        st_values.append(sequence_type)

    if not rows:
        raise RuntimeError("mlst returned no isolate assignments.")

    st_counts = Counter(st_values)
    summary = {
        "n_isolates": len(rows),
        "n_sequence_types": len(st_counts),
        "top_sequence_types": [{"sequence_type": st, "count": count} for st, count in st_counts.most_common(10)],
        "simpsons_diversity_index": _simpsons_diversity(st_values),
    }
    data = {
        "tool": "mlst",
        "sequence_types": rows,
        "allele_profiles": allele_profiles,
        "sequence_type_table": str(mlst_tsv),
    }
    return summary, data


def _find_chewbbaca_profile(output_dir: Path) -> Path:
    candidates = sorted(output_dir.rglob("*results_alleles.tsv")) + sorted(output_dir.rglob("*alleles.tsv"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("chewBBACA completed but no allele profile table was found.")


def _run_cgmlst(
    input_path: Path,
    output_dir: Path,
    schema_dir: Path,
    threshold: int,
) -> tuple[dict, dict]:
    binary = shutil.which("chewBBACA") or shutil.which("chewBBACA.py")
    if not binary:
        raise RuntimeError("chewBBACA not found on PATH.")
    if not schema_dir.exists():
        raise RuntimeError(f"cgMLST schema directory not found: {schema_dir}")

    run_dir = output_dir / "chewbbaca"
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [binary, "AlleleCall", "-i", str(input_path), "-g", str(schema_dir), "-o", str(run_dir)]
    _run_command(cmd)

    profile_path = _find_chewbbaca_profile(run_dir)
    with profile_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    if not rows:
        raise RuntimeError("cgMLST profile table is empty.")

    isolate_profiles: list[dict[str, object]] = []
    isolates: list[str] = []
    profile_vectors: dict[str, dict[str, str]] = {}
    for row in rows:
        isolate = row.get("FILE") or row.get("Genome") or row.get("Sample") or "unknown"
        isolate = Path(isolate).stem
        normalized = {k: str(v).strip() for k, v in row.items() if k}
        normalized["isolate"] = isolate
        isolate_profiles.append(normalized)
        isolates.append(isolate)
        profile_vectors[isolate] = normalized

    loci = [key for key in isolate_profiles[0].keys() if key not in {"FILE", "Genome", "Sample", "isolate"}]
    distance_rows: list[dict[str, object]] = []
    cluster_rows: list[dict[str, object]] = []
    cluster_id = 0
    seen: set[str] = set()
    for isolate in isolates:
        if isolate in seen:
            continue
        cluster_id += 1
        members = [isolate]
        seen.add(isolate)
        for other in isolates:
            if other in seen or other == isolate:
                continue
            differences = 0
            for locus in loci:
                a = profile_vectors[isolate].get(locus, "")
                b = profile_vectors[other].get(locus, "")
                if not a or not b or a in {"INF-", "LNF"} or b in {"INF-", "LNF"}:
                    continue
                if a != b:
                    differences += 1
            distance_rows.append({"isolate_a": isolate, "isolate_b": other, "allele_differences": differences})
            if differences <= threshold:
                members.append(other)
                seen.add(other)
        for member in members:
            cluster_rows.append({"isolate": member, "cluster_id": f"cluster_{cluster_id}", "threshold": threshold})

    summary = {
        "n_isolates": len(isolates),
        "n_clusters": len({row['cluster_id'] for row in cluster_rows}),
        "cluster_threshold": threshold,
        "simpsons_diversity_index": _simpsons_diversity([row["cluster_id"] for row in cluster_rows]),
    }
    data = {
        "tool": "chewbbaca",
        "allele_profiles": isolate_profiles,
        "distance_matrix": distance_rows,
        "cluster_assignments": cluster_rows,
        "allele_profile_table": str(profile_path),
    }
    return summary, data


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def generate_report(output_path: Path, scheme: str, summary: dict, data: dict) -> None:
    header = generate_report_header(
        title="Pathogen Typing Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Scheme": scheme, "Tool": data["tool"], "Version": VERSION},
    )
    lines = [
        "## Typing Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Isolates processed | {summary['n_isolates']} |",
        f"| Diversity index | {summary['simpsons_diversity_index']} |",
    ]
    if scheme == "mlst":
        lines.extend(
            [
                f"| Unique sequence types | {summary['n_sequence_types']} |",
                "",
                "## Top Sequence Types",
                "",
                "| Sequence Type | Count |",
                "|---|---|",
            ]
        )
        for row in summary["top_sequence_types"]:
            lines.append(f"| {row['sequence_type']} | {row['count']} |")
    else:
        lines.extend(
            [
                f"| Clusters detected | {summary['n_clusters']} |",
                f"| Cluster threshold | {summary['cluster_threshold']} alleles |",
            ]
        )
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pathogen_typing",
        description="EpiClaw Pathogen Typing -- MLST and cgMLST execution chain.",
    )
    parser.add_argument("--input", default=None, help="Genome FASTA file or directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo isolates")
    parser.add_argument("--scheme", choices=["mlst", "cgmlst"], default="mlst")
    parser.add_argument("--threshold", type=int, default=10, help="cgMLST cluster threshold in allele differences")
    parser.add_argument("--schema-dir", default=None, help="cgMLST schema directory for chewBBACA")
    return parser


def _run_demo_mlst(output_dir: Path) -> tuple[dict, dict]:
    profiles = [
        {"isolate": "iso01", "scheme": "demo", "sequence_type": "42", "allele_profile": "1:4:7:2:3:8:5"},
        {"isolate": "iso02", "scheme": "demo", "sequence_type": "42", "allele_profile": "1:4:7:2:3:8:5"},
        {"isolate": "iso03", "scheme": "demo", "sequence_type": "108", "allele_profile": "2:4:7:9:3:8:5"},
    ]
    summary = {
        "n_isolates": 3,
        "n_sequence_types": 2,
        "top_sequence_types": [{"sequence_type": "42", "count": 2}, {"sequence_type": "108", "count": 1}],
        "simpsons_diversity_index": 0.6667,
    }
    data = {"tool": "mlst (simulated)", "sequence_types": profiles, "allele_profiles": profiles, "sequence_type_table": str(output_dir / "sequence_types.tsv")}
    return summary, data


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo or not args.input:
        summary, data = _run_demo_mlst(output_dir)
        _write_csv(output_dir / "allele_profiles.tsv", data["allele_profiles"])
    elif args.scheme == "mlst":
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        fasta_files = _collect_fasta_inputs(input_path)
        summary, data = _run_mlst(fasta_files, output_dir)
        _write_csv(output_dir / "allele_profiles.tsv", data["allele_profiles"])
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        if args.schema_dir is None:
            raise SystemExit("[error] --schema-dir is required for --scheme cgmlst")
        summary, data = _run_cgmlst(input_path, output_dir, Path(args.schema_dir), args.threshold)
        _write_csv(output_dir / "allele_profiles.tsv", data["allele_profiles"])
        _write_csv(output_dir / "distance_matrix.tsv", data["distance_matrix"])
        _write_csv(output_dir / "cluster_assignments.tsv", data["cluster_assignments"])

    report_path = output_dir / "report.md"
    generate_report(report_path, args.scheme, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)

    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
