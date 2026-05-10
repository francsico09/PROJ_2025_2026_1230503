import logging
from time import process_time_ns
from typing import Optional

import requests

from src.core.settings.settings import settings
from src.modules.normalization.models.result.normalization_result import RawWosMetrics, RawWosPublication

logger = logging.getLogger(__name__)


class WosExtractor:

    def __init__(self) -> None:
        self._base_url = settings.WOS_BASE_URL
        self._headers = {
            "X-ApiKey": settings.WOS_API_KEY,
            "Accept": "application/json",
        }

    def extract(self, user_name: str, keywords: list[str]) -> Optional[RawWosMetrics]:
        print(settings.WOS_API_KEY)
        try:
            docs = self._fetch_all_documents(user_name, keywords)

            if not docs:
                logger.warning(f"[WoS] No documents found for user '{user_name}' with keywords: {keywords}")
                return None

            publications = [self._parse_publication(doc) for doc in docs]
            citations = [p.times_cited for p in publications]

            metrics = RawWosMetrics(
                user_name=user_name,
                keywords=keywords,
                i10_index=self._calculate_i10_index(citations),
                h_index=self._calculate_h_index(citations),
                total_citations=sum(citations),
                total_publications=len(publications),
                url=f"https://www.webofscience.com/wos/author/name/{user_name}",
                publications=publications,
            )

            logger.info(
                f"[WoS] Extracted — h_index={metrics.h_index}, "
                f"citations={metrics.total_citations}, "
                f"publications={metrics.total_publications}"
            )

            return metrics

        except Exception as e:
            logger.error(f"[WoS] Unexpected error for '{user_name}': {e}")
            return None

    def _fetch_all_documents(self, user_name: str, keywords: list[str]) -> list[dict]:
        """
        Paginates through all documents for the given ResearcherID (RID).
        The WoS Starter API returns a max of 50 records per page.
        """
        docs = []
        page = 1
        limit = 50

        formated_name = self.format_wos_author(user_name)
        formated_keywords = self.build_wos_keywords(keywords)

        while True:
            try:
                response = requests.get(
                    f"{self._base_url}/documents",
                    headers=self._headers,
                    params={
                        "q": f"AU={formated_name} AND TS={formated_keywords}",
                        "db": "WOS",
                        "limit": limit,
                        "page": page,
                    },
                )
                response.raise_for_status()
                data = response.json()

                hits = data.get("hits", [])
                docs.extend(hits)

                logger.debug(f"[WoS] Page {page}: {len(hits)} documents fetched")

                if len(hits) < limit:
                    break

                page += 1

            except requests.HTTPError as e:
                logger.error(f"[WoS] HTTP error on page {page} for '{user_name}': {e}")
                break

        return docs

    @staticmethod
    def _parse_publication(doc: dict) -> RawWosPublication:
        # title
        title = doc.get("title") or ""

        # source title
        source_title = (
                doc.get("source", {}).get("sourceTitle")
                or doc.get("source", {}).get("title")
        )

        # year
        year = doc.get("source", {}).get("publishYear")

        # citations
        times_cited = (
                doc.get("metrics", {}).get("timesCited")
                or doc.get("timesCited")
                or doc.get("times_cited")
                or 0
        )

        # DOI
        identifiers = doc.get("identifiers", {})
        doi = None

        if isinstance(identifiers, dict):
            doi = identifiers.get("doi")

        elif isinstance(identifiers, str) and "10." in identifiers:
            doi = identifiers

        return RawWosPublication(
            title=title,
            year=int(year) if year else None,
            times_cited=int(times_cited),
            doi=doi,
            source_title=source_title,
        )

    @staticmethod
    def _calculate_h_index(citations: list[int]) -> int:
        sorted_citations = sorted(citations, reverse=True)
        h = 0
        for i, c in enumerate(sorted_citations):
            if c >= i + 1:
                h = i + 1
            else:
                break
        return h

    @staticmethod
    def _calculate_i10_index(citations: list[int]) -> int:
        return sum(1 for c in citations if c >= 10)

    @staticmethod
    def format_wos_author(name: str) -> str:
        parts = name.strip().split()

        if len(parts) == 1:
            return parts[0]

        surname = parts[-1]
        initials = "".join(p[0].upper() for p in parts[:-1])

        return f"{surname} {initials}"

    @staticmethod
    def build_wos_keywords(keywords: list[str]) -> str:
        if not keywords:
            return ""

        formatted = " OR ".join(f'"{kw}"' for kw in keywords)
        return f"({formatted})"
