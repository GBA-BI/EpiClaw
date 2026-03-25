#!/usr/bin/env python3
"""Epi-Analyst — Core epidemiological analysis agent.

Usage:
    python epi_analyst.py --framework outbreak --pathogen Salmonella --output <dir>
    python epi_analyst.py --framework bradford-hill --topic "smoking and cancer" --output <dir>
    python epi_analyst.py --demo --output /tmp/epi_demo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


SKILL_VERSION = "0.1.0"

FRAMEWORKS = {
    "outbreak": "CDC 10-Step Outbreak Investigation",
    "bradford-hill": "Bradford Hill Criteria for Causal Inference",
    "surveillance": "Disease Surveillance System Design",
    "study-design": "Epidemiological Study Design Selection",
    "measures": "Measures of Disease Frequency and Association",
}

BRADFORD_HILL_CRITERIA = [
    ("Strength", "Large magnitude of association (RR/OR)?"),
    ("Consistency", "Observed across different studies, populations, settings?"),
    ("Specificity", "Exposure linked to specific disease outcome?"),
    ("Temporality", "Exposure precedes disease? (REQUIRED for causation)"),
    ("Biological gradient", "Dose-response relationship observed?"),
    ("Plausibility", "Biologically plausible mechanism exists?"),
    ("Coherence", "Consistent with known biology of the disease?"),
    ("Experiment", "Experimental evidence supports the association?"),
    ("Analogy", "Similar exposure-disease relationships known?"),
]

CDC_OUTBREAK_STEPS = [
    "Prepare for field work",
    "Establish the existence of an outbreak",
    "Verify the diagnosis",
    "Define and identify cases",
    "Describe data by person, place, and time",
    "Develop hypotheses",
    "Evaluate hypotheses analytically",
    "Refine hypotheses and additional studies",
    "Implement control and prevention measures",
    "Communicate findings",
]


def generate_outbreak_report(pathogen: str, output_dir: Path) -> dict:
    """Generate an outbreak investigation template report."""
    lines = [
        generate_report_header(
            f"Outbreak Investigation: {pathogen}",
            "epi-analyst",
            extra_metadata={"Framework": "CDC 10-Step Outbreak Investigation", "Pathogen": pathogen},
        ),
        "## CDC 10-Step Outbreak Investigation Framework\n",
    ]

    for i, step in enumerate(CDC_OUTBREAK_STEPS, 1):
        lines.append(f"### Step {i}: {step}\n")
        lines.append(f"**Status**: Pending\n")
        lines.append(f"**Actions needed**:\n- [ ] TODO\n")
        lines.append(f"**Findings**: _To be completed_\n")

    lines.append("\n## Case Definition\n")
    lines.append(f"| Level | Criteria |\n|-------|----------|\n")
    lines.append(f"| Confirmed | Laboratory-confirmed {pathogen} infection |\n")
    lines.append(f"| Probable | Clinically compatible + epidemiological link |\n")
    lines.append(f"| Suspected | Clinically compatible illness |\n")

    lines.append("\n## Key Metrics to Track\n")
    lines.append("- Attack rate (overall and by exposure)\n")
    lines.append("- Case fatality rate\n")
    lines.append("- Secondary attack rate\n")
    lines.append("- Incubation period distribution\n")
    lines.append("- Epidemic curve (epi curve)\n")

    lines.append(generate_report_footer())
    report = "\n".join(lines)
    (output_dir / "report.md").write_text(report)

    summary = {
        "framework": "outbreak",
        "pathogen": pathogen,
        "steps": len(CDC_OUTBREAK_STEPS),
        "status": "template_generated",
    }
    write_result_json(output_dir, "epi-analyst", SKILL_VERSION, summary, {"steps": CDC_OUTBREAK_STEPS})
    return summary


def generate_bradford_hill_report(topic: str, output_dir: Path) -> dict:
    """Generate a Bradford Hill criteria assessment template."""
    lines = [
        generate_report_header(
            f"Causal Inference Assessment: {topic}",
            "epi-analyst",
            extra_metadata={"Framework": "Bradford Hill Criteria", "Topic": topic},
        ),
        "## Bradford Hill Criteria Assessment\n",
        "| # | Criterion | Question | Assessment | Evidence |\n",
        "|---|-----------|----------|------------|----------|\n",
    ]

    for i, (criterion, question) in enumerate(BRADFORD_HILL_CRITERIA, 1):
        required = " **(REQUIRED)**" if criterion == "Temporality" else ""
        lines.append(f"| {i} | {criterion}{required} | {question} | _Pending_ | _Cite evidence_ |\n")

    lines.append("\n## Summary Assessment\n")
    lines.append("- **Criteria met**: _/9\n")
    lines.append("- **Criteria partially met**: _/9\n")
    lines.append("- **Overall causal inference**: _Pending review_\n")
    lines.append("\n> **Note**: Temporality is the only criterion that is absolutely required. ")
    lines.append("The remaining criteria strengthen the case for causation but are not individually necessary.\n")

    lines.append(generate_report_footer())
    report = "\n".join(lines)
    (output_dir / "report.md").write_text(report)

    summary = {
        "framework": "bradford-hill",
        "topic": topic,
        "criteria_count": len(BRADFORD_HILL_CRITERIA),
        "status": "template_generated",
    }
    write_result_json(
        output_dir, "epi-analyst", SKILL_VERSION, summary,
        {"criteria": [{"name": c, "question": q} for c, q in BRADFORD_HILL_CRITERIA]},
    )
    return summary


def generate_surveillance_report(output_dir: Path) -> dict:
    """Generate a surveillance system design framework report."""
    lines = [
        generate_report_header(
            "Disease Surveillance System Design",
            "epi-analyst",
            extra_metadata={"Framework": "Surveillance System Design"},
        ),
        "## Surveillance System Types\n",
        "| Type | Description | Strengths | Limitations | Best For |\n",
        "|------|-------------|-----------|-------------|----------|\n",
        "| Passive | Routine provider reporting | Low cost, wide coverage | Underreporting | Notifiable diseases |\n",
        "| Active | Systematic case finding | Complete, timely | Resource intensive | Outbreaks, elimination targets |\n",
        "| Syndromic | Pre-diagnostic symptoms | Early warning | Low specificity | Bioterrorism, novel threats |\n",
        "| Sentinel | Selected enhanced sites | High quality | Not representative | Influenza, AMR |\n",
        "| Wastewater | Environmental detection | Population-level, unbiased | Cannot ID individuals | COVID-19, polio |\n",
        "\n## Evaluation Criteria (CDC Updated Guidelines)\n",
        "1. **Usefulness** — Does it contribute to prevention and control?\n",
        "2. **Simplicity** — Is the system easy to operate?\n",
        "3. **Flexibility** — Can it adapt to changing needs?\n",
        "4. **Data quality** — Are data complete and valid?\n",
        "5. **Acceptability** — Are stakeholders willing to participate?\n",
        "6. **Sensitivity** — What proportion of cases detected?\n",
        "7. **Predictive value positive** — Of those flagged, how many are true cases?\n",
        "8. **Representativeness** — Does it accurately describe disease by person, place, time?\n",
        "9. **Timeliness** — Speed from event to public health action?\n",
        "10. **Stability** — Reliable operation over time?\n",
    ]

    lines.append(generate_report_footer())
    report = "\n".join(lines)
    (output_dir / "report.md").write_text(report)

    summary = {"framework": "surveillance", "status": "template_generated"}
    write_result_json(output_dir, "epi-analyst", SKILL_VERSION, summary, {})
    return summary


def run_demo(output_dir: Path) -> dict:
    """Default demo uses an outbreak template."""
    return generate_outbreak_report("Salmonella", output_dir)

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Epi-Analyst — Core epidemiological analysis")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo mode")
    parser.add_argument("--framework", choices=list(FRAMEWORKS.keys()),
                        help="Analytical framework to apply")
    parser.add_argument("--pathogen", help="Pathogen name (for outbreak framework)")
    parser.add_argument("--topic", help="Topic (for bradford-hill framework)")
    parser.add_argument("--input", help="Input file (CSV with case data)")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo:
        result = run_demo(output_dir)
    elif args.framework == "outbreak":
        pathogen = args.pathogen or "Unknown Pathogen"
        result = generate_outbreak_report(pathogen, output_dir)
    elif args.framework == "bradford-hill":
        topic = args.topic or "Exposure and Disease"
        result = generate_bradford_hill_report(topic, output_dir)
    elif args.framework == "surveillance":
        result = generate_surveillance_report(output_dir)
    elif args.framework:
        # For other frameworks, generate a generic template
        result = generate_surveillance_report(output_dir)
    else:
        # Default: outbreak investigation template
        result = run_demo(output_dir)

    print(f"Epi-Analyst report generated: {output_dir}/report.md")
    print(f"Framework: {result.get('framework', 'demo')}")


if __name__ == "__main__":
    main()
