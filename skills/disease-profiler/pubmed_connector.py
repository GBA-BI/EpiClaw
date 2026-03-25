"""PubMed / NCBI Entrez E-utilities connector for EpiClaw.

Provides search and abstract retrieval from PubMed via the NCBI E-utilities API.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from base_client import BaseAPIClient

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_CACHE_DIR = Path.home() / ".epiclaw" / "pubmed_cache"


class PubMedClient:
    """PubMed search and retrieval via NCBI Entrez E-utilities."""

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | None = None,
        use_cache: bool = True,
    ) -> None:
        self.api_key = api_key or os.environ.get("NCBI_API_KEY", "")
        rate = 0.11 if self.api_key else 0.34  # 10/sec vs 3/sec
        self._client = BaseAPIClient(
            base_url=ENTREZ_BASE,
            cache_dir=cache_dir or DEFAULT_CACHE_DIR,
            rate_limit=rate,
            use_cache=use_cache,
            user_agent="EpiClaw-PubMed/0.1.0",
        )

    def _base_params(self) -> dict:
        params: dict[str, str] = {"tool": "epiclaw", "email": "epiclaw@research.local"}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def search(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "relevance",
        date_range: tuple[str, str] | None = None,
    ) -> list[str]:
        """Search PubMed and return list of PMIDs.

        Args:
            query: PubMed search query (supports MeSH terms, Boolean operators)
            max_results: Maximum number of results to return
            sort: Sort order — "relevance" or "date"
            date_range: Optional (mindate, maxdate) in YYYY/MM/DD format
        """
        params = {
            **self._base_params(),
            "db": "pubmed",
            "term": query,
            "retmax": str(max_results),
            "sort": sort,
            "retmode": "json",
        }
        if date_range:
            params["mindate"] = date_range[0]
            params["maxdate"] = date_range[1]
            params["datetype"] = "pdat"

        data = self._client.get("esearch.fcgi", params=params)
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_abstracts(self, pmids: list[str]) -> list[dict[str, Any]]:
        """Fetch article metadata and abstracts for a list of PMIDs.

        Returns list of dicts with: pmid, title, authors, journal, year, abstract, doi, mesh_terms.
        """
        if not pmids:
            return []

        params = {
            **self._base_params(),
            "db": "pubmed",
            "id": ",".join(pmids[:200]),  # Entrez limit
            "retmode": "xml",
        }
        xml_text = self._client.get_text("efetch.fcgi", params=params)
        return self._parse_pubmed_xml(xml_text)

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
    ) -> list[dict[str, Any]]:
        """Search PubMed and fetch abstracts in one call."""
        pmids = self.search(query, max_results=max_results, sort=sort)
        return self.fetch_abstracts(pmids)

    @staticmethod
    def _parse_pubmed_xml(xml_text: str) -> list[dict[str, Any]]:
        """Parse PubMed XML efetch response into structured dicts."""
        articles = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return articles

        for article_el in root.findall(".//PubmedArticle"):
            medline = article_el.find("MedlineCitation")
            if medline is None:
                continue

            pmid_el = medline.find("PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            art = medline.find("Article")
            if art is None:
                continue

            title_el = art.find("ArticleTitle")
            title = title_el.text if title_el is not None else ""

            # Authors
            authors = []
            for author in art.findall(".//Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

            # Journal
            journal_el = art.find(".//Title")
            journal = journal_el.text if journal_el is not None else ""

            # Year
            year = ""
            pub_date = art.find(".//PubDate")
            if pub_date is not None:
                year_el = pub_date.find("Year")
                year = year_el.text if year_el is not None else ""

            # Abstract
            abstract_parts = []
            for abs_text in art.findall(".//AbstractText"):
                label = abs_text.get("Label", "")
                text = abs_text.text or ""
                if label:
                    abstract_parts.append(f"**{label}**: {text}")
                else:
                    abstract_parts.append(text)
            abstract = "\n".join(abstract_parts)

            # DOI
            doi = ""
            for eid in article_el.findall(".//ArticleId"):
                if eid.get("IdType") == "doi":
                    doi = eid.text or ""

            # MeSH terms
            mesh_terms = []
            for mesh in medline.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            articles.append({
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "abstract": abstract,
                "doi": doi,
                "mesh_terms": mesh_terms,
            })

        return articles
