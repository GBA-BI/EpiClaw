#!/usr/bin/env python3
"""Outbreak Investigator — Linelist analysis, epi curves, and attack rates.

Usage:
    python outbreak_investigator.py --input linelist.csv --output <dir>
    python outbreak_investigator.py --demo --output /tmp/demo
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta
from io import StringIO
import sys
from pathlib import Path
from random import Random

from reporting import generate_report_header, generate_report_footer, write_result_json


SKILL_VERSION = "0.1.0"


def generate_demo_linelist() -> list[dict]:
    """Generate a synthetic foodborne outbreak linelist."""
    rng = Random(42)
    base_date = datetime(2025, 6, 15)
    exposures = ["potato_salad", "chicken", "water", "cake"]
    cases = []

    for i in range(60):
        onset = base_date + timedelta(hours=rng.gauss(48, 18))
        ate_potato = rng.random() < 0.75 if i < 45 else rng.random() < 0.30
        ill = (ate_potato and rng.random() < 0.65) or (not ate_potato and rng.random() < 0.10)
        cases.append({
            "case_id": f"C{i+1:03d}",
            "onset_date": onset.strftime("%Y-%m-%d %H:%M") if ill else "",
            "age": rng.randint(5, 85),
            "sex": rng.choice(["M", "F"]),
            "potato_salad": "Yes" if ate_potato else "No",
            "chicken": "Yes" if rng.random() < 0.6 else "No",
            "water": "Yes" if rng.random() < 0.9 else "No",
            "cake": "Yes" if rng.random() < 0.4 else "No",
            "ill": "Yes" if ill else "No",
            "outcome": rng.choice(["recovered", "recovered", "recovered", "hospitalized"]) if ill else "well",
        })
    return cases


def load_linelist(filepath: str) -> list[dict]:
    """Load linelist from CSV file."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def compute_epi_curve(cases: list[dict], date_field: str = "onset_date") -> dict[str, int]:
    """Compute daily case counts for epidemic curve."""
    dates = []
    for c in cases:
        d = c.get(date_field, "")
        if d:
            try:
                dt = datetime.strptime(d[:10], "%Y-%m-%d")
                dates.append(dt.strftime("%Y-%m-%d"))
            except ValueError:
                continue
    return dict(sorted(Counter(dates).items()))


def compute_attack_rates(cases: list[dict], exposures: list[str]) -> list[dict]:
    """Compute food-specific attack rates."""
    results = []
    for exp in exposures:
        exposed_ill = sum(1 for c in cases if c.get(exp) == "Yes" and c.get("ill") == "Yes")
        exposed_total = sum(1 for c in cases if c.get(exp) == "Yes")
        unexposed_ill = sum(1 for c in cases if c.get(exp) == "No" and c.get("ill") == "Yes")
        unexposed_total = sum(1 for c in cases if c.get(exp) == "No")

        ar_exposed = exposed_ill / exposed_total if exposed_total else 0
        ar_unexposed = unexposed_ill / unexposed_total if unexposed_total else 0
        rr = ar_exposed / ar_unexposed if ar_unexposed > 0 else float("inf")

        results.append({
            "exposure": exp,
            "exposed_ill": exposed_ill,
            "exposed_total": exposed_total,
            "attack_rate_exposed": round(ar_exposed * 100, 1),
            "unexposed_ill": unexposed_ill,
            "unexposed_total": unexposed_total,
            "attack_rate_unexposed": round(ar_unexposed * 100, 1),
            "risk_ratio": round(rr, 2) if rr != float("inf") else "undefined",
        })
    return results


def generate_epi_curve_ascii(curve: dict[str, int], width: int = 50) -> str:
    """Generate ASCII art epidemic curve."""
    if not curve:
        return "No cases with onset dates.\n"
    max_count = max(curve.values())
    scale = width / max_count if max_count > 0 else 1
    lines = ["```"]
    for date, count in curve.items():
        bar = "█" * int(count * scale)
        lines.append(f"{date} | {bar} {count}")
    lines.append("```")
    return "\n".join(lines)


