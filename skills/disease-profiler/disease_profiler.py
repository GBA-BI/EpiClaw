#!/usr/bin/env python3
"""Disease Profiler — Comprehensive disease research and profiling.

Usage:
    python disease_profiler.py --disease "Malaria" --output <dir>
    python disease_profiler.py --demo --output /tmp/disease_demo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json
from html_report import HtmlReportBuilder, write_html_report


SKILL_VERSION = "0.1.0"
DEMO_DISEASE = "Malaria"

# Built-in disease reference data for demo and offline use
DISEASE_DB = {
    "malaria": {
        "name": "Malaria",
        "pathogen": "Plasmodium falciparum, P. vivax, P. malariae, P. ovale, P. knowlesi",
        "icd10": "B50-B54",
        "transmission": "Mosquito-borne (Anopheles spp.)",
        "incubation": "7-30 days (varies by species)",
        "r0": "1-100+ (varies by setting)",
        "case_fatality": "0.1-0.3% (treated), 15-20% (severe, untreated)",
        "symptoms": "Fever, chills, headache, myalgia, fatigue, nausea; severe: cerebral malaria, anemia, organ failure",
        "diagnosis": "Microscopy (thick/thin blood smear), RDT, PCR",
        "treatment": "ACT (artemisinin-based combination therapy); severe: IV artesunate",
        "prevention": "ITNs, IRS, chemoprophylaxis, RTS,S/AS01 vaccine (Mosquirix), R21/Matrix-M vaccine",
        "global_burden": "~249 million cases, ~608,000 deaths (2022 WHO estimate)",
        "key_regions": "Sub-Saharan Africa (>90% of cases), South/Southeast Asia, South America",
        "who_indicators": ["MALARIA_EST_INCIDENCE", "MALARIA_EST_DEATHS"],
    },
    "tuberculosis": {
        "name": "Tuberculosis (TB)",
        "pathogen": "Mycobacterium tuberculosis",
        "icd10": "A15-A19",
        "transmission": "Airborne (respiratory droplets)",
        "incubation": "2-12 weeks (active disease may develop years later)",
        "r0": "~1-4",
        "case_fatality": "~50% (untreated), <5% (treated)",
        "symptoms": "Chronic cough, hemoptysis, weight loss, night sweats, fever, fatigue",
        "diagnosis": "Sputum smear microscopy, GeneXpert MTB/RIF, culture, TST, IGRA",
        "treatment": "6-month regimen: 2 months HRZE + 4 months HR; MDR-TB: bedaquiline-based",
        "prevention": "BCG vaccine, contact tracing, LTBI treatment, infection control",
        "global_burden": "~10.6 million cases, ~1.3 million deaths (2022 WHO estimate)",
        "key_regions": "India, Indonesia, China, Philippines, Pakistan, Nigeria, Bangladesh, DR Congo",
        "who_indicators": ["TB_e_inc_num", "TB_e_mort_exc_tbhiv_num"],
    },
}


def build_profile(disease_key: str, output_dir: Path) -> dict:
    """Build disease profile from built-in data and live connectors."""
    output_dir.mkdir(parents=True, exist_ok=True)

    info = DISEASE_DB.get(disease_key.lower(), None)
    if info is None:
        # Unknown disease — generate a minimal template
        info = {
            "name": disease_key.title(),
            "pathogen": "Unknown — data retrieval needed",
            "icd10": "Unknown",
            "transmission": "Unknown",
            "incubation": "Unknown",
            "r0": "Unknown",
            "case_fatality": "Unknown",
            "symptoms": "Unknown",
            "diagnosis": "Unknown",
            "treatment": "Unknown",
            "prevention": "Unknown",
            "global_burden": "Unknown — query WHO GHO for indicators",
            "key_regions": "Unknown",
            "who_indicators": [],
        }

    # Try to fetch WHO data
    who_data = {}
    try:
        from who_gho_connector import WHOClient
        client = WHOClient()
        for indicator in info.get("who_indicators", []):
            data = client.get_indicator(indicator)
            if data:
                who_data[indicator] = data[:5]  # Latest 5 records
    except Exception:
        pass

    # Try to fetch recent literature
    lit_articles = []
    try:
        from pubmed_connector import PubMedClient
        client = PubMedClient()
        lit_articles = client.search_and_fetch(
            f"{info['name']} epidemiology", max_results=5
        )
    except Exception:
        pass

    # Generate report
    lines = [
        generate_report_header(
            f"Disease Profile: {info['name']}",
            "disease-profiler",
            extra_metadata={"ICD-10": info.get("icd10", "N/A")},
        ),
        "## 1. Overview\n",
        f"- **Disease**: {info['name']}\n",
        f"- **Pathogen**: {info['pathogen']}\n",
        f"- **ICD-10**: {info['icd10']}\n",
        f"- **Global burden**: {info['global_burden']}\n",
        f"- **Key regions**: {info['key_regions']}\n",
        "\n## 2. Transmission & Epidemiology\n",
        f"- **Transmission**: {info['transmission']}\n",
        f"- **Incubation period**: {info['incubation']}\n",
        f"- **Basic reproduction number (R₀)**: {info['r0']}\n",
        f"- **Case fatality rate**: {info['case_fatality']}\n",
        "\n## 3. Clinical Presentation\n",
        f"- **Symptoms**: {info['symptoms']}\n",
        f"- **Diagnosis**: {info['diagnosis']}\n",
        "\n## 4. Treatment\n",
        f"{info['treatment']}\n",
        "\n## 5. Prevention\n",
        f"{info['prevention']}\n",
    ]

    if who_data:
        lines.append("\n## 6. WHO Global Health Observatory Data\n")
        for indicator, records in who_data.items():
            lines.append(f"\n### {indicator}\n")
            if records:
                lines.append("| Country | Year | Value |\n|---------|------|-------|\n")
                for r in records[:10]:
                    lines.append(
                        f"| {r.get('SpatialDim', 'N/A')} | {r.get('TimeDim', 'N/A')} | "
                        f"{r.get('NumericValue', 'N/A')} |\n"
                    )

    if lit_articles:
        lines.append("\n## 7. Recent Literature\n")
        for i, art in enumerate(lit_articles, 1):
            authors = ", ".join(art.get("authors", [])[:3])
            if len(art.get("authors", [])) > 3:
                authors += " et al."
            lines.append(f"{i}. **{art.get('title', '')}** — {authors} "
                         f"({art.get('journal', '')}, {art.get('year', '')})\n")

    lines.append(generate_report_footer())
    (output_dir / "report.md").write_text("\n".join(lines))

    # HTML report
    html = HtmlReportBuilder("Disease Profile", "disease-profiler")
    html.add_header_block(f"Disease Profile: {info['name']}", info.get("pathogen", ""))
    html.add_metadata({
        "ICD-10": info.get("icd10", "N/A"),
        "Transmission": info.get("transmission", "N/A"),
        "R₀": str(info.get("r0", "N/A")),
        "Global Burden": info.get("global_burden", "N/A"),
    })
    html.add_disclaimer()
    html.add_footer_block("disease-profiler", SKILL_VERSION)
    write_html_report(output_dir, "report.html", html.render())

    # Result JSON
    summary = {
        "disease": info["name"],
        "who_indicators_fetched": len(who_data),
        "literature_articles": len(lit_articles),
    }
    write_result_json(output_dir, "disease-profiler", SKILL_VERSION, summary, info)

    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Disease Profiler — comprehensive disease research")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo disease profile")
    parser.add_argument("--disease", help="Disease name (e.g., Malaria, Tuberculosis)")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args(argv)
    output_dir = Path(args.output)

    disease = args.disease or (DEMO_DISEASE if args.demo else None)
    if disease:
        result = build_profile(disease, output_dir)
    else:
        parser.error("Provide --disease or use --demo.")
        return

    print(f"Disease profile: {output_dir}/report.md")
    print(f"Disease: {result['disease']}")


if __name__ == "__main__":
    main()
