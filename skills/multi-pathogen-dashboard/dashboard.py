#!/usr/bin/env python3
"""Multi-Pathogen Dashboard — Surveillance trend aggregation and visualization.

Usage:
    python dashboard.py --input surveillance.csv --output <dir>
    python dashboard.py --demo --output /tmp/dashboard
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from random import Random

from reporting import generate_report_header, generate_report_footer, write_result_json
from html_report import HtmlReportBuilder, write_html_report


SKILL_VERSION = "0.1.0"


def build_demo_data() -> dict[str, list[dict]]:
    """Return synthetic weekly surveillance data for four pathogens."""
    rng = Random(42)
    configs = {
        "Influenza A": (120, 8),
        "RSV": (85, 6),
        "Norovirus": (55, 10),
        "COVID-19": (95, 7),
    }
    data: dict[str, list[dict]] = {}
    for pathogen, (baseline, swing) in configs.items():
        weekly = []
        for week in range(1, 13):
            drift = week - 6 if pathogen in {"COVID-19", "Norovirus"} else 6 - week
            cases = max(1, baseline + drift * swing + rng.randint(-8, 8))
            weekly.append({"week": week, "year": 2025, "cases": cases})
        data[pathogen] = weekly
    return data

def compute_trends(data: dict[str, list[dict]]) -> dict[str, dict]:
    """Compute trend metrics for each pathogen."""
    trends = {}
    for pathogen, weekly in data.items():
        cases = [w["cases"] for w in weekly]
        total = sum(cases)
        peak = max(cases)
        peak_week = cases.index(peak) + 1
        recent_4 = sum(cases[-4:])
        prev_4 = sum(cases[-8:-4]) if len(cases) >= 8 else sum(cases[:4])
        pct_change = ((recent_4 - prev_4) / prev_4 * 100) if prev_4 > 0 else 0

        trends[pathogen] = {
            "total_cases": total,
            "peak_cases": peak,
            "peak_week": peak_week,
            "recent_4wk": recent_4,
            "prev_4wk": prev_4,
            "pct_change_4wk": round(pct_change, 1),
            "trend": "increasing" if pct_change > 10 else "decreasing" if pct_change < -10 else "stable",
        }
    return trends


def run(data: dict[str, list[dict]], output_dir: Path, is_demo: bool = False) -> dict:
    """Generate multi-pathogen dashboard."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    trends = compute_trends(data)

    # Generate trend plots
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        colors = ["#00897b", "#e53935", "#1565c0", "#ff8f00"]
        fig, ax = plt.subplots(figsize=(12, 5))
        for i, (pathogen, weekly) in enumerate(data.items()):
            weeks = [w["week"] for w in weekly]
            cases = [w["cases"] for w in weekly]
            ax.plot(weeks, cases, label=pathogen, color=colors[i % len(colors)], linewidth=2)
        ax.set_xlabel("Epidemiological Week")
        ax.set_ylabel("Cases")
        ax.set_title("Multi-Pathogen Surveillance Trends (2025)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        fig.savefig(figures_dir / "trends.png", dpi=150)
        plt.close(fig)
    except ImportError:
        pass

    # Markdown report
    source = "Synthetic demo data" if is_demo else "User-provided data"
    lines = [
        generate_report_header(
            "Multi-Pathogen Surveillance Dashboard",
            "multi-pathogen-dashboard",
            extra_metadata={"Data source": source, "Pathogens": str(len(data))},
        ),
        "## Trend Summary\n",
        "| Pathogen | Total Cases | Peak (Week) | 4-Week Trend | Change |\n",
        "|----------|-------------|-------------|--------------|--------|\n",
    ]
    for pathogen, t in trends.items():
        arrow = "↑" if t["trend"] == "increasing" else "↓" if t["trend"] == "decreasing" else "→"
        lines.append(
            f"| {pathogen} | {t['total_cases']:,} | {t['peak_cases']:,} (Wk {t['peak_week']}) | "
            f"{arrow} {t['trend']} | {t['pct_change_4wk']:+.1f}% |\n"
        )

    # Alerts
    alerts = [(p, t) for p, t in trends.items() if t["pct_change_4wk"] > 20]
    if alerts:
        lines.append("\n## Alerts\n")
        for pathogen, t in alerts:
            lines.append(f"- **{pathogen}**: {t['pct_change_4wk']:+.1f}% increase over 4 weeks\n")

    if (figures_dir / "trends.png").exists():
        lines.append("\n## Trends\n")
        lines.append("![Multi-Pathogen Trends](figures/trends.png)\n")

    lines.append(generate_report_footer())
    (output_dir / "report.md").write_text("\n".join(lines))

    # HTML dashboard
    html = HtmlReportBuilder("Surveillance Dashboard", "multi-pathogen-dashboard")
    html.add_header_block("Multi-Pathogen Surveillance Dashboard", f"{len(data)} pathogens tracked")

    cards = []
    for pathogen, t in trends.items():
        severity = "critical" if t["pct_change_4wk"] > 20 else "warning" if t["pct_change_4wk"] > 10 else "normal"
        cards.append((pathogen, t["total_cases"], severity))
    html.add_summary_cards(cards)

    headers = ["Pathogen", "Total", "Peak", "Peak Week", "4-Week Change", "Trend"]
    rows = []
    for pathogen, t in trends.items():
        rows.append([
            pathogen,
            f"{t['total_cases']:,}",
            f"{t['peak_cases']:,}",
            str(t["peak_week"]),
            f"{t['pct_change_4wk']:+.1f}%",
            t["trend"],
        ])
    html.add_table(headers, rows)
    html.add_disclaimer()
    html.add_footer_block("multi-pathogen-dashboard", SKILL_VERSION)
    write_html_report(output_dir, "report.html", html.render())

    # Result JSON
    summary = {
        "pathogens": len(data),
        "alerts": len(alerts),
        "trends": {p: t["trend"] for p, t in trends.items()},
    }
    write_result_json(output_dir, "multi-pathogen-dashboard", SKILL_VERSION, summary, trends)

    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Multi-Pathogen Dashboard")
    parser.add_argument("--demo", action="store_true", help="Run built-in synthetic surveillance data")
    parser.add_argument("--input", help="Input CSV (columns: pathogen, week, year, cases)")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args(argv)
    output_dir = Path(args.output)

    if args.demo or not args.input:
        data = build_demo_data()
        result = run(data, output_dir, is_demo=True)
    elif args.input:
        # Load from CSV and group by pathogen
        from parsers import load_csv
        rows = load_csv(args.input)
        data: dict[str, list[dict]] = {}
        for row in rows:
            p = row.get("pathogen", "Unknown")
            data.setdefault(p, []).append({
                "week": int(row.get("week", 0)),
                "year": int(row.get("year", 2025)),
                "cases": int(row.get("cases", 0)),
            })
        result = run(data, output_dir)

    print(f"Dashboard: {output_dir}/report.html")
    print(f"Pathogens: {result['pathogens']}, Alerts: {result['alerts']}")


if __name__ == "__main__":
    main()
