#!/usr/bin/env python3
"""EpiClaw Immune Repertoire -- real-only execution pipeline."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


def detect_input_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        return "table"
    if suffix in {".json"}:
        return "json"
    if suffix in {".fasta", ".fa", ".fna", ".fas", ".ffn", ".faa"}:
        return "fasta"
    if suffix in {".fastq", ".fq"} or path.name.endswith((".fastq.gz", ".fq.gz")):
        return "fastq"
    if suffix in {".nwk", ".newick", ".tree"}:
        return "tree"
    return "text"

def read_table(path: Path) -> list[dict[str, str]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delimiter))

def summarize_table(path: Path) -> dict:
    rows = read_table(path)
    columns = list(rows[0].keys()) if rows else []
    return {
        "kind": "table",
        "rows": len(rows),
        "columns": columns,
        "preview": rows[:5],
    }

def summarize_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        keys = list(payload.keys())
        size = len(payload)
    elif isinstance(payload, list):
        keys = []
        size = len(payload)
    else:
        keys = []
        size = 1
    return {
        "kind": "json",
        "top_level_type": type(payload).__name__,
        "size": size,
        "keys": keys[:20],
    }

def summarize_fasta(path: Path) -> dict:
    n_sequences = 0
    total_length = 0
    lengths: list[int] = []
    current = 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current:
                    lengths.append(current)
                    total_length += current
                n_sequences += 1
                current = 0
                continue
            current += len(line)
    if current:
        lengths.append(current)
        total_length += current
    return {
        "kind": "fasta",
        "n_sequences": n_sequences,
        "total_length": total_length,
        "max_length": max(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
    }

def summarize_fastq(path: Path) -> dict:
    opener = path.open
    if path.name.endswith(".gz"):
        import gzip

        opener = gzip.open
    n_reads = 0
    read_lengths: list[int] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
        for idx, line in enumerate(fh):
            if idx % 4 == 1:
                n_reads += 1
                read_lengths.append(len(line.strip()))
    return {
        "kind": "fastq",
        "n_reads": n_reads,
        "mean_read_length": round(sum(read_lengths) / len(read_lengths), 2) if read_lengths else 0.0,
        "max_read_length": max(read_lengths) if read_lengths else 0,
    }

def summarize_tree(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    n_leaves = text.count(",") + 1 if "(" in text else 0
    return {
        "kind": "tree",
        "characters": len(text),
        "leaf_count_estimate": n_leaves,
    }

def summarize_directory(path: Path) -> dict:
    files = sorted(p for p in path.rglob("*") if p.is_file())
    exts: dict[str, int] = {}
    for file in files:
        suffix = file.suffix.lower() or "<none>"
        exts[suffix] = exts.get(suffix, 0) + 1
    return {
        "kind": "directory",
        "n_files": len(files),
        "extensions": dict(sorted(exts.items())),
        "sample_files": [str(p.relative_to(path)) for p in files[:10]],
    }

def summarize_input(path: Path) -> dict:
    kind = detect_input_kind(path)
    if kind == "table":
        return summarize_table(path)
    if kind == "json":
        return summarize_json(path)
    if kind == "fasta":
        return summarize_fasta(path)
    if kind == "fastq":
        return summarize_fastq(path)
    if kind == "tree":
        return summarize_tree(path)
    if kind == "directory":
        return summarize_directory(path)
    return {
        "kind": "text",
        "size_bytes": path.stat().st_size,
    }

def maybe_run_tool(binary_names: list[str], cmd_builder) -> tuple[str, str] | None:
    for name in binary_names:
        binary = shutil.which(name)
        if not binary:
            continue
        cmd = cmd_builder(binary)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return name, proc.stdout.strip() or proc.stderr.strip()
    return None


VERSION = "0.1.0"
SKILL_NAME = "immune-repertoire"
TOOL_CANDIDATES = ['mixcr', 'igblastn', 'igblastp']
DEMO_FASTA = """>clone1
CASSLGQDTQYF
>clone2
CASSIRSSYEQYF
>clone3
CASSLGQDTQYF
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).stem,
        description="EpiClaw Immune Repertoire -- real execution only.",
    )
    parser.add_argument("--input", type=str, default=None, help="Input file or directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo repertoire")
    if TOOL_CANDIDATES:
        parser.add_argument("--tool", type=str, default="auto", help="Preferred tool or auto")
    return parser


def _write_demo_input(output_dir: Path) -> Path:
    demo_path = output_dir / "demo_repertoire.fasta"
    demo_path.write_text(DEMO_FASTA, encoding="utf-8")
    return demo_path


def probe_tool(preferred: str | None) -> dict:
    candidates = TOOL_CANDIDATES
    if preferred and preferred not in {"", "auto"}:
        candidates = [preferred]
    if not candidates:
        return {"selected": None, "message": "python-only pipeline"}

    result = maybe_run_tool(candidates, lambda binary: [binary, "--version"])
    if result is None:
        return {"selected": None, "message": "no supported CLI detected on PATH"}
    name, output = result
    return {"selected": name, "message": output.splitlines()[0] if output else "version probe succeeded"}


def generate_report(output_path: Path, input_path: Path, summary: dict, tool_info: dict) -> None:
    header = generate_report_header(
        title="Immune Repertoire Report",
        skill_name=SKILL_NAME,
        extra_metadata={
            "Mode": "Real",
            "Tool": tool_info.get("selected") or "python",
            "Version": VERSION,
        },
    )
    body = [
        "## Summary",
        "",
        f"- **Input**: {input_path}",
        f"- **Detected input kind**: {summary.get('kind', 'unknown')}",
        f"- **Tool probe**: {tool_info.get('message', 'not attempted')}",
        "",
        "## Parsed Data",
        "",
        "```json",
        __import__('json').dumps(summary, indent=2, ensure_ascii=False),
        "```",
    ]
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + body + [footer]), encoding="utf-8")


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

    summary = summarize_input(input_path)
    tool_info = probe_tool(getattr(args, "tool", "auto"))

    report_path = output_dir / "report.md"
    generate_report(report_path, input_path, summary, tool_info)

    write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "n_sequences": summary.get("n_sequences", 0),
            "input_kind": summary.get("kind", "unknown"),
            "tool": tool_info.get("selected"),
        },
        data={
            "input": str(input_path),
            "summary": summary,
            "tool_probe": tool_info,
        },
    )

    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
