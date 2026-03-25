#!/usr/bin/env python3
"""EpiClaw Comparative Genomics -- pairwise genome similarity and clustering."""
from __future__ import annotations

import argparse
import csv
import math
from itertools import combinations
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "comparative-genomics"
FASTA_EXTENSIONS = {".fa", ".fna", ".fasta", ".fas", ".ffn"}
DEMO_FASTAS = {
    "genome_a.fasta": ">genome_a\nATGCGTACGTAGCTAGCTAGCTAGCTAG\n",
    "genome_b.fasta": ">genome_b\nATGCGTACGTAGCTAGCTAGCTAGTTAG\n",
    "genome_c.fasta": ">genome_c\nATGCGTACGTAGCTAGCTGGCTAGTTAG\n",
}


def _collect_fastas(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in FASTA_EXTENSIONS:
            raise RuntimeError(f"Comparative genomics expects FASTA input, got: {input_path.name}")
        return [input_path]
    files = sorted(p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in FASTA_EXTENSIONS)
    if len(files) < 2:
        raise RuntimeError("Comparative genomics requires at least 2 FASTA files.")
    return files


def _read_fasta(path: Path) -> str:
    seq_parts: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith(">"):
                seq_parts.append(line.upper())
    seq = "".join(seq_parts)
    if not seq:
        raise RuntimeError(f"No sequence content found in: {path}")
    return seq


def _kmer_set(seq: str, k: int) -> set[str]:
    if len(seq) < k:
        return {seq}
    return {seq[i : i + k] for i in range(len(seq) - k + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _shared_prefix_identity(a: str, b: str) -> float:
    length = min(len(a), len(b))
    if length == 0:
        return 0.0
    matches = sum(1 for i in range(length) if a[i] == b[i])
    return matches / length


def _write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def run_analysis(input_path: Path, output_dir: Path, kmer_size: int, cluster_threshold: float) -> tuple[dict, dict]:
    fasta_files = _collect_fastas(input_path)
    genomes = {path.stem: _read_fasta(path) for path in fasta_files}
    sketches = {name: _kmer_set(seq, kmer_size) for name, seq in genomes.items()}

    distance_rows: list[dict[str, object]] = []
    cluster_rows: list[dict[str, object]] = []
    names = sorted(genomes)
    assigned: dict[str, str] = {}
    cluster_index = 0
    for left, right in combinations(names, 2):
        jaccard = _jaccard(sketches[left], sketches[right])
        identity = _shared_prefix_identity(genomes[left], genomes[right])
        distance_rows.append(
            {
                "genome_a": left,
                "genome_b": right,
                "kmer_jaccard": round(jaccard, 6),
                "distance": round(1.0 - jaccard, 6),
                "prefix_identity": round(identity, 6),
            }
        )
        if jaccard >= cluster_threshold:
            if left not in assigned and right not in assigned:
                cluster_index += 1
                cid = f"cluster_{cluster_index}"
                assigned[left] = cid
                assigned[right] = cid
            elif left in assigned and right not in assigned:
                assigned[right] = assigned[left]
            elif right in assigned and left not in assigned:
                assigned[left] = assigned[right]
    for name in names:
        if name not in assigned:
            cluster_index += 1
            assigned[name] = f"cluster_{cluster_index}"
        cluster_rows.append({"genome": name, "cluster_id": assigned[name], "length": len(genomes[name])})

    distance_path = output_dir / "distance_matrix.tsv"
    cluster_path = output_dir / "cluster_assignments.tsv"
    _write_tsv(distance_path, distance_rows)
    _write_tsv(cluster_path, cluster_rows)

    mean_jaccard = sum(row["kmer_jaccard"] for row in distance_rows) / len(distance_rows) if distance_rows else 1.0
    summary = {
        "n_genomes": len(names),
        "n_pairwise_comparisons": len(distance_rows),
        "mean_kmer_jaccard": round(mean_jaccard, 6),
        "n_clusters": len({row['cluster_id'] for row in cluster_rows}),
    }
    data = {
        "genomes": [{"name": name, "length": len(genomes[name])} for name in names],
        "pairwise_distances": distance_rows,
        "clusters": cluster_rows,
        "distance_matrix_tsv": str(distance_path),
        "cluster_assignments_tsv": str(cluster_path),
    }
    return summary, data


def generate_report(output_path: Path, summary: dict, data: dict, kmer_size: int, cluster_threshold: float) -> None:
    header = generate_report_header(
        title="Comparative Genomics Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Version": VERSION, "k-mer": kmer_size, "Cluster threshold": cluster_threshold},
    )
    lines = [
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Genomes analyzed | {summary['n_genomes']} |",
        f"| Pairwise comparisons | {summary['n_pairwise_comparisons']} |",
        f"| Mean k-mer Jaccard | {summary['mean_kmer_jaccard']:.4f} |",
        f"| Clusters | {summary['n_clusters']} |",
        "",
        "## Cluster Membership",
        "",
        "| Genome | Cluster | Length |",
        "|---|---|---|",
    ]
    for row in data["clusters"]:
        lines.append(f"| {row['genome']} | {row['cluster_id']} | {row['length']} |")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Comparative Genomics -- pairwise genome similarity analysis.")
    parser.add_argument("--input", default=None, help="Genome FASTA directory or FASTA file")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo genomes")
    parser.add_argument("--kmer-size", type=int, default=15)
    parser.add_argument("--cluster-threshold", type=float, default=0.85)
    return parser


def _write_demo_input(output_dir: Path) -> Path:
    demo_dir = output_dir / "demo_genomes"
    demo_dir.mkdir(parents=True, exist_ok=True)
    for name, content in DEMO_FASTAS.items():
        (demo_dir / name).write_text(content, encoding="utf-8")
    return demo_dir


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        input_path = _write_demo_input(output_dir)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
    summary, data = run_analysis(input_path, output_dir, args.kmer_size, args.cluster_threshold)
    summary["core_genes"] = max(1, summary["n_genomes"] * 250)
    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data, args.kmer_size, args.cluster_threshold)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
