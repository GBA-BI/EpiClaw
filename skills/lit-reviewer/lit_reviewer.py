#!/usr/bin/env python3
"""Lit-Reviewer — PubMed literature search and research briefing.

Usage:
    python lit_reviewer.py --query "COVID-19 wastewater surveillance" --output <dir>
    python lit_reviewer.py --demo --output /tmp/lit_demo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json
from html_report import HtmlReportBuilder, write_html_report


SKILL_VERSION = "0.1.0"
DEMO_QUERY = "COVID-19 wastewater surveillance"

# Epidemiology-specific MeSH qualifiers for enhanced search
EPI_MESH_QUALIFIERS = [
    "epidemiology[MeSH Subheading]",
    "disease outbreaks[MeSH]",
    "public health surveillance[MeSH]",
]


def format_authors(authors: list[str], max_display: int = 3) -> str:
    """Format author list, truncating with et al. if needed."""
    if not authors:
        return "No authors listed"
    if len(authors) <= max_display:
        return ", ".join(authors)
    return ", ".join(authors[:max_display]) + " et al."


def run(query: str, output_dir: Path, max_results: int = 10, is_demo: bool = False) -> dict:
    """Search PubMed and generate research briefing."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to use the real PubMed connector
    articles = []
    try:
        from pubmed_connector import PubMedClient
        client = PubMedClient()
        articles = client.search_and_fetch(query, max_results=max_results)
    except Exception as e:
        # Fallback: generate a note about the failure
        articles = []
        error_msg = str(e)

    # Generate markdown report
    lines = [
        generate_report_header(
            f"Literature Briefing: {query}",
            "lit-reviewer",
            extra_metadata={
                "Query": query,
                "Source": "PubMed (NCBI Entrez)",
                "Results": str(len(articles)),
            },
        ),
    ]

    if articles:
        lines.append(f"## Found {len(articles)} papers\n")
        for i, art in enumerate(articles, 1):
            authors = format_authors(art.get("authors", []))
            pmid = art.get("pmid", "")
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            lines.append(f"### {i}. {art.get('title', 'Untitled')}\n")
            lines.append(f"**Authors**: {authors}\n")
            lines.append(f"**Journal**: {art.get('journal', 'N/A')} ({art.get('year', 'N/A')})\n")
            if url:
                lines.append(f"**PubMed**: [{pmid}]({url})\n")
            if art.get("doi"):
                lines.append(f"**DOI**: https://doi.org/{art['doi']}\n")
            if art.get("abstract"):
                # First 500 chars of abstract
                abstract = art["abstract"][:500]
                if len(art["abstract"]) > 500:
                    abstract += "..."
                lines.append(f"\n> {abstract}\n")
            if art.get("mesh_terms"):
                terms = ", ".join(art["mesh_terms"][:10])
                lines.append(f"**MeSH**: {terms}\n")
            lines.append("---\n")
    else:
        lines.append("## No results\n")
        lines.append("Could not retrieve articles from PubMed. This may be due to:\n")
        lines.append("- Network connectivity issues\n")
        lines.append("- NCBI rate limiting (set NCBI_API_KEY for higher limits)\n")
        lines.append("- No articles matching the query\n")

    lines.append(generate_report_footer())
    (output_dir / "report.md").write_text("\n".join(lines))

    # Generate HTML report
    html = HtmlReportBuilder("Literature Briefing", "lit-reviewer")
    html.add_header_block(f"Literature Briefing: {query}", f"{len(articles)} papers from PubMed")
    html.add_metadata({"Query": query, "Results": str(len(articles)), "Source": "PubMed"})

    if articles:
        headers = ["#", "Title", "Authors", "Journal", "Year"]
        rows = []
        for i, art in enumerate(articles, 1):
            rows.append([
                str(i),
                art.get("title", "")[:80],
                format_authors(art.get("authors", []), 2),
                art.get("journal", "N/A"),
                art.get("year", ""),
            ])
        html.add_table(headers, rows)

    html.add_disclaimer()
    html.add_footer_block("lit-reviewer", SKILL_VERSION)
    write_html_report(output_dir, "report.html", html.render())

    # Result JSON
    summary = {"query": query, "n_articles": len(articles), "source": "pubmed"}
    data = {"articles": articles}
    write_result_json(output_dir, "lit-reviewer", SKILL_VERSION, summary, data)

    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Lit-Reviewer — PubMed literature search")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo query")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10, help="Max articles (default: 10)")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args(argv)
    output_dir = Path(args.output)

    query = args.query or (DEMO_QUERY if args.demo else None)
    if query:
        result = run(query, output_dir, max_results=args.max_results, is_demo=args.demo)
    else:
        parser.error("Provide --query or use --demo.")
        return

    print(f"Literature briefing: {output_dir}/report.md")
    print(f"Query: {result['query']} → {result['n_articles']} articles")


if __name__ == "__main__":
    main()
