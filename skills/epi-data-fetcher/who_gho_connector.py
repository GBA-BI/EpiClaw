"""WHO Global Health Observatory (GHO) OData API connector for EpiClaw.

Provides access to WHO health indicators, disease surveillance data, and outbreak information.
API docs: https://www.who.int/data/gho/info/gho-odata-api
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from base_client import BaseAPIClient

GHO_BASE = "https://ghoapi.azureedge.net/api"
DEFAULT_CACHE_DIR = Path.home() / ".epiclaw" / "who_gho_cache"


class WHOClient:
    """WHO Global Health Observatory data retrieval."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        use_cache: bool = True,
    ) -> None:
        self._client = BaseAPIClient(
            base_url=GHO_BASE,
            cache_dir=cache_dir or DEFAULT_CACHE_DIR,
            rate_limit=0.5,
            use_cache=use_cache,
            user_agent="EpiClaw-WHO/0.1.0",
        )

    def list_indicators(self, filter_text: str = "") -> list[dict[str, Any]]:
        """List available GHO indicators, optionally filtered by text.

        Returns list of dicts with: IndicatorCode, IndicatorName.
        """
        data = self._client.get("Indicator")
        indicators = data.get("value", [])
        if filter_text:
            ft = filter_text.lower()
            indicators = [
                i for i in indicators
                if ft in i.get("IndicatorName", "").lower()
                or ft in i.get("IndicatorCode", "").lower()
            ]
        return indicators

    def get_indicator(
        self,
        indicator_code: str,
        country: str | None = None,
        year_range: tuple[int, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch data for a specific indicator.

        Args:
            indicator_code: GHO indicator code (e.g., "MALARIA_EST_INCIDENCE")
            country: ISO3 country code filter (e.g., "USA", "BRA")
            year_range: Optional (start_year, end_year) filter
        """
        params: dict[str, str] = {}

        # Build OData filter
        filters = []
        if country:
            filters.append(f"SpatialDim eq '{country}'")
        if year_range:
            filters.append(f"TimeDim ge {year_range[0]} and TimeDim le {year_range[1]}")
        if filters:
            params["$filter"] = " and ".join(filters)

        data = self._client.get(indicator_code, params=params)
        return data.get("value", [])

    def get_country_data(
        self,
        indicator_code: str,
        country: str,
        year_range: tuple[int, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Convenience method to get indicator data for a specific country.

        Returns sorted by year, with keys: year, value, country.
        """
        raw = self.get_indicator(indicator_code, country=country, year_range=year_range)
        results = []
        for row in raw:
            try:
                results.append({
                    "year": int(row.get("TimeDim", 0)),
                    "value": float(row.get("NumericValue", 0)),
                    "country": row.get("SpatialDim", country),
                    "dim1": row.get("Dim1", ""),
                    "dim2": row.get("Dim2", ""),
                })
            except (ValueError, TypeError):
                continue
        results.sort(key=lambda x: x["year"])
        return results

    def search_indicators(self, query: str, max_results: int = 20) -> list[dict[str, str]]:
        """Search for indicators matching a query string.

        Returns list of dicts with: code, name.
        """
        indicators = self.list_indicators(query)
        return [
            {"code": i["IndicatorCode"], "name": i["IndicatorName"]}
            for i in indicators[:max_results]
        ]

    def list_countries(self) -> list[dict[str, str]]:
        """List all available countries with their ISO3 codes."""
        data = self._client.get("DIMENSION/COUNTRY/DimensionValues")
        return [
            {"code": c.get("Code", ""), "name": c.get("Title", "")}
            for c in data.get("value", [])
        ]
