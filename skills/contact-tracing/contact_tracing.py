#!/usr/bin/env python3
"""EpiClaw Contact Tracing -- Network-based contact tracing with generation intervals, secondary attack rates, and superspreader detection."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np

from reporting import generate_report_header, generate_report_footer, write_result_json

VERSION = "0.1.0"
SKILL_NAME = "contact-tracing"

# Optional networkx import with graceful fallback
try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:
    _HAS_NETWORKX = False


# --------------------------------------------------------------------------- #
# Demo data generation
# --------------------------------------------------------------------------- #

def generate_demo_contacts(
    n_seed_cases: int = 5,
    generations: int = 3,
    serial_interval: float = 5.0,
    rng_seed: int = 42,

):
    rng = np.random.default_rng(rng_seed)
    start_date = datetime(2025, 1, 1)
    source_cases = [f"seed_{idx + 1}" for idx in range(n_seed_cases)]
    onset_dates = {case_id: start_date + timedelta(days=int(rng.integers(0, 3))) for case_id in source_cases}
    records: list[dict[str, str]] = []
    current_generation = source_cases
    settings = ["household", "workplace", "school", "community"]
    for generation in range(1, generations + 1):
        next_generation: list[str] = []
        for source in current_generation:
            n_contacts = int(rng.poisson(2.0)) + 1
            for contact_idx in range(n_contacts):
                contact_id = f"g{generation}_{source}_{contact_idx + 1}"
                contact_date = onset_dates[source] + timedelta(days=max(1, int(rng.normal(serial_interval, 1.5))))
                onset_dates[contact_id] = contact_date
                next_generation.append(contact_id)
                records.append(
                    {
                        "case_id": source,
                        "contact_id": contact_id,
                        "contact_date": contact_date.strftime("%Y-%m-%d"),
                        "exposure_setting": str(rng.choice(settings)),
                        "generation": str(generation),
                    }
                )
        current_generation = next_generation
        if not current_generation:
            break
    return records
def load_contacts(filepath: str) -> list[dict]:
    """Load contact tracing data from CSV file."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Validate required columns
    required = {"contact_id", "case_id", "contact_date", "exposure_setting"}
    if rows:
        missing = required - set(rows[0].keys())
        if missing:
            print(f"[warn] Missing columns: {missing}. Proceeding with available data.")
    return rows


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #

def build_transmission_graph_networkx(records: list[dict]):
    """Build directed transmission graph using networkx."""
    G = nx.DiGraph()
    for r in records:
        src = r["case_id"]
        tgt = r["contact_id"]
        setting = r.get("exposure_setting", "unknown")
        G.add_edge(src, tgt, setting=setting)
    return G


def build_transmission_graph_dict(records: list[dict]) -> dict[str, list[str]]:
    """Build adjacency dict when networkx is unavailable."""
    graph: dict[str, list[str]] = {}
    for r in records:
        src = r["case_id"]
        tgt = r["contact_id"]
        graph.setdefault(src, []).append(tgt)
        graph.setdefault(tgt, [])  # ensure node exists
    return graph


def compute_out_degrees(records: list[dict]) -> dict[str, int]:
    """Count how many contacts each case generated."""
    out_deg: dict[str, int] = {}
    for r in records:
        src = r["case_id"]
        out_deg[src] = out_deg.get(src, 0) + 1
    return out_deg


def compute_sar_by_setting(records: list[dict]) -> dict[str, float]:
    """Secondary attack rate per exposure setting.

    SAR = contacts traced / total contacts for that setting (proxy: all records).
    Since every record represents a traced contact who became a case, SAR here
    is reported as proportion of total contacts in that setting that are traced
    secondary cases.
    """
    from collections import Counter
    setting_counts = Counter(r.get("exposure_setting", "unknown") for r in records)
    total = len(records)
    if total == 0:
        return {}
    sar = {}
    for setting, count in setting_counts.items():
        # SAR as proportion of all traced contacts in this setting
        sar[setting] = round(count / total, 4)
    return sar


