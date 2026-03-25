#!/usr/bin/env python3
"""EpiClaw Disease Forecaster -- short-horizon case forecasting."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "disease-forecaster"
DEMO_ROWS = [
    {"date": "2025-01-01", "cases": 18},
    {"date": "2025-01-08", "cases": 22},
    {"date": "2025-01-15", "cases": 27},
    {"date": "2025-01-22", "cases": 31},
    {"date": "2025-01-29", "cases": 34},
    {"date": "2025-02-05", "cases": 38},
    {"date": "2025-02-12", "cases": 42},
    {"date": "2025-02-19", "cases": 47},
]


def _load_series(path: Path) -> tuple[list[str], list[float]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("Forecast input is empty.")
    if "cases" not in rows[0]:
        raise RuntimeError("Input must include a 'cases' column.")
    dates = [row.get("date", str(i + 1)) for i, row in enumerate(rows)]
    series = [float(row["cases"]) for row in rows]
    return dates, series


def _naive_forecast(series: list[float], horizon: int) -> list[float]:
    return [series[-1]] * horizon


def _holt_linear(series: list[float], horizon: int, alpha: float = 0.5, beta: float = 0.3) -> tuple[list[float], list[float]]:
    if len(series) < 2:
        raise RuntimeError("Holt forecast requires at least 2 observations.")
    level = series[0]
    trend = series[1] - series[0]
    fitted: list[float] = [series[0]]
    for value in series[1:]:
        prev_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        fitted.append(level + trend)
    forecast = [max(0.0, level + step * trend) for step in range(1, horizon + 1)]
    return fitted, forecast


def run_analysis(input_path: Path, horizon: int, method: str) -> tuple[dict, dict]:
    dates, series = _load_series(input_path)
    if method == "auto":
        method = "holtwinters" if len(series) >= 5 else "naive"
    if method == "naive":
        fitted = [series[0]] + series[:-1]
        forecast = _naive_forecast(series, horizon)
    else:
        fitted, forecast = _holt_linear(series, horizon)
    residuals = [observed - predicted for observed, predicted in zip(series[1:], fitted[1:])] if len(series) > 1 else [0.0]
    rmse = math.sqrt(sum(r * r for r in residuals) / len(residuals)) if residuals else 0.0
    forecast_rows = []
    for step, value in enumerate(forecast, start=1):
        width = 1.96 * rmse * math.sqrt(step)
        forecast_rows.append(
            {
                "horizon_step": step,
                "point_forecast": round(value, 4),
                "pi_low": round(max(0.0, value - width), 4),
                "pi_high": round(value + width, 4),
            }
        )
    slope = (series[-1] - series[0]) / max(1, len(series) - 1)
    summary = {
        "n_observations": len(series),
        "method": method,
        "horizon": horizon,
        "rmse": round(rmse, 4),
        "trend_per_step": round(slope, 4),
        "latest_cases": series[-1],
    }
    data = {"dates": dates, "historical_cases": series, "fitted": fitted, "forecast": forecast_rows}
    return summary, data


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_report(output_path: Path, summary: dict, data: dict) -> None:
    header = generate_report_header(title="Disease Forecaster Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION, "Method": summary["method"]})
    lines = [
        "## Forecast Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Observations | {summary['n_observations']} |",
        f"| Method | {summary['method']} |",
        f"| Horizon | {summary['horizon']} |",
        f"| RMSE | {summary['rmse']} |",
        f"| Trend per step | {summary['trend_per_step']} |",
        f"| Latest cases | {summary['latest_cases']} |",
        "",
        "## Forecast",
        "",
        "| Step | Forecast | 95% PI |",
        "|---|---|---|",
    ]
    for row in data["forecast"]:
        lines.append(f"| {row['horizon_step']} | {row['point_forecast']} | {row['pi_low']} to {row['pi_high']} |")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Disease Forecaster -- short horizon case forecasting.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--demo", action="store_true", help="Run built-in demo time series")
    parser.add_argument("--horizon", type=int, default=14)
    parser.add_argument("--method", choices=["auto", "naive", "holtwinters"], default="auto")
    return parser


def _write_demo_input(path: Path) -> Path:
    _write_csv(path, DEMO_ROWS)
    return path


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
    else:
        input_path = _write_demo_input(output_dir / "demo_forecast_input.csv")
    summary, data = run_analysis(input_path, args.horizon, args.method)
    forecast_csv = output_dir / "forecast.csv"
    _write_csv(forecast_csv, data["forecast"])
    data["forecast_csv"] = str(forecast_csv)
    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
