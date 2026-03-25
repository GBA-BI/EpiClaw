#!/usr/bin/env python3
"""EpiClaw NCBI Sequence Fetcher -- search and download viral/pathogen sequences from
NCBI Nucleotide, NCBI Virus, and SRA databases for genomic epidemiology workflows."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

from reporting import generate_report_header, generate_report_footer, write_result_json
from ncbi_virus_connector import NCBIVirusClient


VERSION = "0.1.0"
SKILL_NAME = "ncbi-sequence-fetcher"

# ---------------------------------------------------------------------------
# Organism presets
# ---------------------------------------------------------------------------

ORGANISM_PRESETS: dict[str, dict[str, str]] = {
    "sars-cov-2": {
        "query": 'SARS-CoV-2[Organism] AND "complete genome"[Title]',
        "db": "nuccore",
        "description": "SARS-CoV-2 complete genomes",
    },
    "influenza-a": {
        "query": "Influenza A virus[Organism] AND segment AND complete",
        "db": "nuccore",
        "description": "Influenza A virus segments",
    },
    "mpox": {
        "query": "Monkeypox virus[Organism] AND complete genome",
        "db": "nuccore",
        "description": "Monkeypox virus complete genomes",
    },
    "dengue": {
        "query": "Dengue virus[Organism] AND complete genome",
        "db": "nuccore",
        "description": "Dengue virus complete genomes",
    },
    "ebola": {
        "query": "Ebola virus[Organism] AND complete genome",
        "db": "nuccore",
        "description": "Ebola virus complete genomes",
    },
    "rsv": {
        "query": "Respiratory syncytial virus[Organism] AND complete genome",
        "db": "nuccore",
        "description": "RSV complete genomes",
    },
}

# ---------------------------------------------------------------------------
# Demo data (offline fallback)
# ---------------------------------------------------------------------------

DEMO_METADATA: list[dict[str, Any]] = [
    {"accession": "MN908947", "title": "Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1, complete genome",
     "organism": "Severe acute respiratory syndrome coronavirus 2", "length": 29903,
     "collection_date": "Dec-2019", "country": "China"},
    {"accession": "NC_045512", "title": "Severe acute respiratory syndrome coronavirus 2, complete genome (RefSeq)",
     "organism": "Severe acute respiratory syndrome coronavirus 2", "length": 29903,
     "collection_date": "Dec-2019", "country": "China"},
    {"accession": "OQ034627", "title": "SARS-CoV-2 isolate XBB.1.5, complete genome",
     "organism": "Severe acute respiratory syndrome coronavirus 2", "length": 29797,
     "collection_date": "Jan-2023", "country": "USA"},
]

DEMO_FASTA_SNIPPET = (
    ">MN908947.3 Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1, complete genome\n"
    "ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCTGTTCTCTAAA\n"
    "CGAACTTTAAAATCTGTGTGGCTGTCACTCGGCTGCATGCTTAGTGCACTCACGCAGTATAAT\n"
)


# ---------------------------------------------------------------------------
# Live NCBI fetchers
# ---------------------------------------------------------------------------

def search_and_fetch_ncbi(
    query: str,
    db: str,
    max_results: int,
    download_fasta: bool,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], str | None]:
    """Search NCBI, fetch metadata, optionally download FASTA."""
    import os

    api_key = os.environ.get("NCBI_API_KEY")
    client = NCBIVirusClient(api_key=api_key)

    print(f"[info] Searching NCBI {db}: {query!r} (max {max_results})...")
    accessions = client.search_sequences(query=query, db=db, max_results=max_results)
    if not accessions:
        print("[warn] No accessions returned by NCBI search.")
        return [], None

    print(f"[info] Found {len(accessions)} accessions. Fetching metadata...")
    metadata = client.fetch_metadata(accessions[:max_results], db=db)

    fasta_path_str: str | None = None
    if download_fasta and metadata:
        ids_to_download = [m["accession"] for m in metadata if m.get("accession")][:20]
        if ids_to_download:
            fasta_path = output_dir / "sequences.fasta"
            print(f"[info] Downloading FASTA for {len(ids_to_download)} sequences...")
            try:
                client.download_fasta(ids_to_download, db=db, output_path=fasta_path)
                fasta_path_str = str(fasta_path)
                print(f"[info] FASTA saved: {fasta_path}")
            except Exception as e:
                print(f"[warn] FASTA download failed: {e}")

    return metadata, fasta_path_str


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def generate_report(
    metadata: list[dict[str, Any]],
    query: str,
    db: str,
    fasta_path: str | None,
    demo: bool,
) -> str:
    lines = [
        generate_report_header(
            title="NCBI Sequence Fetch Report",
            skill_name=SKILL_NAME,
            extra_metadata={
                "Query": query,
                "Database": db,
                "Sequences found": str(len(metadata)),
                "FASTA downloaded": "Yes" if fasta_path else "No",
                "Mode": "DEMO" if demo else "LIVE",
                "Version": VERSION,
            },
        ),
        "## Sequences Retrieved",
        "",
        f"- Total sequences: **{len(metadata)}**",
        f"- Database: `{db}`",
        f"- Query: `{query}`",
        "",
        "## Sequence Metadata",
        "",
        "| Accession | Organism | Length (bp) | Collection Date | Country |",
        "|-----------|----------|-------------|-----------------|---------|",
    ]
    for row in metadata[:30]:
        lines.append(
            f"| {row.get('accession', '')} "
            f"| {str(row.get('organism', ''))[:40]} "
            f"| {row.get('length', '')} "
            f"| {row.get('collection_date', row.get('createdate', ''))} "
            f"| {row.get('country', '')} |"
        )
    if fasta_path:
        lines.extend(["", "## FASTA Output", "", f"Sequences written to: `{fasta_path}`", ""])
    lines.extend([
        "",
        "## Downstream Skill Chains",
        "",
        "Feed sequences into genomic epidemiology skills:",
        "- `variant-surveillance` — lineage classification",
        "- `phylodynamics` — molecular clock, BEAST",
        "- `transmission-inference` — who infected whom",
        "- `seqqc` — quality control before assembly",
        "",
        generate_report_footer(),
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="EpiClaw NCBI Sequence Fetcher — search and download pathogen sequences"
    )
    parser.add_argument("--organism", default=None,
                        help=f"Organism preset: {list(ORGANISM_PRESETS.keys())}")
    parser.add_argument("--query", default=None,
                        help="Custom NCBI Entrez query (overrides --organism)")
    parser.add_argument("--db", default="nuccore",
                        choices=["nuccore", "protein", "biosample"],
                        help="NCBI database (default: nuccore)")
    parser.add_argument("--max-results", type=int, default=50,
                        help="Maximum sequences to fetch (default: 50)")
    parser.add_argument("--download-fasta", action="store_true",
                        help="Download FASTA sequences (first 20) in addition to metadata")
    parser.add_argument("--output", default="output/ncbi-sequence-fetcher")
    parser.add_argument("--demo", action="store_true", help="Run demo (offline, no API calls)")
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw {SKILL_NAME} v{VERSION}")

    # Resolve query
    if args.query:
        query = args.query
        db = args.db
    elif args.organism:
        preset = ORGANISM_PRESETS.get(args.organism.lower())
        if not preset:
            parser.error(f"Unknown organism preset '{args.organism}'. "
                         f"Available: {list(ORGANISM_PRESETS.keys())}")
        query = preset["query"]
        db = preset["db"]
        print(f"[info] Using preset: {preset['description']}")
    else:
        query = ORGANISM_PRESETS["sars-cov-2"]["query"]
        db = "nuccore"
        print("[info] No query specified; defaulting to SARS-CoV-2 complete genomes.")

    print(f"[info] Query: {query!r}, DB: {db}")

    metadata: list[dict[str, Any]] = []
    fasta_path: str | None = None

    if args.demo:
        print("[info] Demo mode — using pre-loaded SARS-CoV-2 reference metadata.")
        metadata = DEMO_METADATA
        fasta_path_obj = out_dir / "sequences.fasta"
        fasta_path_obj.write_text(DEMO_FASTA_SNIPPET, encoding="utf-8")
        fasta_path = str(fasta_path_obj)
        print(f"[info] Demo FASTA snippet written to {fasta_path}")
    else:
        try:
            metadata, fasta_path = search_and_fetch_ncbi(
                query=query, db=db,
                max_results=args.max_results,
                download_fasta=args.download_fasta,
                output_dir=out_dir,
            )
        except Exception as e:
            print(f"[warn] NCBI fetch failed ({e}). Falling back to demo data.")
            metadata = DEMO_METADATA

    print(f"[info] Sequences: {len(metadata)}")

    # Write metadata CSV
    if metadata:
        csv_path = out_dir / "metadata.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(metadata[0].keys()))
            writer.writeheader()
            writer.writerows(metadata)
        print(f"[info] Metadata CSV: {csv_path}")

    # Write report
    report_md = generate_report(metadata, query, db, fasta_path, args.demo)
    report_path = out_dir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[info] Report: {report_path}")

    summary: dict[str, Any] = {
        "query": query,
        "db": db,
        "n_sequences": len(metadata),
        "fasta_downloaded": fasta_path is not None,
        "mode": "demo" if args.demo else "live",
    }
    write_result_json(out_dir, SKILL_NAME, VERSION, summary,
                      {"sequences": metadata[:20]})
    print("[info] Done.")


if __name__ == "__main__":
    main()
