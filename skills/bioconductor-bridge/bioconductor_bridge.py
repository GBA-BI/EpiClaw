#!/usr/bin/env python3
"""EpiClaw Bioconductor Bridge -- package recommendation and setup inspection."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json
from repro import write_checksums_manifest, write_commands_script


VERSION = "0.1.0"
SKILL_NAME = "bioconductor-bridge"

PACKAGE_CATALOG = [
    {
        "package": "DESeq2",
        "domain": "bulk-rna-seq",
        "container": "SummarizedExperiment",
        "summary": "Differential expression for count matrices with covariate-aware design formulas.",
        "keywords": ["bulk", "rna", "differential", "expression", "deseq2", "counts", "pseudobulk"],
    },
    {
        "package": "edgeR",
        "domain": "bulk-rna-seq",
        "container": "DGEList",
        "summary": "Negative-binomial differential expression with flexible quasi-likelihood workflows.",
        "keywords": ["bulk", "rna", "differential", "expression", "edger", "counts"],
    },
    {
        "package": "SingleCellExperiment",
        "domain": "single-cell",
        "container": "SingleCellExperiment",
        "summary": "Canonical container for single-cell assays and metadata.",
        "keywords": ["single-cell", "single cell", "container", "sce", "object"],
    },
    {
        "package": "scater",
        "domain": "single-cell",
        "container": "SingleCellExperiment",
        "summary": "Single-cell QC, exploratory analysis, and visualization.",
        "keywords": ["single-cell", "qc", "visualization", "scater", "pca"],
    },
    {
        "package": "scran",
        "domain": "single-cell",
        "container": "SingleCellExperiment",
        "summary": "Single-cell normalization, variance modelling, and clustering utilities.",
        "keywords": ["single-cell", "normalization", "clustering", "scran"],
    },
    {
        "package": "GenomicRanges",
        "domain": "ranges",
        "container": "GRanges",
        "summary": "Interval arithmetic and overlap queries for genomic coordinates.",
        "keywords": ["ranges", "genomicranges", "intervals", "bed", "granges", "annotation"],
    },
    {
        "package": "VariantAnnotation",
        "domain": "variant-annotation",
        "container": "VCF",
        "summary": "Read, subset, and annotate VCF files using Bioconductor containers.",
        "keywords": ["variant", "vcf", "annotation", "variantannotation", "clinvar"],
    },
    {
        "package": "AnnotationHub",
        "domain": "resource-hub",
        "container": "Hub resources",
        "summary": "Programmatic access to genomic annotations and reference resources.",
        "keywords": ["annotationhub", "annotation", "reference", "hub"],
    },
    {
        "package": "ExperimentHub",
        "domain": "resource-hub",
        "container": "Hub resources",
        "summary": "Programmatic access to curated experimental datasets.",
        "keywords": ["experimenthub", "dataset", "reference", "hub"],
    },
    {
        "package": "ComplexHeatmap",
        "domain": "visualization",
        "container": "matrix-like objects",
        "summary": "Composable heatmaps for omics and annotation-rich matrices.",
        "keywords": ["heatmap", "visualization", "complexheatmap", "plot"],
    },
]

WORKFLOW_TEMPLATES = {
    "bulk-rna-seq": {
        "title": "Bulk RNA-seq differential expression",
        "packages": ["DESeq2", "SummarizedExperiment", "apeglm", "ComplexHeatmap"],
        "steps": [
            "Import counts and sample metadata into a SummarizedExperiment-like structure.",
            "Filter low-count genes and run DESeq2 size-factor / dispersion estimation.",
            "Fit the design formula and extract the requested contrast.",
            "Shrink log2 fold changes and visualize top signals with MA/heatmap plots.",
        ],
    },
    "single-cell": {
        "title": "Single-cell QC and normalization",
        "packages": ["SingleCellExperiment", "scater", "scran", "batchelor"],
        "steps": [
            "Load counts into SingleCellExperiment.",
            "Compute QC metrics and flag low-quality cells.",
            "Normalize with scran and inspect reduced dimensions.",
            "Hand off to downstream clustering / marker workflows.",
        ],
    },
    "variant-annotation": {
        "title": "VCF annotation workflow",
        "packages": ["VariantAnnotation", "BSgenome", "AnnotationHub"],
        "steps": [
            "Read the VCF with VariantAnnotation.",
            "Attach transcript / locus metadata from AnnotationHub resources.",
            "Filter variants by effect class and population frequency evidence.",
            "Export annotated tables for downstream interpretation.",
        ],
    },
}


def _score_package(query: str, package: dict[str, str]) -> int:
    tokens = {token for token in query.lower().replace("-", " ").split() if token}
    haystack = " ".join(
        [package["package"], package["domain"], package["container"], package["summary"], " ".join(package["keywords"])]
    ).lower()
    return sum(3 if token in package["package"].lower() else 1 for token in tokens if token in haystack)


def _recommend_packages(query: str, limit: int = 5) -> list[dict[str, str | int]]:
    ranked = []
    for package in PACKAGE_CATALOG:
        score = _score_package(query, package)
        if score <= 0:
            continue
        ranked.append({**package, "score": score})
    ranked.sort(key=lambda item: (-int(item["score"]), str(item["package"])))
    return ranked[:limit] or [{**PACKAGE_CATALOG[0], "score": 0}]


def _detect_workflow(query: str) -> str:
    lowered = query.lower()
    if any(token in lowered for token in ("single-cell", "single cell", "scrna", "sce")):
        return "single-cell"
    if any(token in lowered for token in ("vcf", "variant", "clinvar")):
        return "variant-annotation"
    return "bulk-rna-seq"


def _inspect_setup() -> dict[str, object]:
    rscript = shutil.which("Rscript")
    status: dict[str, object] = {
        "rscript_available": bool(rscript),
        "r_version": None,
        "biocmanager_available": False,
        "message": "",
    }
    if not rscript:
        status["message"] = "Rscript not found on PATH."
        return status
    version_proc = subprocess.run([rscript, "--version"], capture_output=True, text=True, check=False)
    status["r_version"] = (version_proc.stderr or version_proc.stdout).strip().splitlines()[0]
    probe = subprocess.run(
        [rscript, "-e", "cat(requireNamespace('BiocManager', quietly=TRUE))"],
        capture_output=True,
        text=True,
        check=False,
    )
    status["biocmanager_available"] = probe.returncode == 0 and "TRUE" in (probe.stdout + probe.stderr)
    status["message"] = (
        "BiocManager detected." if status["biocmanager_available"] else "BiocManager not available in current R library."
    )
    return status


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_repro_bundle(output_dir: Path, selected_packages: list[str], workflow_key: str, commands: list[str]) -> list[Path]:
    repro_dir = output_dir / "reproducibility"
    repro_dir.mkdir(parents=True, exist_ok=True)
    install_script = repro_dir / "install_packages.R"
    starter_script = repro_dir / "starter_workflow.R"
    env_file = repro_dir / "environment.yml"
    session_info = repro_dir / "sessionInfo.txt"
    commands_file = repro_dir / "commands.sh"

    install_script.write_text(
        "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager')\n"
        f"BiocManager::install(c({', '.join(json.dumps(pkg) for pkg in selected_packages)}), ask = FALSE, update = FALSE)\n",
        encoding="utf-8",
    )

    workflow = WORKFLOW_TEMPLATES[workflow_key]
    starter_script.write_text(
        "\n".join(
            [
                "# Auto-generated EpiClaw starter workflow",
                f"# Workflow: {workflow['title']}",
                "",
                *[f"# Step {index + 1}: {step}" for index, step in enumerate(workflow["steps"])],
                "",
                *[f"library({pkg})" for pkg in workflow["packages"] if pkg.isidentifier()],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env_file.write_text(
        "\n".join(
            [
                "name: epiclaw-bioconductor-bridge",
                "channels:",
                "  - conda-forge",
                "dependencies:",
                "  - r-base",
                "  - python",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    setup = _inspect_setup()
    session_info.write_text(
        "\n".join(
            [
                "EpiClaw Bioconductor setup snapshot",
                f"Rscript available: {setup['rscript_available']}",
                f"R version: {setup['r_version']}",
                f"BiocManager available: {setup['biocmanager_available']}",
                f"Status: {setup['message']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_commands_script(commands_file, commands)
    manifest = write_checksums_manifest(repro_dir, [install_script, starter_script, env_file, session_info, commands_file])
    return [install_script, starter_script, env_file, session_info, commands_file, manifest]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Bioconductor Bridge")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--search", type=str, help="Search Bioconductor packages for a query")
    group.add_argument("--recommend", type=str, help="Recommend packages for a task")
    group.add_argument("--docs-search", type=str, help="Search documentation-oriented package matches")
    group.add_argument("--package-docs", type=str, help="Show package guidance for one package")
    group.add_argument("--workflow", type=str, help="Suggest a canonical workflow")
    group.add_argument("--setup", action="store_true", help="Inspect local R / BiocManager setup")
    group.add_argument("--install", type=str, help="Install comma-separated package list via BiocManager")
    group.add_argument("--demo", action="store_true", help="Run demo recommendation mode")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    mode = "demo"
    query = "bulk RNA-seq differential expression"
    if args.search:
        mode, query = "search", args.search
    elif args.recommend:
        mode, query = "recommend", args.recommend
    elif args.docs_search:
        mode, query = "docs-search", args.docs_search
    elif args.package_docs:
        mode, query = "package-docs", args.package_docs
    elif args.workflow:
        mode, query = "workflow", args.workflow
    elif args.setup:
        mode, query = "setup", "setup"
    elif args.install:
        mode, query = "install", args.install

    workflow_key = _detect_workflow(query)
    recommendations = _recommend_packages(query, limit=5)
    if mode == "package-docs":
        recommendations = [item for item in PACKAGE_CATALOG if item["package"].lower() == query.lower()] or recommendations[:1]
    selected_packages = [str(item["package"]) for item in recommendations[:4]]

    setup = _inspect_setup()
    install_status = None
    commands = [f"# Query mode: {mode}", f"# Query: {query}"]
    if mode == "install":
        selected_packages = [item.strip() for item in query.split(",") if item.strip()]
        commands.append(f"Rscript -e \"BiocManager::install(c({', '.join(json.dumps(pkg) for pkg in selected_packages)}))\"")
        if setup["rscript_available"]:
            proc = subprocess.run(
                [
                    shutil.which("Rscript") or "Rscript",
                    "-e",
                    "if (!requireNamespace('BiocManager', quietly=TRUE)) install.packages('BiocManager');"
                    f"BiocManager::install(c({', '.join(json.dumps(pkg) for pkg in selected_packages)}), ask=FALSE, update=FALSE)",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            install_status = {
                "return_code": proc.returncode,
                "stdout": proc.stdout[-1000:],
                "stderr": proc.stderr[-1000:],
            }
        else:
            install_status = {"return_code": 127, "stdout": "", "stderr": "Rscript not available."}

    table_dir = output_dir / "tables"
    _write_csv(table_dir / "recommended_packages.csv", recommendations)
    repro_files = _write_repro_bundle(output_dir, selected_packages, workflow_key, commands)

    report_lines = [
        generate_report_header(
            title="Bioconductor Bridge Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Mode": mode, "Workflow": workflow_key, "Version": VERSION},
        ),
        "## Recommendations",
        "",
        "| Package | Domain | Container | Why it fits |",
        "|---|---|---|---|",
    ]
    for item in recommendations:
        report_lines.append(
            f"| {item['package']} | {item['domain']} | {item['container']} | {item['summary']} |"
        )
    workflow = WORKFLOW_TEMPLATES[workflow_key]
    report_lines.extend(["", f"## Suggested Workflow — {workflow['title']}", ""])
    for index, step in enumerate(workflow["steps"], start=1):
        report_lines.append(f"{index}. {step}")
    report_lines.extend(
        [
            "",
            "## Local Setup",
            "",
            f"- Rscript available: `{setup['rscript_available']}`",
            f"- R version: `{setup['r_version']}`",
            f"- BiocManager available: `{setup['biocmanager_available']}`",
            f"- Note: {setup['message']}",
        ]
    )
    if install_status is not None:
        report_lines.extend(
            [
                "",
                "## Install Status",
                "",
                f"- Return code: `{install_status['return_code']}`",
                f"- stderr tail: `{install_status['stderr'] or 'none'}`",
            ]
        )
    report_lines.append(generate_report_footer())
    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "mode": mode,
            "workflow": workflow_key,
            "top_package": selected_packages[0] if selected_packages else "",
            "n_recommendations": len(recommendations),
            "setup_ready": bool(setup["rscript_available"]),
        },
        data={
            "query": query,
            "recommendations": recommendations,
            "workflow": workflow,
            "setup": setup,
            "install_status": install_status,
            "reproducibility_files": [str(path) for path in repro_files],
        },
    )

    repro_dir = output_dir / "reproducibility"
    write_checksums_manifest(repro_dir, [report_path, result_path, table_dir / "recommended_packages.csv", *repro_files])
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {result_path}")


if __name__ == "__main__":
    main()
