#!/usr/bin/env python3
"""EpiClaw Epi-Data-Fetcher -- download and normalize epidemiological surveillance data
from WHO GHO, Our World in Data (OWID), and ECDC public APIs."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from reporting import generate_report_header, generate_report_footer, write_result_json
from who_gho_connector import WHOClient


VERSION = "0.1.0"
SKILL_NAME = "epi-data-fetcher"

# ---------------------------------------------------------------------------
# WHO GHO fetcher (uses existing connector)
# ---------------------------------------------------------------------------

# Common WHO GHO indicator codes by disease
WHO_INDICATORS = {
    "malaria": ["MALARIA_EST_INCIDENCE", "MALARIA_EST_DEATHS"],
    "cholera": ["WHS3_62", "WHS3_63"],
    "tuberculosis": ["MDG_0000000020", "MDG_0000000021"],
    "hiv": ["HIV_0000000026", "HIV_0000000006"],
    "measles": ["WHS4_544", "WHS4_100"],
    "dengue": ["DENGUE_CASES", "DENGUE_DEATHS"],
    "influenza": ["RS_198", "RS_200"],
}


def fetch_who_gho(
    disease: str,
    country: str | None,
    year_start: int,
    year_end: int,
) -> list[dict[str, Any]]:
    """Fetch time-series data from WHO Global Health Observatory."""
    client = WHOClient()
    indicators = WHO_INDICATORS.get(disease.lower(), [])
    if not indicators:
        # Try disease name as indicator code directly
        indicators = [disease.upper()]

    records: list[dict[str, Any]] = []
    for code in indicators:
        print(f"[info] Fetching WHO GHO indicator: {code} ...")
        try:
            rows = client.get_country_data(
                indicator_code=code,
                country=country,
                year_range=(year_start, year_end),
            )
            for row in rows:
                records.append({
                    "source": "WHO GHO",
                    "indicator": code,
                    "country": row.get("country", country or "GLOBAL"),
                    "year": row.get("year"),
                    "value": row.get("value"),
                    "dim1": row.get("dim1", ""),
                })
        except Exception as e:
            print(f"[warn] WHO GHO {code}: {e}")
    return records


# ---------------------------------------------------------------------------
# OWID fetcher (Our World in Data public COVID/disease CSV)
# ---------------------------------------------------------------------------

OWID_CSV_URLS = {
    "covid-19": "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv",
    "monkeypox": "https://raw.githubusercontent.com/owid/monkeypox/main/public/data/latest/owid-monkeypox-latest.csv",
}


def fetch_owid(
    disease: str,
    country_code: str | None,
    max_rows: int = 1000,
) -> list[dict[str, Any]]:
    """Fetch latest snapshot from Our World in Data public CSV API."""
    disease_key = disease.lower().replace("-", "").replace("_", "")
    url = None
    for k, v in OWID_CSV_URLS.items():
        if k.replace("-", "") in disease_key or disease_key in k.replace("-", ""):
            url = v
            break
    if not url:
        print(f"[warn] No OWID dataset configured for disease='{disease}'. "
              f"Available: {list(OWID_CSV_URLS.keys())}")
        return []

    import urllib.request
    print(f"[info] Fetching OWID {disease} data...")
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[warn] OWID fetch failed: {e}")
        return []

    reader = csv.DictReader(content.splitlines())
    records: list[dict[str, Any]] = []
    for i, row in enumerate(reader):
        if i >= max_rows:
            break
        iso = row.get("iso_code", "")
        if country_code and iso.upper() != country_code.upper():
            continue
        records.append({
            "source": "Our World in Data",
            "indicator": disease,
            "country": row.get("location", iso),
            "date": row.get("date", ""),
            "new_cases": _safe_float(row.get("new_cases")),
            "new_deaths": _safe_float(row.get("new_deaths")),
            "total_cases": _safe_float(row.get("total_cases")),
            "total_deaths": _safe_float(row.get("total_deaths")),
            "new_vaccinations": _safe_float(row.get("new_vaccinations")),
            "people_fully_vaccinated_per_hundred": _safe_float(
                row.get("people_fully_vaccinated_per_hundred")
            ),
        })
    return records


def _safe_float(val: Any) -> float | None:
    try:
        return float(val) if val not in ("", None) else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# ECDC weekly respiratory data (public CSV via ECDC Surveillance Atlas)
# ---------------------------------------------------------------------------

ECDC_URLS = {
    "influenza": "https://opendata.ecdc.europa.eu/influenza/heroesreporting/csv",
}


def fetch_ecdc(disease: str, country: str | None) -> list[dict[str, Any]]:
    """Fetch from ECDC open data portal."""
    url = ECDC_URLS.get(disease.lower())
    if not url:
        print(f"[warn] No ECDC dataset configured for disease='{disease}'.")
        return []

    import urllib.request
    print(f"[info] Fetching ECDC {disease} data...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EpiClaw/0.1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[warn] ECDC fetch failed: {e}")
        return []

    records: list[dict[str, Any]] = []
    for row in csv.DictReader(content.splitlines()):
        if country and row.get("countryCode", "").upper() != country.upper():
            continue
        records.append({
            "source": "ECDC",
            "indicator": disease,
            "country": row.get("countryCode", ""),
            "year": row.get("Year", ""),
            "week": row.get("Week", ""),
            "value": _safe_float(row.get("value") or row.get("NumberOfCases")),
        })
    return records


# ---------------------------------------------------------------------------
# Demo data (offline fallback)
# ---------------------------------------------------------------------------

DEMO_WHO_RECORDS = [
    {"source": "WHO GHO (demo)", "indicator": "MALARIA_EST_INCIDENCE", "country": "NGA",
     "year": y, "value": round(100_000 * (0.8 ** (y - 2015)) + 5000, 0), "dim1": ""}
    for y in range(2015, 2024)
]

DEMO_OWID_RECORDS = [
    {"source": "Our World in Data (demo)", "indicator": "covid-19",
     "country": "World", "date": f"2020-0{m:02d}-01",
     "new_cases": 100 * (3 ** (m - 1)), "new_deaths": 5 * (3 ** (m - 1)),
     "total_cases": None, "total_deaths": None,
     "new_vaccinations": None, "people_fully_vaccinated_per_hundred": None}
    for m in range(1, 10)
]


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    if not records:
        return
    # Collect all keys across all records (heterogeneous rows from different sources)
    all_keys: list[str] = []
    seen: set[str] = set()
    for row in records:
        for k in row.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def generate_report(records: list[dict[str, Any]], source: str, disease: str,
                    country: str | None, output_dir: Path) -> str:
    sources = sorted({r["source"] for r in records})
    lines = [
        generate_report_header(
            title="Epidemiological Data Fetch Report",
            skill_name=SKILL_NAME,
            extra_metadata={
                "Disease": disease,
                "Country": country or "All",
                "Sources": ", ".join(sources),
                "Records": str(len(records)),
                "Version": VERSION,
            },
        ),
        "## Summary",
        "",
        f"- Total records fetched: **{len(records)}**",
        f"- Data sources: {', '.join(f'`{s}`' for s in sources)}",
        "",
        "## Records (first 20)",
        "",
    ]
    if records:
        headers = list(records[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in records[:20]:
            lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")

    lines.extend([
        "",
        "## Downstream Skills",
        "",
        "Feed the generated `data.csv` into:",
        "- `rt-estimator --input data.csv` — real-time Rt estimation",
        "- `disease-forecaster --input data.csv` — outbreak forecasting",
        "- `early-warning-system --input data.csv` — CUSUM aberration detection",
        "- `multi-pathogen-dashboard --input data.csv` — surveillance dashboard",
        "",
        generate_report_footer(),
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="EpiClaw Epi-Data-Fetcher — download epidemiological surveillance data"
    )
    parser.add_argument("--disease", default="malaria",
                        help="Disease name (malaria, cholera, covid-19, influenza, tuberculosis, hiv, ...)")
    parser.add_argument("--source", choices=["who", "owid", "ecdc", "all"], default="who",
                        help="Data source (default: who)")
    parser.add_argument("--country", default=None,
                        help="ISO3 country code (e.g. NGA, USA, DEU) or blank for global")
    parser.add_argument("--year-start", type=int, default=2015)
    parser.add_argument("--year-end", type=int, default=2024)
    parser.add_argument("--output", default="output/epi-data-fetcher")
    parser.add_argument("--demo", action="store_true", help="Run demo (offline, no API calls)")
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw {SKILL_NAME} v{VERSION}")
    print(f"[info] Disease: {args.disease}, Source: {args.source}, Country: {args.country or 'global'}")

    records: list[dict[str, Any]] = []

    if args.demo:
        print("[info] Demo mode — using built-in synthetic records (no API calls).")
        records = DEMO_WHO_RECORDS + DEMO_OWID_RECORDS
    else:
        if args.source in ("who", "all"):
            try:
                records += fetch_who_gho(args.disease, args.country, args.year_start, args.year_end)
            except Exception as e:
                print(f"[warn] WHO GHO fetch failed: {e}")

        if args.source in ("owid", "all"):
            try:
                records += fetch_owid(args.disease, args.country)
            except Exception as e:
                print(f"[warn] OWID fetch failed: {e}")

        if args.source in ("ecdc", "all"):
            try:
                records += fetch_ecdc(args.disease, args.country)
            except Exception as e:
                print(f"[warn] ECDC fetch failed: {e}")

        if not records:
            print("[warn] No records fetched from live APIs. Falling back to demo data.")
            records = DEMO_WHO_RECORDS + DEMO_OWID_RECORDS

    print(f"[info] Total records: {len(records)}")

    # Write normalized CSV
    csv_path = out_dir / "data.csv"
    write_csv(records, csv_path)
    print(f"[info] Data CSV: {csv_path}")

    # Write report
    report_md = generate_report(records, args.source, args.disease, args.country, out_dir)
    report_path = out_dir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[info] Report: {report_path}")

    summary: dict[str, Any] = {
        "disease": args.disease,
        "source": args.source,
        "country": args.country or "global",
        "year_start": args.year_start,
        "year_end": args.year_end,
        "n_records": len(records),
        "sources_used": sorted({r["source"] for r in records}),
    }
    write_result_json(out_dir, SKILL_NAME, VERSION, summary, {"records": records[:50]})
    print("[info] Done.")


if __name__ == "__main__":
    main()
