#!/usr/bin/env python3
"""EpiClaw VCF annotator with local INFO-field parsing and prioritisation."""
from __future__ import annotations

import argparse
import csv
import gzip
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json
from repro import write_checksums_manifest, write_commands_script


VERSION = "0.1.0"
SKILL_NAME = "vcf-annotator"
IMPACT_RANK = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "MODIFIER": 3, "UNKNOWN": 4}
DEMO_VARIANTS = [
    {"chrom": "chr7", "pos": "55249071", "ref": "C", "alt": "T", "gene": "EGFR", "impact": "HIGH", "clinvar": "Pathogenic", "af": "0.0001"},
    {"chrom": "chr17", "pos": "7579472", "ref": "G", "alt": "A", "gene": "TP53", "impact": "MODERATE", "clinvar": "Likely_pathogenic", "af": "0.0003"},
    {"chrom": "chr1", "pos": "55516888", "ref": "G", "alt": "A", "gene": "MUC1", "impact": "LOW", "clinvar": "Uncertain_significance", "af": "0.023"},
]


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def _parse_info(info_field: str) -> dict[str, str]:
    info: dict[str, str] = {}
    for entry in info_field.split(";"):
        if "=" in entry:
            key, value = entry.split("=", 1)
            info[key] = value
    return info


def _extract_gene(info: dict[str, str]) -> str:
    if "GENE" in info:
        return info["GENE"]
    ann = info.get("ANN") or info.get("CSQ")
    if ann:
        first = ann.split(",")[0].split("|")
        for value in first[3:5]:
            if value:
                return value
    return "NA"


def _extract_impact(info: dict[str, str]) -> str:
    if "IMPACT" in info:
        return info["IMPACT"].upper()
    ann = info.get("ANN") or info.get("CSQ")
    if ann:
        first = ann.split(",")[0].split("|")
        for value in first:
            upper = value.upper()
            if upper in IMPACT_RANK:
                return upper
    return "UNKNOWN"


def _extract_af(info: dict[str, str]) -> float:
    for key in ("gnomAD_AF", "AF", "MAX_AF"):
        value = info.get(key)
        if value:
            try:
                return float(value.split(",")[0])
            except ValueError:
                continue
    return 0.0


def _read_vcf(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with _open_text(path) as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            chrom, pos, _vid, ref, alt, qual, filt, info_field, *_rest = line.rstrip("\n").split("\t")
            info = _parse_info(info_field)
            impact = _extract_impact(info)
            af = _extract_af(info)
            rows.append(
                {
                    "chrom": chrom,
                    "pos": int(pos),
                    "ref": ref,
                    "alt": alt,
                    "gene": _extract_gene(info),
                    "impact": impact,
                    "clinvar": info.get("CLNSIG", "NA"),
                    "gnomad_af": af,
                    "filter": filt,
                    "qual": qual,
                }
            )
    return rows


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
    parser = argparse.ArgumentParser(description="EpiClaw VCF annotator")
    parser.add_argument("--input", type=str, help="Annotated VCF/VCF.GZ input file")
    parser.add_argument("--top-n", type=int, default=20, help="Top prioritised variants to report")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo or not args.input:
        variants = [
            {
                "chrom": row["chrom"],
                "pos": int(row["pos"]),
                "ref": row["ref"],
                "alt": row["alt"],
                "gene": row["gene"],
                "impact": row["impact"],
                "clinvar": row["clinvar"],
                "gnomad_af": float(row["af"]),
                "filter": "PASS",
                "qual": "99",
            }
            for row in DEMO_VARIANTS
        ]
        input_files: list[Path] = []
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input file not found: {input_path}")
        variants = _read_vcf(input_path)
        input_files = [input_path]

    if not variants:
        raise SystemExit("[error] No variant records were found.")

    for row in variants:
        row["priority_score"] = (
            (10 - IMPACT_RANK.get(str(row["impact"]).upper(), 4) * 2)
            + (6 if "pathogenic" in str(row["clinvar"]).lower() else 0)
            + (2 if float(row["gnomad_af"]) < 0.01 else 0)
            + (1 if str(row["filter"]).upper() == "PASS" else 0)
        )
    prioritized = sorted(
        variants,
        key=lambda row: (
            -float(row["priority_score"]),
            IMPACT_RANK.get(str(row["impact"]).upper(), 4),
            float(row["gnomad_af"]),
        ),
    )

    tables_dir = output_dir / "tables"
    _write_csv(tables_dir / "annotated_variants.csv", variants)
    _write_csv(tables_dir / "prioritised_variants.csv", prioritized[: args.top_n])

    repro_dir = output_dir / "reproducibility"
    repro_dir.mkdir(parents=True, exist_ok=True)
    commands_file = write_commands_script(
        repro_dir / "commands.sh",
        [
            f"python skills/vcf-annotator/vcf_annotator.py --input {args.input or '<demo>'} --output {output_dir}",
        ],
    )
    manifest = write_checksums_manifest(
        repro_dir,
        [commands_file, tables_dir / "annotated_variants.csv", tables_dir / "prioritised_variants.csv"],
    )

    high_impact = [row for row in prioritized if str(row["impact"]).upper() in {"HIGH", "MODERATE"}]
    report_lines = [
        generate_report_header(
            title="VCF Annotation Report",
            skill_name=SKILL_NAME,
            input_files=input_files,
            extra_metadata={"Version": VERSION, "Records": str(len(variants))},
        ),
        "## Prioritised Variants",
        "",
        "| Gene | Locus | Impact | ClinVar | gnomAD AF | Priority |",
        "|---|---|---|---|---|---|",
    ]
    for row in prioritized[: args.top_n]:
        report_lines.append(
            f"| {row['gene']} | {row['chrom']}:{row['pos']} {row['ref']}>{row['alt']} | {row['impact']} | "
            f"{row['clinvar']} | {row['gnomad_af']} | {row['priority_score']} |"
        )
    report_lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- Prioritisation favours high/moderate predicted impact, low population frequency, and pathogenic ClinVar labels when present.",
            "- Treat annotation labels as supporting evidence rather than standalone clinical interpretation.",
            generate_report_footer(),
        ]
    )
    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "n_variants": len(variants),
            "n_prioritised": min(len(prioritized), args.top_n),
            "n_high_or_moderate": len(high_impact),
            "top_gene": prioritized[0]["gene"],
        },
        data={
            "prioritised_variants": prioritized[: args.top_n],
            "all_variants": variants[:200],
            "reproducibility_files": [str(commands_file), str(manifest)],
        },
    )
    write_checksums_manifest(repro_dir, [report_path, result_path, commands_file, manifest], output_name="checksums.sha256")
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {result_path}")


if __name__ == "__main__":
    main()