def describe_cases(cases: list[dict]) -> dict:
    """Generate descriptive epidemiology summary."""
    ill_cases = [c for c in cases if c.get("ill") == "Yes"]
    total = len(cases)
    n_ill = len(ill_cases)

    ages = [int(c["age"]) for c in ill_cases if c.get("age")]
    sexes = Counter(c.get("sex", "Unknown") for c in ill_cases)
    outcomes = Counter(c.get("outcome", "unknown") for c in ill_cases)

    return {
        "total_persons": total,
        "total_cases": n_ill,
        "overall_attack_rate": round(n_ill / total * 100, 1) if total else 0,
        "age_range": f"{min(ages)}-{max(ages)}" if ages else "N/A",
        "median_age": sorted(ages)[len(ages) // 2] if ages else "N/A",
        "sex_distribution": dict(sexes),
        "outcomes": dict(outcomes),
    }


def run(cases: list[dict], output_dir: Path, is_demo: bool = False) -> dict:
    """Main analysis pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    # Descriptive epi
    desc = describe_cases(cases)

    # Epidemic curve
    epi_curve = compute_epi_curve(cases)

    # Detect exposure columns (columns with Yes/No values, excluding 'ill')
    exposure_cols = []
    if cases:
        for key in cases[0].keys():
            if key in ("case_id", "onset_date", "age", "sex", "ill", "outcome"):
                continue
            vals = {c.get(key, "") for c in cases}
            if vals <= {"Yes", "No", ""}:
                exposure_cols.append(key)

    # Attack rates
    attack_rates = compute_attack_rates(cases, exposure_cols) if exposure_cols else []

    # Generate epi curve plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if epi_curve:
            fig, ax = plt.subplots(figsize=(10, 4))
            dates = list(epi_curve.keys())
            counts = list(epi_curve.values())
            ax.bar(range(len(dates)), counts, color="#00897b", edgecolor="white")
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)
            ax.set_xlabel("Date of Onset")
            ax.set_ylabel("Number of Cases")
            ax.set_title("Epidemic Curve")
            plt.tight_layout()
            fig.savefig(figures_dir / "epi_curve.png", dpi=150)
            plt.close(fig)
    except ImportError:
        pass  # matplotlib optional

    # Generate report
    source = "Synthetic demo data" if is_demo else "User-provided linelist"
    lines = [
        generate_report_header(
            "Outbreak Investigation Report",
            "outbreak-investigator",
            extra_metadata={"Data source": source},
        ),
        "## Descriptive Epidemiology\n",
        f"- **Total persons**: {desc['total_persons']}\n",
        f"- **Total cases**: {desc['total_cases']}\n",
        f"- **Overall attack rate**: {desc['overall_attack_rate']}%\n",
        f"- **Age range**: {desc['age_range']} (median: {desc['median_age']})\n",
        f"- **Sex distribution**: {desc['sex_distribution']}\n",
        f"- **Outcomes**: {desc['outcomes']}\n",
        "\n## Epidemic Curve\n",
        generate_epi_curve_ascii(epi_curve),
        "\n![Epidemic Curve](figures/epi_curve.png)\n" if (figures_dir / "epi_curve.png").exists() else "",
    ]

    if attack_rates:
        lines.append("\n## Food-Specific Attack Rates\n")
        lines.append("| Exposure | Exposed Ill/Total | AR (Exposed) | Unexposed Ill/Total | AR (Unexposed) | RR |\n")
        lines.append("|----------|-------------------|--------------|---------------------|----------------|----|")
        for ar in attack_rates:
            lines.append(
                f"| {ar['exposure']} | {ar['exposed_ill']}/{ar['exposed_total']} | "
                f"{ar['attack_rate_exposed']}% | {ar['unexposed_ill']}/{ar['unexposed_total']} | "
                f"{ar['attack_rate_unexposed']}% | {ar['risk_ratio']} |"
            )

        # Highlight highest RR
        valid_rr = [ar for ar in attack_rates if isinstance(ar["risk_ratio"], (int, float))]
        if valid_rr:
            top = max(valid_rr, key=lambda x: x["risk_ratio"])
            lines.append(f"\n**Strongest association**: {top['exposure']} (RR = {top['risk_ratio']})\n")

    lines.append(generate_report_footer())
    (output_dir / "report.md").write_text("\n".join(lines))

    summary = {**desc, "exposures_tested": len(attack_rates)}
    data = {
        "descriptive": desc,
        "epi_curve": epi_curve,
        "attack_rates": attack_rates,
    }
    write_result_json(output_dir, "outbreak-investigator", SKILL_VERSION, summary, data)

    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Outbreak Investigator — linelist analysis")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo linelist")
    parser.add_argument("--input", help="Input linelist CSV file")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--pathogen", help="Pathogen name (for report title)")
    args = parser.parse_args(argv)
    output_dir = Path(args.output)

    if args.demo or not args.input:
        cases = generate_demo_linelist()
        result = run(cases, output_dir, is_demo=True)
    elif args.input:
        cases = load_linelist(args.input)
        result = run(cases, output_dir, is_demo=False)
    else:
        parser.error("Provide --input.")
        return

    print(f"Outbreak report: {output_dir}/report.md")
    print(f"Cases: {result['total_cases']}/{result['total_persons']} (AR: {result['overall_attack_rate']}%)")


if __name__ == "__main__":
    main()
