#!/usr/bin/env python3
"""EpiClaw Pathogen-Intel -- Pathogen intelligence brief: taxonomy, epidemiology, emergence risk."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "pathogen-intel"


# ---------------------------------------------------------------------------
# Demo / hardcoded data
# ---------------------------------------------------------------------------

NIPAH_PROFILE: dict = {
    "taxonomy": {
        "family": "Paramyxoviridae",
        "genus": "Henipavirus",
        "species": "Nipah henipavirus",
        "genome": "Negative-sense single-stranded RNA",
        "size_nm": "150–300",
    },
    "epidemiology": {
        "natural_reservoir": "Pteropus fruit bats (flying foxes)",
        "transmission_routes": [
            "Animal-to-human (direct contact with infected bats, pigs, or their excretions)",
            "Human-to-human (close contact, limited; documented in Bangladesh/India outbreaks)",
            "Consumption of raw date palm sap contaminated by bat urine/saliva",
        ],
        "geographic_range": "South and Southeast Asia (Bangladesh, India, Malaysia, Singapore, Philippines)",
        "last_outbreak": "2023 Kerala, India (6 cases, 2 deaths)",
        "who_priority_pathogen": True,
        "who_r_and_d_blueprint": True,
    },
    "clinical": {
        "incubation_period": "4–21 days",
        "cfr_range": "40–75%",
        "clinical_presentation": [
            "Fever, headache, dizziness (prodrome)",
            "Acute encephalitis (inflammation of the brain)",
            "Respiratory illness in some cases",
            "Long-term neurological sequelae in survivors",
        ],
        "treatment": "Supportive care; ribavirin and monoclonal antibody m102.4 investigated",
    },
    "prevention": {
        "vaccine_status": "None approved; phase II candidates (including Hendra virus vaccine cross-protection)",
        "prophylaxis": "None approved",
        "control_measures": [
            "Avoid contact with sick animals and bat habitats",
            "Do not drink raw date palm sap",
            "Standard infection prevention and control (PPE for healthcare workers)",
            "Contact tracing and isolation of cases",
        ],
    },
    "risk_assessment": {
        "zoonotic_potential": "high",
        "emergence_risk_score": 0.82,
        "emergence_risk_label": "high",
        "pandemic_potential": "moderate-high",
        "notes": (
            "Nipah virus is a WHO R&D Blueprint priority pathogen. "
            "High CFR, ability for limited human-to-human transmission, "
            "and no approved vaccine or treatment make it a significant pandemic threat."
        ),
    },
}


# ---------------------------------------------------------------------------
# Connector integration (best-effort)
# ---------------------------------------------------------------------------

def _try_fetch_pubmed_count(pathogen: str) -> int:
    """Attempt to count PubMed articles for pathogen. Returns 0 on failure."""
    try:
        from pubmed_connector import PubMedClient

        client = PubMedClient()
        return len(client.search(query=pathogen, max_results=1))
    except Exception:
        return 0


def _try_fetch_who_data(pathogen: str) -> dict:
    """Attempt to fetch WHO GHO data for pathogen. Returns empty dict on failure."""
    try:
        from who_gho_connector import WHOClient

        client = WHOClient()
        indicators = client.search_indicators(pathogen, max_results=5)
        if not indicators:
            return {}
        return {
            "taxonomy": {"matched_indicators": indicators},
            "epidemiology": {"indicator_count": len(indicators)},
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Profile selection
# ---------------------------------------------------------------------------

def get_profile(pathogen: str | None, demo: bool = False) -> tuple[str, dict, int, bool]:
    """Return (pathogen_name, profile_dict, pubmed_count, is_demo)."""
    if demo or pathogen is None or pathogen.lower() in ("nipah", "nipah virus"):
        return "Nipah virus", NIPAH_PROFILE, 0, True

    # For real pathogen: try connectors, fall back to minimal stub
    pubmed_count = _try_fetch_pubmed_count(pathogen)
    who_data = _try_fetch_who_data(pathogen)

    stub_profile: dict = {
        "taxonomy": who_data.get("taxonomy", {"note": "[live data not available for default profile]"}),
        "epidemiology": who_data.get("epidemiology", {"note": "[live fetch attempted]"}),
        "clinical": who_data.get("clinical", {"note": "[live fetch attempted]"}),
        "prevention": who_data.get("prevention", {"note": "[live fetch attempted]"}),
        "risk_assessment": {
            "zoonotic_potential": "unknown",
            "emergence_risk_score": 0.0,
            "emergence_risk_label": "unknown",
            "pandemic_potential": "unknown",
            "notes": f"[demo] Live connector data for {pathogen!r} not fully available.",
        },
    }
    return pathogen, stub_profile, pubmed_count, False


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_report(
    output_dir: Path,
    pathogen_name: str,
    profile: dict,
    pubmed_count: int,
    is_demo: bool,
    country: str | None,

):
    header = generate_report_header(
        title="Pathogen Intelligence Brief",
        skill_name=SKILL_NAME,
        extra_metadata={"Pathogen": pathogen_name, "Country": country or "N/A", "Version": VERSION},
    )
    lines = [
        "## Taxonomy",
        "",
        json.dumps(profile.get("taxonomy", {}), indent=2),
        "",
        "## Epidemiology",
        "",
        json.dumps(profile.get("epidemiology", {}), indent=2),
        "",
        "## Clinical",
        "",
        json.dumps(profile.get("clinical", {}), indent=2),
        "",
        "## Prevention",
        "",
        json.dumps(profile.get("prevention", {}), indent=2),
        "",
        "## Risk Assessment",
        "",
        json.dumps(profile.get("risk_assessment", {}), indent=2),
        "",
        f"PubMed count (best effort): `{pubmed_count}`",
        f"Demo mode: `{is_demo}`",
        "",
        generate_report_footer(),
    ]
    (output_dir / "report.md").write_text(header + "\n".join(lines), encoding="utf-8")
    write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary={
            "pathogen": pathogen_name,
            "emergence_risk_score": profile.get("risk_assessment", {}).get("emergence_risk_score", 0.0),
            "pubmed_count": pubmed_count,
        },
        data=profile,
    )
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="EpiClaw Pathogen-Intel: pathogen intelligence brief."
    )
    parser.add_argument(
        "--pathogen",
        default=None,
        help="Pathogen name (required unless --demo)",
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demo profile")
    parser.add_argument("--country", default=None, help="Country filter (optional)")
    parser.add_argument("--output", default="/tmp/epiclaw_pathogen_intel", help="Output directory")
    args = parser.parse_args(argv)
    if args.pathogen is None and not args.demo:
        print("[info] No --pathogen specified: switching to demo mode (Nipah virus).")
        args.demo = True

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw Pathogen-Intel v{VERSION}")

    pathogen_name, profile, pubmed_count, is_demo = get_profile(args.pathogen, args.demo)
    print(f"[info] Profiling: {pathogen_name}")
    if is_demo:
        print("[info] Using hardcoded demo data for Nipah virus.")
    else:
        print("[info] Attempting live connector data fetch...")
        if pubmed_count > 0:
            print(f"[info] PubMed: {pubmed_count} article(s) found.")
        else:
            print("[info] PubMed connector not available or returned 0 results.")

    print("[info] Building intelligence brief...")
    build_report(
        output_dir=output_dir,
        pathogen_name=pathogen_name,
        profile=profile,
        pubmed_count=pubmed_count,
        is_demo=is_demo,
        country=args.country,
    )

    print(f"[info] Done. Output: {output_dir}/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
