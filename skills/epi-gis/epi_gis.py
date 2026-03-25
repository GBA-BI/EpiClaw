#!/usr/bin/env python3
"""EpiClaw Epi GIS -- simple spatial epidemiology metrics."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "epi-gis"
DEMO_ROWS = [
    {"id": "district_a", "latitude": 22.3193, "longitude": 114.1694, "cases": 18},
    {"id": "district_b", "latitude": 22.3019, "longitude": 114.1746, "cases": 11},
    {"id": "district_c", "latitude": 22.3364, "longitude": 114.1786, "cases": 9},
]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def run_analysis(input_path: Path, hotspot_radius_km: float) -> tuple[dict, dict]:
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("Epi GIS input is empty.")
    for column in ("latitude", "longitude"):
        if column not in rows[0]:
            raise RuntimeError(f"Input must include a '{column}' column.")
    points = []
    for idx, row in enumerate(rows, start=1):
        points.append(
            {
                "id": row.get("id") or row.get("case_id") or f"point_{idx}",
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "cases": float(row.get("cases", 1)),
            }
        )
    latitudes = [point["latitude"] for point in points]
    longitudes = [point["longitude"] for point in points]
    centroid_lat = statistics.mean(latitudes)
    centroid_lon = statistics.mean(longitudes)
    hotspot_rows = []
    nearest: list[float] = []
    for point in points:
        neighbors = 0
        distances = []
        for other in points:
            if other["id"] == point["id"]:
                continue
            distance = _haversine(point["latitude"], point["longitude"], other["latitude"], other["longitude"])
            distances.append(distance)
            if distance <= hotspot_radius_km:
                neighbors += 1
        if distances:
            nearest.append(min(distances))
        hotspot_rows.append({"id": point["id"], "neighbors_within_radius": neighbors})
    summary = {
        "n_points": len(points),
        "centroid_latitude": round(centroid_lat, 6),
        "centroid_longitude": round(centroid_lon, 6),
        "mean_nearest_neighbor_km": round(statistics.mean(nearest), 4) if nearest else None,
        "hotspot_radius_km": hotspot_radius_km,
    }
    data = {"points": points, "hotspots": hotspot_rows}
    return summary, data


def _write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def generate_report(output_path: Path, summary: dict, data: dict) -> None:
    header = generate_report_header(title="Epi GIS Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION})
    lines = [
        "## Spatial Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Points | {summary['n_points']} |",
        f"| Centroid latitude | {summary['centroid_latitude']} |",
        f"| Centroid longitude | {summary['centroid_longitude']} |",
        f"| Mean nearest neighbor (km) | {summary['mean_nearest_neighbor_km']} |",
        f"| Hotspot radius (km) | {summary['hotspot_radius_km']} |",
        "",
        "## Hotspot Counts",
        "",
        "| ID | Neighbors within radius |",
        "|---|---|",
    ]
    for row in data["hotspots"]:
        lines.append(f"| {row['id']} | {row['neighbors_within_radius']} |")
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Epi GIS -- simple spatial cluster metrics.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--demo", action="store_true", help="Run built-in demo geospatial dataset")
    parser.add_argument("--hotspot-radius-km", type=float, default=10.0)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        input_path = output_dir / "demo_points.csv"
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "latitude", "longitude", "cases"])
            writer.writeheader()
            writer.writerows(DEMO_ROWS)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
    summary, data = run_analysis(input_path, args.hotspot_radius_km)
    summary["n_regions"] = summary["n_points"]
    hotspot_tsv = output_dir / "hotspots.tsv"
    _write_tsv(hotspot_tsv, data["hotspots"])
    data["hotspots_tsv"] = str(hotspot_tsv)
    report_path = output_dir / "report.md"
    generate_report(report_path, summary, data)
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
