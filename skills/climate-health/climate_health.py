#!/usr/bin/env python3
"""EpiClaw Climate Health -- lagged climate-disease association analysis."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "climate-health"
DEMO_ROWS = [
    {"date": "2025-01", "temperature_c": 18.0, "rainfall_mm": 12.0, "cases": 11},
    {"date": "2025-02", "temperature_c": 19.2, "rainfall_mm": 18.0, "cases": 14},
    {"date": "2025-03", "temperature_c": 21.1, "rainfall_mm": 28.0, "cases": 18},
    {"date": "2025-04", "temperature_c": 24.0, "rainfall_mm": 45.0, "cases": 22},
]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _pearson(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 3:
        return float("nan")
    mx = statistics.mean(x)
    my = statistics.mean(y)
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def _linear_slope(x: list[float], y: list[float]) -> float:
    mx = statistics.mean(x)
    my = statistics.mean(y)
    denom = sum((v - mx) ** 2 for v in x)
    if denom == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / denom


def run_analysis(input_path: Path, climate_var: str, max_lag: int) -> tuple[dict, dict]:
    rows = _read_rows(input_path)
    if not rows:
        raise RuntimeError("Climate-health input is empty.")
    if climate_var == "both":
        climate_var = "temperature_c" if "temperature_c" in rows[0] else "rainfall_mm"
    if climate_var not in rows[0]:
        raise RuntimeError(f"Climate variable column not found: {climate_var}")
    if "cases" not in rows[0]:
        raise RuntimeError("Input must contain a 'cases' column.")

    climate = [float(row[climate_var]) for row in rows]
    cases = [float(row["cases"]) for row in rows]
    dates = [row.get("date", str(i + 1)) for i, row in enumerate(rows)]

    lag_rows: list[dict[str, object]] = []
    for lag in range(max_lag + 1):
        x = climate[: len(climate) - lag] if lag else climate[:]
        y = cases[lag:] if lag else cases[:]
        corr = _pearson(x, y)
        lag_rows.append({"lag": lag, "correlation": round(corr, 6) if not math.isnan(corr) else None})
    best = max(lag_rows, key=lambda row: abs(row["correlation"] or 0.0))
    lag = int(best["lag"])
    x_best = climate[: len(climate) - lag] if lag else climate[:]
    y_best = [math.log1p(value) for value in (cases[lag:] if lag else cases[:])]
    slope = _linear_slope(x_best, y_best)
    pct_change = (math.exp(slope) - 1.0) * 100.0

    summary = {
        "n_timepoints": len(rows),
        "climate_variable": climate_var,
        "optimal_lag": lag,
        "optimal_correlation": best["correlation"],
        "percent_change_per_unit": round(pct_change, 4),
    }
    data = {
        "dates": dates,
        "climate_series": climate,
        "case_series": cases,
        "lag_correlations": lag_rows,
    }
    return summary, data


def generate_report(output_path: Path, summary: dict, data: dict) -> None:
    header = generate_report_header(title="Climate Health Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION})
    lines = [
        "## Lagged Association Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Time points | {summary['n_timepoints']} |",
        f"| Climate variable | {summary['climate_variable']} |",
        f"| Optimal lag | {summary['optimal_lag']} |",
        f"| Optimal correlation | {summary['optimal_correlation']} |",
        f"| Percent change per unit climate | {summary['percent_change_per_unit']:.4f}% |",
        "",
        "## Lag Response",
        "",
        "| Lag | Correlation |",
        "|---|---|",
    ]
    for row in data["lag_correlations"]:
        lines.append(f"| {row['lag']} | {row['correlation']} |")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Climate Health -- lagged climate-disease analysis.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--demo", action="store_true", help="Run built-in demo climate series")
    parser.add_argument("--climate-var", default="temperature_c")
    parser.add_argument("--max-lag", type=int, default=6)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        input_path = output_dir / "demo_climate.csv"
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["date", "temperature_c", "rainfall_mm", "cases"])
            writer.writeheader()
            writer.writerows(DEMO_ROWS)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
    summary, data = run_analysis(input_path, args.climate_var, args.max_lag)
    summary["n_months"] = summary["n_timepoints"]
    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