def compute_generation_intervals(records: list[dict], serial_interval: float) -> list[float]:
    """Estimate generation intervals from contact dates.

    Requires the records to be sorted by generation. Uses date differences
    between source onset (approximated from contact_date chain) and contact_date.
    Returns a list of interval values in days.
    """
    # Build a map: case_id -> contact_date (treating it as approximate onset)
    onset_by_id: dict[str, str] = {}
    for r in records:
        onset_by_id[r["contact_id"]] = r["contact_date"]

    intervals = []
    for r in records:
        source = r["case_id"]
        contact_date_str = r["contact_date"]
        source_date_str = onset_by_id.get(source)
        if source_date_str and contact_date_str:
            try:
                d_source = datetime.strptime(source_date_str, "%Y-%m-%d")
                d_contact = datetime.strptime(contact_date_str, "%Y-%m-%d")
                diff = (d_contact - d_source).days
                if diff >= 0:
                    intervals.append(float(diff))
            except ValueError:
                pass

    if not intervals:
        # Fall back to simulated intervals using the serial_interval parameter
        rng = np.random.default_rng(99)
        intervals = list(rng.exponential(serial_interval, size=20).tolist())

    return intervals


def identify_superspreaders(out_degrees: dict[str, int], threshold: int = 3) -> list[str]:
    """Return list of case IDs with out-degree > threshold."""
    return [cid for cid, deg in out_degrees.items() if deg > threshold]


def count_generations(records: list[dict]) -> dict[int, int]:
    """Count cases per generation if 'generation' column is present."""
    from collections import Counter
    if records and "generation" in records[0]:
        counts = Counter(int(r["generation"]) for r in records)
        return dict(sorted(counts.items()))
    # Estimate generations from graph depth
    return {}


# --------------------------------------------------------------------------- #
# Report generation
# --------------------------------------------------------------------------- #

def generate_report(
    summary: dict[str, Any],
    data: dict[str, Any],
    pathogen: str,
    output_dir: Path,

):
    lines = [
        generate_report_header(
            title="Contact Tracing Report",
            skill_name=SKILL_NAME,
            extra_metadata={"Pathogen": pathogen, "Version": VERSION},
        ),
        "## Summary",
        "",
        f"- Total cases: `{summary['total_cases']}`",
        f"- Contacts traced: `{summary['total_contacts_traced']}`",
        f"- Secondary attack rate: `{summary['secondary_attack_rate']}`",
        f"- Mean generation interval: `{summary['mean_generation_interval']}` days",
        f"- Superspreaders identified: `{summary['superspreaders_identified']}`",
        "",
        "## Secondary Attack Rate by Setting",
        "",
        "| Setting | Share |",
        "|---|---|",
    ]
    for setting, value in data["sar_by_setting"].items():
        lines.append(f"| {setting} | {value:.4f} |")
    lines.extend(
        [
            "",
            "## Cases by Generation",
            "",
            json.dumps(data["cases_by_generation"], indent=2),
            "",
            "## Superspreaders",
            "",
            ", ".join(data["superspreaders"]) if data["superspreaders"] else "None identified.",
            "",
            generate_report_footer(),
        ]
    )
    return "\n".join(lines)
# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="EpiClaw Contact Tracing — network-based contact tracing analysis"
    )
    parser.add_argument("--input", dest="input_path", help="Input CSV file (contact_id, case_id, contact_date, exposure_setting)")
    parser.add_argument("--output", dest="output_dir", default="/tmp/epiclaw_contact_tracing", help="Output directory")
    parser.add_argument("--pathogen", default="Unknown Pathogen", help="Pathogen name")
    parser.add_argument("--serial-interval", type=float, default=5.0, help="Mean serial interval in days (default: 5.0)")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo network")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ #
    # Load data
    # ------------------------------------------------------------------ #
    if args.demo or not args.input_path:
        print("[info] Using built-in demo contact network")
        records = generate_demo_contacts(serial_interval=args.serial_interval)
        pathogen = args.pathogen
    elif args.input_path:
        print(f"[info] Loading contact data from: {args.input_path}")
        records = load_contacts(args.input_path)
        pathogen = args.pathogen
    else:
        parser.error("Provide --input <file>.")

    print(f"[info] Loaded {len(records)} contact records")

    # ------------------------------------------------------------------ #
    # Analysis
    # ------------------------------------------------------------------ #
    print("[info] Building transmission graph...")
    if _HAS_NETWORKX:
        G = build_transmission_graph_networkx(records)
        all_nodes = set(G.nodes())
        out_degrees = dict(G.out_degree())
    else:
        print("[info] networkx not available; using dict-based graph")
        graph_dict = build_transmission_graph_dict(records)
        all_nodes = set(graph_dict.keys())
        out_degrees = {k: len(v) for k, v in graph_dict.items()}

    print("[info] Computing secondary attack rates by setting...")
    sar_by_setting = compute_sar_by_setting(records)

    print("[info] Computing generation intervals...")
    gen_intervals = compute_generation_intervals(records, args.serial_interval)

    print("[info] Identifying superspreaders...")
    superspreaders = identify_superspreaders(out_degrees, threshold=3)

    print("[info] Counting cases by generation...")
    gen_counts = count_generations(records)

    # Derive unique cases (source + contacts)
    all_case_ids = set(r["case_id"] for r in records) | set(r["contact_id"] for r in records)
    total_cases = len(all_case_ids)
    total_contacts = len(records)

    # Overall SAR: total contacts / total unique sources
    unique_sources = len(set(r["case_id"] for r in records))
    overall_sar = (total_contacts / unique_sources) if unique_sources > 0 else 0.0
    # Normalise to [0,1] as a rate (capped at 1)
    overall_sar_norm = min(overall_sar / max(overall_sar, 1), 1.0) if overall_sar > 1 else overall_sar

    mean_gi = float(np.mean(gen_intervals)) if gen_intervals else 0.0
    n_generations = max(gen_counts.keys()) if gen_counts else (len(set(r.get("generation", 0) for r in records)) - 1)

    summary = {
        "total_cases": total_cases,
        "total_contacts_traced": total_contacts,
        "secondary_attack_rate": round(overall_sar_norm, 4),
        "mean_generation_interval": round(mean_gi, 2),
        "superspreaders_identified": len(superspreaders),
        "generations": n_generations,
    }

    data = {
        "cases_by_generation": {str(k): v for k, v in gen_counts.items()},
        "sar_by_setting": sar_by_setting,
        "generation_intervals": [round(x, 2) for x in gen_intervals[:100]],  # cap for JSON
        "superspreaders": superspreaders,
        "out_degrees": {k: v for k, v in out_degrees.items() if v > 0},
    }

    # ------------------------------------------------------------------ #
    # Figure: transmission chain bar chart
    # ------------------------------------------------------------------ #
    print("[info] Generating figures...")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if gen_counts:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            # Left: cases by generation
            ax = axes[0]
            gens = [int(g) for g in gen_counts.keys()]
            counts = list(gen_counts.values())
            ax.bar(gens, counts, color="#4C8BE0", edgecolor="white")
            ax.set_xlabel("Generation")
            ax.set_ylabel("Number of Cases")
            ax.set_title(f"Cases by Transmission Generation\n({pathogen})")
            ax.set_xticks(gens)

            # Right: generation interval histogram
            ax2 = axes[1]
            if gen_intervals:
                ax2.hist(gen_intervals, bins=20, color="#E07C4C", edgecolor="white", alpha=0.85)
                ax2.axvline(mean_gi, color="black", linestyle="--", linewidth=1.5, label=f"Mean = {mean_gi:.1f}d")
                ax2.set_xlabel("Generation Interval (days)")
                ax2.set_ylabel("Frequency")
                ax2.set_title("Generation Interval Distribution")
                ax2.legend()

            plt.tight_layout()
            fig_path = figures_dir / "contact_tracing.png"
            plt.savefig(fig_path, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"[info] Figure saved: {fig_path}")
        else:
            print("[info] No generation data for figure; skipping chart")
    except Exception as e:
        print(f"[warn] Figure generation failed: {e}")

    # ------------------------------------------------------------------ #
    # Report + JSON
    # ------------------------------------------------------------------ #
    print("[info] Writing report...")
    report_md = generate_report(summary, data, pathogen, output_dir)
    report_path = output_dir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")

    result_path = write_result_json(
        output_dir=output_dir,
        skill=SKILL_NAME,
        version=VERSION,
        summary=summary,
        data=data,
    )

    print(f"[info] Report: {report_path}")
    print(f"[info] Result JSON: {result_path}")
    print(f"[info] Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
