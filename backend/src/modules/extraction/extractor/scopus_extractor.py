import logging
from typing import Optional

import requests

from src.core.settings.settings import settings
from src.modules.normalization.models.result.normalization_result import RawScopusMetrics

logger = logging.getLogger(__name__)


class ScopusExtractor:

    def __init__(self) -> None:
        self._base_url = settings.SCOPUS_BASE_URL
        self._headers = {
            "X-ELS-APIKey": settings.SCOPUS_API_KEY,
            "Accept": "application/json",
        }

    def extract(self, identifier: str) -> Optional[RawScopusMetrics]:
        logger.info(f"[Scopus] Starting extraction for identifier '{identifier}'")

        try:
            if identifier.isdigit():
                scopus_id = identifier
            else:
                scopus_id = self._search_author_id(identifier)
                if not scopus_id:
                    return None

            return self._extract_from_search(scopus_id)

        except Exception as e:
            logger.error(f"[Scopus] Error for '{identifier}': {type(e).__name__}: {e}")
            return None

    def _search_author_id(self, query: str) -> Optional[str]:
        logger.info(f"[Scopus] Searching author by query: '{query}'")

        response = requests.get(
            f"{self._base_url}/search/author",
            headers=self._headers,
            params={
                "query": query,
                "field": "identifier,preferred-name,document-count,affiliation-current",
                "count": 1,
            },
        )

        if response.status_code == 404:
            logger.warning(f"[Scopus] No author found for query '{query}'")
            return None

        response.raise_for_status()
        data = response.json()

        entries = data.get("search-results", {}).get("entry", [])

        if not entries or not entries[0].get("dc:identifier"):
            logger.warning(f"[Scopus] Empty results for query '{query}'")
            return None

        raw_id = entries[0].get("dc:identifier", "")
        scopus_id = raw_id.split(":")[-1] if ":" in raw_id else raw_id

        logger.info(f"[Scopus] Found Scopus ID: {scopus_id}")
        return scopus_id

    def _extract_from_search(self, scopus_id: str) -> Optional[RawScopusMetrics]:
        """
        Uses Search API.
        Extracts available metrics from search response.
        """

        logger.info(f"[Scopus] Extracting from search API for ID '{scopus_id}'")

        response = requests.get(
            f"{self._base_url}/search/author",
            headers=self._headers,
            params={
                "query": f"AU-ID({scopus_id})",
                "field": "identifier,preferred-name,document-count",
            },
        )

        response.raise_for_status()
        data = response.json()

        entries = data.get("search-results", {}).get("entry", [])

        if not entries:
            logger.warning(f"[Scopus] No data found for ID '{scopus_id}'")
            return None

        entry = entries[0]

        document_count = int(entry.get("document-count") or 0)

        preferred_name = entry.get("preferred-name", {})
        given = preferred_name.get("given-name", "")
        surname = preferred_name.get("surname", "")

        affiliation = entry.get("affiliation-current", {}).get("affiliation-name")

        metrics = RawScopusMetrics(
            scopus_id=scopus_id,
            h_index=0,  # Not available
            total_citations=0,  # Not available
            total_publications=document_count,
            url=f"https://www.scopus.com/authid/detail.uri?authorId={scopus_id}",
        )

        logger.info(
            f"[Scopus] Extracted from SEARCH — "
            f"publications={metrics.total_publications}, "
            f"name={given} {surname}, "
            f"affiliation={affiliation}"
        )

        return metrics