import logging
from typing import Optional
from scholarly import scholarly, MaxTriesExceededException
from src.modules.normalization.models.result.normalization_result import RawScholarMetrics

logger = logging.getLogger(__name__)


class ScholarExtractor:

    @staticmethod
    def extract(identifier: str) -> Optional[RawScholarMetrics]:
        try:
            is_id = len(identifier) == 12 and " " not in identifier

            if is_id:
                logger.info(f"[Scholar] Searching by ID: '{identifier}'")
                author = scholarly.search_author_id(identifier)
                author = scholarly.fill(author)
            else:
                logger.info(f"[Scholar] Searching by name: '{identifier}'")
                result = next(scholarly.search_author(identifier), None)
                if result is None:
                    logger.warning(f"[Scholar] No result for: '{identifier}'")
                    return None
                author = scholarly.fill(result)

            if not author:
                return None

            scholar_id = author.get("scholar_id", "")

            return RawScholarMetrics(
                scholar_id=scholar_id,
                name=author.get("name", identifier),

                h_index=author.get("hindex", 0),
                i10_index=author.get("i10index", 0),

                total_citations=author.get("citedby", 0),
                total_publications=len(author.get("publications", [])),

                url=f"https://scholar.google.com/citations?user={scholar_id}",

                h_index_5y=author.get("hindex5y", 0),
                i10_index_5y=author.get("i10index5y", 0),
                citations_5y=author.get("citedby5y", 0),
                cites_per_year=author.get("cites_per_year", {}),
            )

        except MaxTriesExceededException:
            logger.error(f"[Scholar] Rate limit exceeded for '{identifier}'")
            return None

        except Exception as e:
            logger.error(f"[Scholar] Unexpected error for '{identifier}': {e}")
            return None