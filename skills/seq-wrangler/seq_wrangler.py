#!/usr/bin/env python3
"""EpiClaw Seq Wrangler -- FASTQ inspection and pipeline planning."""
from __future__ import annotations

import argparse
import csv
import gzip
import shutil
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json
from repro import write_checksums_manifest, write_commands_script


VERSION = "0.1.0"
SKILL_NAME = "seq-wrangler"
FASTQ_SUFFIXES = (".fastq", ".fq", ".fastq.gz", ".fq.gz")


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def _collect_reads(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    reads = sorted(
        path for path in input_path.rglob("*")
        if path.is_file() and any(str(path).endswith(suffix) for suffix in FASTQ_SUFFIXES)
    )
    return reads


def _fastq_metrics(path: Path, max_reads: int = 200) -> dict[str, object]:
    read_count = 0
    total_bases = 0
    gc_bases = 0
    with _open_text(path) as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline().strip()
            handle.readline()
            handle.readline()
            if not sequence:
                continue
            read_count += 1
            total_bases += len(sequence)
            gc_bases += sum(1 for base in sequence.upper() if base in {"G", "C"})
            if read_count >= max_reads:
                break
    return {
        "sample": path.name,
        "n_reads_sampled": read_count,
        "mean_read_length": round(total_bases / max(read_count, 1), 2),
        "gc_content_pct": round(100.0 * gc_bases / max(total_bases, 1), 2),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 3),
    }


def _infer_pairs(reads: list[Path]) -> list[dict[str, str]]:
    grouped: dict[str, dict[str, str]] = {}
    for path in reads:
        name = path.name
        base = (
            name.replace("_R1", "")
            .replace("_R2", "")
            .replace("_1", "")
            .replace("_2", "")
            .replace(".fastq.gz", "")
            .replace(".fq.gz", "")
            .replace(".fastq", "")
            .replace(".fq", "")
        )
        group = grouped.setdefault(base, {"sample_id": base, "read1": "", "read2": ""})
        if "_R2" in name or "_2" in name:
            group["read2"] = str(path)
        else:
            group["read1"] = str(path)
    return list(grouped.values())


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Seq Wrangler")
    parser.add_argument("--input", type=str, help="FASTQ file or directory")
    parser.add_argument("--reference", type=str, help="Reference FASTA for alignment planning")
    parser.add_argument("--aligner", choices=["auto", "bwa", "bowtie2", "minimap2"], default="auto", help="Preferred aligner")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files: list[Path] = []
    if args.demo or not args.input:
        demo_dir = output_dir / "demo_reads"
        demo_dir.mkdir(parents=True, exist_ok=True)
        demo_read = demo_dir / "demo_R1.fastq"
        demo_read.write_text(
            "@read1\nACGTACGTACGT\n+\nFFFFFFFFFFFF\n@read2\nACGTTTGGCCAA\n+\nFFFFFFFFFFFF\n",
            encoding="utf-8",
        )
        reads = [demo_read]
        input_files = [demo_read]
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        reads = _collect_reads(input_path)
        input_files = reads
    if not reads:
        raise SystemExit("[error] No FASTQ files detected.")

    metrics = [_fastq_metrics(path) for path in reads]
    pairs = _infer_pairs(reads)
    aligner = args.aligner
    if aligner == "auto":
        aligner = "bwa" if shutil.which("bwa") else "bowtie2" if shutil.which("bowtie2") else "minimap2" if shutil.which("minimap2") else "bwa"

    alignment_rows = []
    commands = []
    for pair in pairs:
        read1 = pair["read1"]
        read2 = pair["read2"]
        sample_id = pair["sample_id"]
        command = ""
        if args.reference:
            if aligner == "bwa":
                command = f"bwa mem {args.reference} {read1}" + (f" {read2}" if read2 else "") + f" | samtools sort -o {sample_id}.sorted.bam"
            elif aligner == "bowtie2":
                command = f"bowtie2 -x {args.reference} -U {read1}" if not read2 else f"bowtie2 -x {args.reference} -1 {read1} -2 {read2}"
            else:
                command = f"minimap2 -a {args.reference} {read1}" + (f" {read2}" if read2 else "") + f" | samtools sort -o {sample_id}.sorted.bam"
        commands.append(command or f"# No reference provided for sample {sample_id}; QC-only workflow.")
        alignment_rows.append(
            {
                "sample_id": sample_id,
                "aligner": aligner,
                "reference": args.reference or "not-provided",
                "read1": read1,
                "read2": read2 or "",
                "planned_command": command or "qc-only",
            }
        )

    tables_dir = output_dir / "tables"
    _write_csv(tables_dir / "sample_qc.csv", metrics)
    _write_csv(tables_dir / "alignment_metrics.csv", alignment_rows)

    repro_dir = output_dir / "reproducibility"
    repro_dir.mkdir(parents=True, exist_ok=True)
    commands_file = write_commands_script(repro_dir / "commands.sh", commands)
    manifest = write_checksums_manifest(
        repro_dir,
        [commands_file, tables_dir / "sample_qc.csv", tables_dir / "alignment_metrics.csv"],
    )

    report_lines = [
        generate_report_header(
            title="Seq Wrangler Report",
            skill_name=SKILL_NAME,
            input_files=input_files,
            extra_metadata={"Aligner": aligner, "Version": VERSION},
        ),
        "## QC Summary",
        "",
        "| Sample | Reads Sampled | Mean Length | GC % | Size (MB) |",
        "|---|---|---|---|---|",
    ]
    for row in metrics:
        report_lines.append(
            f"| {row['sample']} | {row['n_reads_sampled']} | {row['mean_read_length']} | {row['gc_content_pct']} | {row['size_mb']} |"
        )
    report_lines.extend(
        [
            "",
            "## Alignment Plan",
            "",
            "| Sample | Aligner | Reference | Command |",
            "|---|---|---|---|",
        ]
    )
    for row in alignment_rows:
        report_lines.append(
            f"| {row['sample_id']} | {row['aligner']} | {row['reference']} | `{row['planned_command']}` |"
        )
    report_lines.append(generate_report_footer())
    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "n_samples": len(metrics),
            "paired_samples": sum(1 for row in alignment_rows if row["read2"]),
            "aligner": aligner,
            "reference_provided": bool(args.reference),
        },
        data={
            "qc_metrics": metrics,
            "alignment_plan": alignment_rows,
            "reproducibility_files": [str(commands_file), str(manifest)],
        },
    )
    write_checksums_manifest(repro_dir, [report_path, result_path, commands_file, manifest], output_name="checksums.sha256")
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {result_path}")


if __name__ == "__main__":
    main()
