#!/usr/bin/env python3
"""EpiClaw Travel Health -- destination risk and vaccine guidance."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "travel-health"

COUNTRY_PROFILES = {
    "THA": {"vaccines": ["Hepatitis A", "Typhoid", "Rabies (consider)"], "malaria": "Selective risk; atovaquone-proguanil or doxycycline for border/rural travel", "diseases": {"dengue": "high", "malaria": "medium", "typhoid": "medium"}},
    "KEN": {"vaccines": ["Yellow fever", "Hepatitis A", "Typhoid", "Rabies (consider)"], "malaria": "High risk outside Nairobi/highlands; atovaquone-proguanil or doxycycline", "diseases": {"malaria": "high", "yellow_fever": "high", "dengue": "low"}},
    "IND": {"vaccines": ["Hepatitis A", "Typhoid", "Rabies (consider)", "Japanese encephalitis (consider)"], "malaria": "Variable risk; prophylaxis for forested/rural zones", "diseases": {"typhoid": "high", "dengue": "high", "malaria": "medium"}},
    "BRA": {"vaccines": ["Yellow fever (region dependent)", "Hepatitis A", "Typhoid"], "malaria": "Amazon basin risk; atovaquone-proguanil or doxycycline", "diseases": {"yellow_fever": "medium", "dengue": "high", "malaria": "medium"}},
}


def run_assessment(destination: str, duration: int, immunocompromised: bool, pregnant: bool) -> tuple[dict, dict]:
    profile = COUNTRY_PROFILES.get(destination.upper())
    if profile is None:
        raise RuntimeError(f"No curated travel-health profile for destination: {destination}")
    multiplier = 1.0 if duration < 14 else (1.5 if duration <= 56 else 2.0)
    precautions = [
        "Strict food and water hygiene",
        "Mosquito bite avoidance",
        "Travel insurance and fever contingency plan",
    ]
    if immunocompromised:
        precautions.append("Review live vaccine contraindications with a travel medicine clinician")
    if pregnant:
        precautions.append("Confirm pregnancy-specific vaccine and malaria prophylaxis safety")
    risk_matrix = {disease: {"level": level, "duration_multiplier": multiplier} for disease, level in profile["diseases"].items()}
    summary = {
        "destination": destination.upper(),
        "duration_days": duration,
        "risk_multiplier": multiplier,
        "n_vaccines": len(profile["vaccines"]),
        "malaria_guidance": profile["malaria"],
    }
    data = {
        "vaccines": profile["vaccines"],
        "risk_matrix": risk_matrix,
        "precautions": precautions,
    }
    return summary, data


def generate_report(output_path: Path, summary: dict, data: dict) -> None:
    header = generate_report_header(title="Travel Health Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION})
    lines = [
        "## Destination Summary",
        "",
        f"- Destination: `{summary['destination']}`",
        f"- Duration: `{summary['duration_days']}` days",
        f"- Risk multiplier: `{summary['risk_multiplier']}`",
        f"- Malaria guidance: {summary['malaria_guidance']}",
        "",
        "## Vaccine Checklist",
        "",
    ]
    for vaccine in data["vaccines"]:
        lines.append(f"- {vaccine}")
    lines.extend(["", "## Disease Risk Matrix", "", "| Disease | Risk | Multiplier |", "|---|---|---|"])
    for disease, detail in sorted(data["risk_matrix"].items()):
        lines.append(f"| {disease} | {detail['level']} | {detail['duration_multiplier']} |")
    lines.extend(["", "## Precautions", ""])
    for precaution in data["precautions"]:
        lines.append(f"- {precaution}")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Travel Health -- curated destination health assessment.")
    parser.add_argument("--destination", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--demo", action="store_true", help="Run built-in demo destination")
    parser.add_argument("--duration", type=int, default=14)
    parser.add_argument("--immunocompromised", action="store_true")
    parser.add_argument("--pregnant", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.destination or ("THA" if args.demo else None)
    if not destination:
        raise SystemExit("[error] Provide --destination or use --demo")
    summary, data = run_assessment(destination, args.duration, args.immunocompromised, args.pregnant)
    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
