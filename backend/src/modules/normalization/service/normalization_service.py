import logging
from datetime import date
from uuid import UUID

from src.core.repositories.repositories import Repositories
from src.modules.normalization.models.metric.normalized_metric import NormalizedMetric
from src.modules.normalization.models.profile.normalized_researcher_profile import NormalizedProfile
from src.modules.normalization.models.result.normalization_result import (
    RawExtractionResult, NormalizationResult, RawScholarMetrics, RawWosMetrics
)
from src.core.settings.settings import settings
from src.modules.normalization.models.result.normalization_result import RawWosPublication

from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import MetricPublication
from src.core.domain.researcher_metric.researcher_metric_model.source_model import SourceName, Source

logger = logging.getLogger(__name__)


class NormalizationService:

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    async def normalize(self, raw: RawExtractionResult) -> NormalizationResult:
        result = NormalizationResult(user_id=raw.user_id, run=raw.run)

        async with self._repos as repos:
            researcher = await repos.profiles.get_by_user_id(raw.user_id)

        if not researcher:
            result.skipped_reasons.append("Researcher profile not found")
            return result

        # --- Scholar ---
        if raw.scholar:
            metric = await self._normalize_metric(
                researcher_id=researcher.id,
                source=Source(SourceName.scholar, f"{settings.SCHOLAR_BASE_URL}/{raw.scholar.scholar_id}"),
                h_index=raw.scholar.h_index,
                total_citations=raw.scholar.total_citations,
                total_publications=raw.scholar.total_publications,
                i10_index=raw.scholar.i10_index,
                h_index_5y=raw.scholar.h_index_5y,
                i10_index_5y=raw.scholar.i10_index_5y,
                citations_5y=raw.scholar.citations_5y,
                cites_per_year=raw.scholar.cites_per_year,
            )
            if metric.is_duplicate:
                result.skipped_reasons.append(f"Scholar metric from {date.today()} already exists.")
            else:
                result.metrics.append(metric)

        # --- WoS ---
        if raw.wos:
            print('[NORMALIZATION SERVICE] RAW WOS PUBS EXTRACTED: ', raw.wos.publications)

            metric = await self._normalize_metric(
                researcher_id=researcher.id,
                source=Source(SourceName.wos, f"{settings.WOS_BASE_URL}/{raw.wos.user_name}"),
                h_index=raw.wos.h_index,
                total_citations=raw.wos.total_citations,
                total_publications=raw.wos.total_publications,
                publications=raw.wos.publications,
            )

            if metric.is_duplicate:
                result.skipped_reasons.append(f"WoS metric from {date.today()} already exists.")
            else:
                result.metrics.append(metric)

        # --- ORCID - Updates Profile ---
        if raw.orcid:
            profile_update = NormalizedProfile(
                researcher_id=researcher.id,
                biography=raw.orcid.biography,
                keywords=raw.orcid.keywords,
                orcid_id=raw.orcid.orcid_id,
                scholar_id=raw.orcid.scholar_id,
                wos_id=raw.orcid.wos_id,
                scopus_id=raw.orcid.scopus_id,
            )
            result.profile_update = profile_update

        return result

    async def normalize_all(self, raw_results: list[RawExtractionResult]) -> list[NormalizationResult]:
        normalized = []
        for raw in raw_results:
            try:
                n = await self.normalize(raw)
                normalized.append(n)
            except Exception as e:
                logger.error(f"[Normalization] Error for user {raw.user_id}: {e}")
                normalized.append(NormalizationResult(
                    user_id=raw.user_id,
                    skipped_reasons=[f"Normalization error: {str(e)}"],
                ))
        return normalized

    async def _normalize_metric(
            self,
            researcher_id: UUID,
            source: Source,
            h_index: int,
            total_citations: int,
            total_publications: int,
            i10_index: int | None = None,
            h_index_5y: int | None = None,
            i10_index_5y: int | None = None,
            citations_5y: int | None = None,
            cites_per_year: dict | None = None,
            publications: list[RawWosPublication] | None = None,
    ) -> NormalizedMetric:
        print('[NORMALIZATION SERVICE] PUBS: ', publications)

        is_duplicate = await self._is_duplicate_metric(researcher_id, source, date.today())

        publications_converted = []

        for p in (publications or []):
            publications_converted.append(
                MetricPublication(
                    title=p.title,
                    times_cited=p.times_cited,
                    year=p.year,
                    doi=p.doi,
                    source_title=p.source_title,
                )
            )

        print('[NORMALIZATION SERVICE] CONVERTED PUBS: ', publications_converted)

        return NormalizedMetric(
            researcher_id=researcher_id,
            source=source,
            h_index=h_index,
            total_citations=total_citations,
            total_publications=total_publications,
            i10_index=i10_index,
            h_index_5y=h_index_5y,
            i10_index_5y=i10_index_5y,
            citations_5y=citations_5y,
            cites_per_year=cites_per_year,
            is_duplicate=is_duplicate,
            publications=publications_converted
        )

    async def _is_duplicate_metric(
            self,
            researcher_id: UUID,
            source: SourceName,
            extraction_date: date,
    ) -> bool:
        async with self._repos as repos:
            existing = await repos.metrics.get_by_researcher_id(researcher_id)

        return any(
            m.date == extraction_date and m.source == source
            for m in existing
        )