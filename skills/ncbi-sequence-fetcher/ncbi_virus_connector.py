"""NCBI Virus / Entrez nucleotide connector for EpiClaw.

Provides viral sequence search, metadata retrieval, and FASTA download
via the NCBI Entrez E-utilities API.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from base_client import BaseAPIClient

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_CACHE_DIR = Path.home() / ".epiclaw" / "ncbi_virus_cache"


class NCBIVirusClient:
    """NCBI Virus / nucleotide sequence search and retrieval."""

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | None = None,
        use_cache: bool = True,
    ) -> None:
        self.api_key = api_key or os.environ.get("NCBI_API_KEY", "")
        rate = 0.11 if self.api_key else 0.34
        self._client = BaseAPIClient(
            base_url=ENTREZ_BASE,
            cache_dir=cache_dir or DEFAULT_CACHE_DIR,
            rate_limit=rate,
            use_cache=use_cache,
            user_agent="EpiClaw-NCBIVirus/0.1.0",
        )

    def _base_params(self) -> dict:
        params: dict[str, str] = {"tool": "epiclaw", "email": "epiclaw@research.local"}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def search_sequences(
        self,
        query: str,
        db: str = "nuccore",
        max_results: int = 50,
        sort: str = "relevance",
    ) -> list[str]:
        """Search NCBI nucleotide database and return accession IDs.

        Args:
            query: Entrez search query (e.g., "SARS-CoV-2[Organism] AND complete genome")
            db: Database — "nuccore" (nucleotide), "protein", "biosample"
            max_results: Maximum number of results
            sort: Sort order — "relevance" or "date"
        """
        params = {
            **self._base_params(),
            "db": db,
            "term": query,
            "retmax": str(max_results),
            "sort": sort,
            "retmode": "json",
        }
        data = self._client.get("esearch.fcgi", params=params)
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_metadata(self, ids: list[str], db: str = "nuccore") -> list[dict[str, Any]]:
        """Fetch metadata summary for a list of sequence IDs.

        Returns list of dicts with: uid, accession, title, organism, length, createdate, etc.
        """
        if not ids:
            return []

        params = {
            **self._base_params(),
            "db": db,
            "id": ",".join(ids[:200]),
            "retmode": "json",
        }
        data = self._client.get("esummary.fcgi", params=params)
        result = data.get("result", {})
        uids = result.get("uids", [])
        return [result[uid] for uid in uids if uid in result and isinstance(result[uid], dict)]

    def download_fasta(
        self,
        ids: list[str],
        db: str = "nuccore",
        output_path: Path | None = None,
    ) -> str:
        """Download sequences in FASTA format.

        Args:
            ids: List of accession IDs
            db: Database
            output_path: If provided, write FASTA to file; otherwise return as string
        """
        params = {
            **self._base_params(),
            "db": db,
            "id": ",".join(ids[:100]),
            "rettype": "fasta",
            "retmode": "text",
        }
        fasta_text = self._client.get_text("efetch.fcgi", params=params)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(fasta_text, encoding="utf-8")

        return fasta_text

    def search_virus(
        self,
        organism: str,
        collection_date_range: tuple[str, str] | None = None,
        country: str | None = None,
        max_results: int = 50,
        complete_genome: bool = False,
    ) -> list[str]:
        """Convenience method to search for viral sequences.

        Args:
            organism: Virus name (e.g., "SARS-CoV-2", "Influenza A H5N1")
            collection_date_range: (min_date, max_date) in YYYY/MM/DD format
            country: Country filter
            max_results: Maximum number of results
            complete_genome: If True, filter for complete genomes only
        """
        parts = [f"{organism}[Organism]"]
        if complete_genome:
            parts.append('"complete genome"[Title]')
        if country:
            parts.append(f"{country}[Country]")
        if collection_date_range:
            parts.append(
                f"{collection_date_range[0]}:{collection_date_range[1]}[Collection Date]"
            )

        query = " AND ".join(parts)
        return self.search_sequences(query, max_results=max_results, sort="date")
