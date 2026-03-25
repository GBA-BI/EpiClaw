"""Common data format parsers for EpiClaw skills."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_csv(filepath: str | Path, delimiter: str | None = None) -> list[dict[str, str]]:
    """Load a CSV/TSV file as a list of dicts.

    Auto-detects delimiter if not specified.
    """
    filepath = Path(filepath)
    if delimiter is None:
        if filepath.suffix == ".tsv":
            delimiter = "\t"
        else:
            # Sniff first line
            with open(filepath, newline="", encoding="utf-8") as f:
                sample = f.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def load_json(filepath: str | Path) -> Any:
    """Load a JSON file."""
    filepath = Path(filepath)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def detect_csv_type(filepath: str | Path) -> str | None:
    """Inspect CSV headers to infer data type for orchestrator routing.

    Returns a skill hint string or None if unrecognized.
    """
    rows = load_csv(filepath)
    if not rows:
        return None

    headers = {h.lower().strip() for h in rows[0].keys()}

    # Outbreak linelist
    if {"case_id", "onset_date"} <= headers or {"case_id", "symptoms"} <= headers:
        return "outbreak-investigator"

    # Surveillance time series
    if {"date", "cases"} <= headers:
        if "deaths" in headers:
            return "disease-modeler"
        return "disease-forecaster"

    # Geospatial
    if {"latitude", "longitude"} <= headers or {"lat", "lon"} <= headers:
        return "epi-gis"

    # Variant surveillance
    if {"sample_id", "lineage"} <= headers or {"sequence_id", "lineage"} <= headers:
        return "variant-surveillance"

    # Contact tracing
    if {"contact_id", "source_id"} <= headers or {"source", "target"} <= headers:
        return "contact-tracing"

    # Wastewater
    if "concentration" in headers and ("sample_date" in headers or "date" in headers):
        return "wastewater-surveillance"

    # Vaccine effectiveness
    if "vaccine_status" in headers and ("outcome" in headers or "test_result" in headers):
        return "vaccine-effectiveness"

    # 2x2 table data
    if {"exposed", "cases", "total"} <= headers:
        return "epi-calculator"

    return None
