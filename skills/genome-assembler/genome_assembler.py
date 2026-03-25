#!/usr/bin/env python3
"""EpiClaw Genome Assembler -- de novo genome assembly and quality assessment."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "genome-assembler"
DEMO_CONTIGS = """>contig_1
ATGCGTACGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
>contig_2
ATGCGTACGTAGCTAGCTAGCTAGCTAGCTAGCTAACGATCGATCGA
>contig_3
ATGCGTACGTAGCTAGCTAGCTAGCTAACGATCGATCGATCGATCGA
"""


def _detect_read_inputs(input_path: Path) -> tuple[Path | None, Path | None, Path | None]:
    if input_path.is_file():
        name = input_path.name
        if "_R1" in name:
            mate = input_path.with_name(name.replace("_R1", "_R2"))
            if mate.exists():
                return input_path, mate, None
        return None, None, input_path

    files: list[Path] = []
    for ext in ("*.fastq.gz", "*.fq.gz", "*.fastq", "*.fq", "*.fasta", "*.fa"):
        files.extend(sorted(input_path.glob(ext)))
    if not files:
        return None, None, None

    r1 = next((p for p in files if "_R1" in p.name), None)
    if r1:
        r2 = r1.with_name(r1.name.replace("_R1", "_R2"))
        if r2.exists():
            return r1, r2, None
    return None, None, files[0]


def _resolve_tool(tool: str, mode: str) -> tuple[str, str]:
    tool_bins = {
        "spades": shutil.which("spades.py") or shutil.which("spades"),
        "unicycler": shutil.which("unicycler"),
        "flye": shutil.which("flye"),
    }
    if tool == "auto":
        if mode == "long" and tool_bins["flye"]:
            tool = "flye"
        elif mode == "hybrid" and tool_bins["unicycler"]:
            tool = "unicycler"
        elif tool_bins["spades"]:
            tool = "spades"
        else:
            for candidate in ("spades", "unicycler", "flye"):
                if tool_bins[candidate]:
                    tool = candidate
                    break
            else:
                raise RuntimeError("No assembler found on PATH (spades.py/spades, unicycler, flye).")
    binary = tool_bins.get(tool)
    if not binary:
        raise RuntimeError(f"Tool '{tool}' not found on PATH.")
    return tool, binary


def _run_assembler(tool: str, binary: str, input_path: Path, output_dir: Path) -> Path:
    real_dir = output_dir / "assembly_run"
    real_dir.mkdir(parents=True, exist_ok=True)
    r1, r2, single = _detect_read_inputs(input_path)

    if tool == "spades":
        cmd = [binary, "-o", str(real_dir)]
        if r1 and r2:
            cmd.extend(["-1", str(r1), "-2", str(r2)])
        elif single:
            cmd.extend(["-s", str(single)])
        else:
            raise RuntimeError("SPAdes requires readable FASTQ/FASTA inputs.")
        expected = real_dir / "contigs.fasta"
    elif tool == "unicycler":
        cmd = [binary, "-o", str(real_dir)]
        if r1 and r2:
            cmd.extend(["-1", str(r1), "-2", str(r2)])
        elif single:
            cmd.extend(["-s", str(single)])
        else:
            raise RuntimeError("Unicycler requires readable FASTQ/FASTA inputs.")
        expected = real_dir / "assembly.fasta"
    else:
        long_read = single or r1
        if not long_read:
            raise RuntimeError("Flye requires a long-read FASTQ/FASTA input.")
        cmd = [binary, "--nano-raw", str(long_read), "--out-dir", str(real_dir), "--threads", "1"]
        expected = real_dir / "assembly.fasta"

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{tool} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    if not expected.exists():
        raise RuntimeError(f"Assembler completed but output FASTA is missing: {expected}")
    return expected


def _contig_lengths_and_gc(contigs_path: Path) -> tuple[list[int], float]:
    lengths: list[int] = []
    gc_count = 0
    total_bases = 0
    current = 0
    with contigs_path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current > 0:
                    lengths.append(current)
                current = 0
                continue
            seq = line.upper()
            current += len(seq)
            total_bases += len(seq)
            gc_count += seq.count("G") + seq.count("C")
    if current > 0:
        lengths.append(current)
    if not lengths:
        raise RuntimeError("No contigs found in output FASTA.")
    gc_pct = (gc_count / total_bases * 100.0) if total_bases else 0.0
    return sorted(lengths, reverse=True), round(gc_pct, 2)


def _n_stat(lengths: list[int], fraction: float) -> int:
    target = sum(lengths) * fraction
    seen = 0
    for length in lengths:
        seen += length
        if seen >= target:
            return int(length)
    return int(lengths[-1])


def _parse_quast_report(report_tsv: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    lines = report_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= 2:
            metrics[parts[0].strip()] = parts[1].strip()
    return metrics


def _run_quast(contigs_path: Path, output_dir: Path, reference: str | None) -> dict[str, str]:
    quast_bin = shutil.which("quast") or shutil.which("quast.py")
    if not quast_bin:
        return {}
    quast_dir = output_dir / "quast"
    cmd = [quast_bin, str(contigs_path), "-o", str(quast_dir)]
    if reference:
        cmd.extend(["-r", reference])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {}
    report_tsv = quast_dir / "report.tsv"
    if not report_tsv.exists():
        return {}
    return _parse_quast_report(report_tsv)


def run_pipeline(input_path: Path, output_dir: Path, tool: str, mode: str, reference: str | None) -> tuple[dict, dict, str]:
    selected_tool, binary = _resolve_tool(tool, mode)
    contigs_path = _run_assembler(selected_tool, binary, input_path, output_dir)
    lengths, gc_content = _contig_lengths_and_gc(contigs_path)
    quast_metrics = _run_quast(contigs_path, output_dir, reference)

    total_length = sum(lengths)
    n50 = _n_stat(lengths, 0.5)
    n90 = _n_stat(lengths, 0.9)
    n_contigs = len(lengths)
    largest_contig = lengths[0]
    quality = "HIGH" if n_contigs <= 20 and n50 >= 100_000 else ("MEDIUM" if n_contigs <= 200 and n50 >= 20_000 else "LOW")

    summary = {
        "total_length": total_length,
        "n_contigs": n_contigs,
        "n50": n50,
        "n90": n90,
        "largest_contig": largest_contig,
        "gc_content": gc_content,
        "assembly_quality": quality,
    }
    data = {
        "tool_used": selected_tool,
        "mode": mode,
        "contigs_fasta": str(contigs_path),
        "contig_lengths": lengths,
        "quast_metrics": quast_metrics,
    }
    return summary, data, selected_tool


def run_demo_pipeline(output_dir: Path, mode: str) -> tuple[dict, dict, str]:
    contigs_path = output_dir / "demo_contigs.fasta"
    contigs_path.write_text(DEMO_CONTIGS, encoding="utf-8")
    lengths, gc_content = _contig_lengths_and_gc(contigs_path)
    summary = {
        "total_length": sum(lengths),
        "n_contigs": len(lengths),
        "n50": _n_stat(lengths, 0.5),
        "n90": _n_stat(lengths, 0.9),
        "largest_contig": lengths[0],
        "gc_content": gc_content,
        "assembly_quality": "DEMO",
    }
    data = {
        "tool_used": "spades (simulated)",
        "mode": mode,
        "contigs_fasta": str(contigs_path),
        "contig_lengths": lengths,
        "quast_metrics": {},
    }
    return summary, data, "spades (simulated)"


def generate_report(summary: dict, data: dict, output_path: Path) -> None:
    header = generate_report_header(
        title="Genome Assembly Report",
        skill_name=SKILL_NAME,
        extra_metadata={"Assembler": data["tool_used"], "Mode": data["mode"], "Version": VERSION},
    )
    lines = [
        "## Assembly Statistics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total Assembly Length | {summary['total_length']:,} bp |",
        f"| Number of Contigs | {summary['n_contigs']} |",
        f"| N50 | {summary['n50']:,} bp |",
        f"| N90 | {summary['n90']:,} bp |",
        f"| Largest Contig | {summary['largest_contig']:,} bp |",
        f"| GC Content | {summary['gc_content']}% |",
        f"| Quality | {summary['assembly_quality']} |",
    ]
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genome_assembler",
        description="EpiClaw Genome Assembler -- de novo genome assembly and quality assessment.",
    )
    parser.add_argument("--input", type=str, default=None, help="Path to reads file or directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo assembly summary")
    parser.add_argument("--tool", choices=["spades", "unicycler", "flye", "auto"], default="auto")
    parser.add_argument("--mode", choices=["short", "long", "hybrid"], default="short")
    parser.add_argument("--reference", type=str, default=None, help="Optional reference genome for QUAST")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo or not args.input:
        summary, data, _tool_used = run_demo_pipeline(output_dir, args.mode)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        summary, data, _tool_used = run_pipeline(input_path, output_dir, args.tool, args.mode, args.reference)
    report_path = output_dir / "report.md"
    generate_report(summary, data, report_path)

    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
