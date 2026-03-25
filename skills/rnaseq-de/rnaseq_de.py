#!/usr/bin/env python3
"""EpiClaw RNA-seq differential expression with demo-friendly local statistics."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json
from repro import write_checksums_manifest, write_commands_script


VERSION = "0.1.0"
SKILL_NAME = "rnaseq-de"

DEMO_COUNTS = [
    ["gene_id", "ctrl_1", "ctrl_2", "treat_1", "treat_2"],
    ["IFI27", "18", "22", "180", "175"],
    ["CXCL10", "25", "21", "130", "120"],
    ["ISG15", "30", "32", "160", "170"],
    ["MUC1", "90", "86", "95", "91"],
    ["KRT8", "110", "112", "105", "103"],
    ["GAPDH", "500", "490", "505", "498"],
]

DEMO_METADATA = [
    ["sample_id", "condition", "batch"],
    ["ctrl_1", "control", "A"],
    ["ctrl_2", "control", "B"],
    ["treat_1", "treated", "A"],
    ["treat_2", "treated", "B"],
]


def _write_demo_inputs(output_dir: Path) -> tuple[Path, Path]:
    counts_path = output_dir / "demo_counts.csv"
    metadata_path = output_dir / "demo_metadata.csv"
    with counts_path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(DEMO_COUNTS)
    with metadata_path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(DEMO_METADATA)
    return counts_path, metadata_path


def _read_matrix(path: Path) -> tuple[list[str], list[dict[str, object]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        sample_ids = [name for name in reader.fieldnames[1:]] if reader.fieldnames else []
        rows = []
        for row in reader:
            gene_id = row[reader.fieldnames[0]]
            values = {sample: float(row[sample]) for sample in sample_ids}
            rows.append({"gene_id": gene_id, "values": values})
    return sample_ids, rows


def _read_metadata(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normal_pvalue(z_score: float) -> float:
    return max(min(math.erfc(abs(z_score) / math.sqrt(2.0)), 1.0), 0.0)


def _adjust_bh(rows: list[dict[str, object]]) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: float(item[1]["p_value"]))
    total = len(rows)
    running = 1.0
    for rank, (original_index, row) in enumerate(reversed(ordered), start=1):
        p_value = float(row["p_value"])
        adjusted = min(running, p_value * total / (total - rank + 1))
        rows[original_index]["padj"] = adjusted
        running = adjusted


def _make_svg(points: list[tuple[float, float, str]], path: Path, title: str, x_label: str, y_label: str) -> None:
    width, height = 640, 420
    if not points:
        path.write_text("<svg xmlns='http://www.w3.org/2000/svg' width='640' height='420'></svg>\n", encoding="utf-8")
        return
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = (x_max - x_min) or 1.0
    y_span = (y_max - y_min) or 1.0

    def sx(value: float) -> float:
        return 60 + ((value - x_min) / x_span) * 520

    def sy(value: float) -> float:
        return 360 - ((value - y_min) / y_span) * 280

    circles = []
    labels = []
    for x_value, y_value, label in points:
        circles.append(f"<circle cx='{sx(x_value):.1f}' cy='{sy(y_value):.1f}' r='5' fill='#2563eb' opacity='0.75' />")
        labels.append(f"<text x='{sx(x_value)+7:.1f}' y='{sy(y_value)-7:.1f}' font-size='10'>{label}</text>")
    svg = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<rect width='100%' height='100%' fill='white' />",
        f"<text x='30' y='28' font-size='18'>{title}</text>",
        "<line x1='60' y1='360' x2='580' y2='360' stroke='black' />",
        "<line x1='60' y1='80' x2='60' y2='360' stroke='black' />",
        f"<text x='250' y='400' font-size='12'>{x_label}</text>",
        f"<text x='12' y='220' transform='rotate(-90 12 220)' font-size='12'>{y_label}</text>",
        *circles,
        *labels,
        "</svg>",
    ]
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


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
    parser = argparse.ArgumentParser(description="EpiClaw RNA-seq differential expression")
    parser.add_argument("--counts", type=str, help="Count matrix CSV/TSV")
    parser.add_argument("--metadata", type=str, help="Sample metadata CSV/TSV")
    parser.add_argument("--formula", type=str, default="~ condition", help="Design formula")
    parser.add_argument("--contrast", type=str, default="condition,treated,control", help="Contrast factor,numerator,denominator")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top genes to report")
    parser.add_argument("--demo", action="store_true", help="Run demo analysis")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo or not (args.counts and args.metadata):
        counts_path, metadata_path = _write_demo_inputs(output_dir)
    else:
        counts_path = Path(args.counts)
        metadata_path = Path(args.metadata)
        if not counts_path.exists() or not metadata_path.exists():
            raise SystemExit("[error] Counts or metadata file not found.")

    sample_ids, genes = _read_matrix(counts_path)
    metadata = _read_metadata(metadata_path)
    contrast_parts = [part.strip() for part in args.contrast.split(",")]
    if len(contrast_parts) != 3:
        raise SystemExit("[error] Contrast must be factor,numerator,denominator.")
    factor, numerator, denominator = contrast_parts
    group_map = {row["sample_id"]: row.get(factor, "") for row in metadata}
    numerator_samples = [sample for sample in sample_ids if group_map.get(sample) == numerator]
    denominator_samples = [sample for sample in sample_ids if group_map.get(sample) == denominator]
    if not numerator_samples or not denominator_samples:
        raise SystemExit("[error] Contrast groups were not found in metadata.")

    library_sizes = {sample: 0.0 for sample in sample_ids}
    detected_genes = {sample: 0 for sample in sample_ids}
    de_rows: list[dict[str, object]] = []
    normalized_rows: list[dict[str, object]] = []
    for gene in genes:
        values = gene["values"]
        normalized_row: dict[str, object] = {"gene_id": gene["gene_id"]}
        for sample in sample_ids:
            count = float(values[sample])
            library_sizes[sample] += count
            if count > 0:
                detected_genes[sample] += 1
            normalized_row[sample] = round(math.log2(count + 1.0), 4)
        normalized_rows.append(normalized_row)

        numerator_values = [float(values[sample]) for sample in numerator_samples]
        denominator_values = [float(values[sample]) for sample in denominator_samples]
        mean_num = statistics.mean(numerator_values)
        mean_den = statistics.mean(denominator_values)
        log2fc = math.log2((mean_num + 1.0) / (mean_den + 1.0))
        log_num = [math.log2(value + 1.0) for value in numerator_values]
        log_den = [math.log2(value + 1.0) for value in denominator_values]
        sd_num = statistics.stdev(log_num) if len(log_num) > 1 else 0.0
        sd_den = statistics.stdev(log_den) if len(log_den) > 1 else 0.0
        stderr = math.sqrt((sd_num ** 2 / max(len(log_num), 1)) + (sd_den ** 2 / max(len(log_den), 1))) or 1e-6
        z_score = (statistics.mean(log_num) - statistics.mean(log_den)) / stderr
        p_value = _normal_pvalue(z_score)
        mean_expr = (mean_num + mean_den) / 2.0
        de_rows.append(
            {
                "gene_id": gene["gene_id"],
                "mean_expression": round(mean_expr, 4),
                "mean_" + numerator: round(mean_num, 4),
                "mean_" + denominator: round(mean_den, 4),
                "log2_fold_change": round(log2fc, 4),
                "z_score": round(z_score, 4),
                "p_value": round(p_value, 6),
            }
        )

    _adjust_bh(de_rows)
    de_rows.sort(key=lambda row: (float(row["padj"]), -abs(float(row["log2_fold_change"]))))
    qc_rows = [
        {
            "sample_id": sample,
            "condition": group_map.get(sample, "unknown"),
            "library_size": round(library_sizes[sample], 2),
            "detected_genes": detected_genes[sample],
        }
        for sample in sample_ids
    ]

    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    pca_points = [
        (row["library_size"], row["detected_genes"], str(row["sample_id"]))
        for row in qc_rows
    ]
    volcano_points = [
        (float(row["log2_fold_change"]), -math.log10(max(float(row["p_value"]), 1e-12)), str(row["gene_id"]))
        for row in de_rows[: min(20, len(de_rows))]
    ]
    ma_points = [
        (math.log2(float(row["mean_expression"]) + 1.0), float(row["log2_fold_change"]), str(row["gene_id"]))
        for row in de_rows[: min(20, len(de_rows))]
    ]
    _make_svg(pca_points, figures_dir / "pca.svg", "Sample QC Scatter", "Library size", "Detected genes")
    _make_svg(volcano_points, figures_dir / "volcano.svg", "Volcano Plot", "log2 fold change", "-log10(p-value)")
    _make_svg(ma_points, figures_dir / "ma_plot.svg", "MA Plot", "log2 mean expression", "log2 fold change")

    _write_csv(tables_dir / "qc_summary.csv", qc_rows)
    _write_csv(tables_dir / "normalized_counts.csv", normalized_rows)
    _write_csv(tables_dir / "de_results.csv", de_rows)

    repro_dir = output_dir / "reproducibility"
    repro_dir.mkdir(parents=True, exist_ok=True)
    commands_file = write_commands_script(
        repro_dir / "commands.sh",
        [
            f"python skills/rnaseq-de/rnaseq_de.py --counts {counts_path.name} --metadata {metadata_path.name} "
            f"--formula \"{args.formula}\" --contrast \"{args.contrast}\" --output {output_dir}",
        ],
    )
    env_file = repro_dir / "environment.yml"
    env_file.write_text(
        "name: epiclaw-rnaseq-de\nchannels:\n  - conda-forge\ndependencies:\n  - python\n  - r-base\n",
        encoding="utf-8",
    )
    manifest = write_checksums_manifest(
        repro_dir,
        [
            commands_file,
            env_file,
            tables_dir / "qc_summary.csv",
            tables_dir / "normalized_counts.csv",
            tables_dir / "de_results.csv",
            figures_dir / "pca.svg",
            figures_dir / "volcano.svg",
            figures_dir / "ma_plot.svg",
        ],
    )

    significant = [row for row in de_rows if float(row["padj"]) <= 0.05 and abs(float(row["log2_fold_change"])) >= 1.0]
    top_hits = de_rows[: args.top_n]
    report = [
        generate_report_header(
            title="RNA-seq Differential Expression Report",
            skill_name=SKILL_NAME,
            input_files=[counts_path, metadata_path],
            extra_metadata={"Formula": args.formula, "Contrast": args.contrast, "Version": VERSION},
        ),
        "## Study Summary",
        "",
        f"- Samples analysed: `{len(sample_ids)}`",
        f"- Genes analysed: `{len(genes)}`",
        f"- Significant genes (padj ≤ 0.05 and |log2FC| ≥ 1): `{len(significant)}`",
        "",
        "## Top Hits",
        "",
        "| Gene | log2FC | p-value | padj |",
        "|---|---|---|---|",
    ]
    for row in top_hits:
        report.append(
            f"| {row['gene_id']} | {row['log2_fold_change']} | {row['p_value']} | {round(float(row['padj']), 6)} |"
        )
    report.append(generate_report_footer())
    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "n_samples": len(sample_ids),
            "n_genes": len(genes),
            "n_significant": len(significant),
            "contrast": args.contrast,
        },
        data={
            "top_hits": top_hits,
            "significant_genes": significant[:50],
            "qc_summary": qc_rows,
            "counts_file": str(counts_path),
            "metadata_file": str(metadata_path),
            "reproducibility_files": [str(commands_file), str(env_file), str(manifest)],
        },
    )
    write_checksums_manifest(repro_dir, [report_path, result_path, commands_file, env_file, manifest], output_name="checksums.sha256")
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {result_path}")


if __name__ == "__main__":
    main()
