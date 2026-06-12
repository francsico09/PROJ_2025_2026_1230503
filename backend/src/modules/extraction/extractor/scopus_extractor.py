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

    def extract(self, identifier: str, user_name: str) -> Optional[RawScopusMetrics]:
        logger.info(f"[Scopus] Starting extraction for identifier '{identifier}'")

        try:
            if identifier.isdigit():
                scopus_id = identifier
            else:
                query = self._build_author_query(identifier, user_name)
                scopus_id = self._search_author_id(query)

                if not scopus_id:
                    return None

            return self._retrieve_author_metrics(scopus_id)

        except Exception as e:
            logger.error(f"[Scopus] Error for '{identifier}': {type(e).__name__}: {e}")
            return None

    @staticmethod
    def _build_author_query(identifier: str, user_name: str) -> str:
        """
        Builds the most precise query possible.
        Prefers structured AUTHLASTNAME/AUTHFIRST from user_name,
        falling back to the raw identifier string.
        """
        parts = user_name.strip().split() if user_name and user_name.strip() else []

        if len(parts) >= 2:
            first_name = parts[0]
            last_name  = " ".join(parts[1:])
            query = f"AUTHLASTNAME({last_name}) AND AUTHFIRST({first_name})"
            logger.info(f"[Scopus] Built structured query from name: '{query}'")
            return query

        logger.info(f"[Scopus] Falling back to raw identifier query: '{identifier}'")
        return identifier

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

        if response.status_code >= 400:
            logger.error(response.text)

        data = response.json()

        entries = data.get("search-results", {}).get("entry", [])

        if not entries or not entries[0].get("dc:identifier"):
            logger.warning(f"[Scopus] Empty results for query '{query}'")
            return None

        raw_id = entries[0].get("dc:identifier", "")
        scopus_id = raw_id.split(":")[-1] if ":" in raw_id else raw_id

        logger.info(f"[Scopus] Found Scopus ID: {scopus_id}")
        return scopus_id

    def _retrieve_author_metrics(self, scopus_id: str) -> Optional[RawScopusMetrics]:
        """
        Uses Author Retrieval API with view=METRICS.
        Returns h-index, cited-by-count, citations-count, document-count.
        Falls back to Search API if Retrieval API returns 401/403 (no institutional access).
        """
        logger.info(f"[Scopus] Retrieving metrics for ID '{scopus_id}'")

        response = requests.get(
            f"{self._base_url}/author/author_id/{scopus_id}",
            headers=self._headers,
            params={"view": "METRICS"},
        )

        if response.status_code in (401, 403):
            logger.warning(f"[Scopus] Retrieval API unauthorized, falling back to Search API")
            return self._retrieve_from_search(scopus_id)

        response.raise_for_status()

        profile = response.json().get("author-retrieval-response", [{}])[0]

        metrics = RawScopusMetrics(
            scopus_id=scopus_id,
            h_index=int(profile.get("h-index") or 0),
            total_citations=int(profile.get("cited-by-count") or 0),
            total_publications=int(profile.get("document-count") or 0),
            url=f"https://www.scopus.com/authid/detail.uri?authorId={scopus_id}",
        )

        logger.info(
            f"[Scopus] Extracted from RETRIEVAL — "
            f"publications={metrics.total_publications}, "
            f"citations={metrics.total_citations}, "
            f"h_index={metrics.h_index}"
        )

        return metrics

    def _retrieve_from_search(self, scopus_id: str) -> Optional[RawScopusMetrics]:
        """
        Fallback: Search API with AU-ID query.
        Only document-count is reliably available here.
        """
        logger.info(f"[Scopus] Fallback search extraction for ID '{scopus_id}'")

        response = requests.get(
            f"{self._base_url}/search/author",
            headers=self._headers,
            params={
                "query": f"AU-ID({scopus_id})",
                "field": "identifier,preferred-name,document-count",
            },
        )

        response.raise_for_status()

        entries = response.json().get("search-results", {}).get("entry", [])

        if not entries:
            logger.warning(f"[Scopus] No data found for ID '{scopus_id}'")
            return None

        entry = entries[0]

        metrics = RawScopusMetrics(
            scopus_id=scopus_id,
            h_index=0,
            total_citations=0,
            total_publications=int(entry.get("document-count") or 0),
            url=f"https://www.scopus.com/authid/detail.uri?authorId={scopus_id}",
        )

        logger.info(
            f"[Scopus] Extracted from SEARCH (fallback) — "
            f"publications={metrics.total_publications}"
        )

        return metrics