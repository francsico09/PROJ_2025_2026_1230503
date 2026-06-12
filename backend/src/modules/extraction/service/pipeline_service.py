import logging
import uuid
from typing import Optional

from uuid import UUID

from fastapi import HTTPException
from starlette import status

from datetime import datetime, timezone

from src.core.repositories.repositories import Repositories
from src.modules.extraction.service.extraction_service import ExtractionService
from src.modules.normalization.models.result.normalization_result import NormalizationResult
from src.modules.normalization.service.normalization_service import NormalizationService
from src.modules.extraction.service.extraction_run_service import ExtractionRunService
from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    ResearcherMetricCreate
from src.modules.researcher_metric.service.researcher_metric_service import ResearcherMetricService

from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    ResearcherMetricResponse

logger = logging.getLogger(__name__)


class ExtractionPipelineResult:
    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id
        self.metric_created: bool = False
        self.profile_updated: bool = False
        self.skipped_reasons: list[str] = []
        self.errors: list[str] = []
        self.metrics: list[ResearcherMetricResponse] = []


class PipelineService:

    def __init__(
            self,
            repos: Repositories,
            extraction_service: ExtractionService,
            normalization_service: NormalizationService,
            metric_service: ResearcherMetricService,
            run_service: ExtractionRunService
    ) -> None:
        self._repos = repos
        self._extraction = extraction_service
        self._normalization = normalization_service
        self._metric_service = metric_service
        self._run_service = run_service

    """
    Runs the complete pipeline for one user.
    
    :param user_id: user id
    :return ExtractionPipelineResult:
    """
    async def run_for_user(
            self,
            user_id: UUID
    ) -> ExtractionPipelineResult:
        pipeline_result = ExtractionPipelineResult(user_id=user_id)

        try:
            raw = await self._extraction.extract_for_user(user_id)

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher was not found - run for user")

        if raw.errors:
            pipeline_result.errors.extend(raw.errors)

        normalized: NormalizationResult = await self._normalization.normalize(raw)
        pipeline_result.skipped_reasons.extend(normalized.skipped_reasons)

        async with self._repos as repos:
            try:
                run = await self._run_service.create_run(normalized.run, repos=repos)

                if normalized.metrics:
                    for m in normalized.metrics:
                        if not m.is_duplicate:
                            logger.info(m)
                            metric_data = ResearcherMetricCreate(
                                researcher_id=m.researcher_id,
                                extraction_run_id=run.id,
                                source=m.source,
                                date=datetime.now(timezone.utc),

                                h_index=m.h_index,
                                total_citations=m.total_citations,
                                total_publications=m.total_publications,

                                i10_index=m.i10_index if m.i10_index else None,
                                h_index_5y=m.h_index_5y if m.h_index_5y else None,
                                i10_index_5y=m.i10_index_5y if m.i10_index_5y else None,
                                citations_5y=m.citations_5y if m.citations_5y else None,
                                cites_per_year=m.cites_per_year if m.cites_per_year else None,

                                publications=[
                                    {
                                        "title": p.title,
                                        "times_cited": p.times_cited,
                                        "year": p.year,
                                        "doi": p.doi,
                                        "source_title": p.source_title,
                                    }
                                    for p in (m.publications or [])
                                ]
                            )

                            created_metric = await self._metric_service.create_metric(metric_data)
                            await repos.commit()

                            pipeline_result.metric_created = True

                            pipeline_result.metrics.append(
                                ResearcherMetricResponse(
                                    id=created_metric.id,
                                    researcher_id=metric_data.researcher_id,
                                    extraction_run_id=metric_data.extraction_run_id,
                                    source=metric_data.source,
                                    date=metric_data.date,
                                    h_index=metric_data.h_index,
                                    total_citations=metric_data.total_citations,
                                    total_publications=metric_data.total_publications,

                                    i10_index=metric_data.i10_index,
                                    h_index_5y=metric_data.h_index_5y,
                                    i10_index_5y=metric_data.i10_index_5y,
                                    citations_5y=metric_data.citations_5y,
                                    cites_per_year=metric_data.cites_per_year,

                                    publications=metric_data.publications
                                )
                            )

            except Exception as e:
                await repos.rollback()
                logger.error(f"Pipeline failed for user {user_id}: {e}")
                raise e

            if normalized.profile_update:
                await self._persist_profile_update(normalized, pipeline_result)

            return pipeline_result

    """
    Runs the pipeline for all active users. Used by the periodic extraction
    job. User errors are registered but do not interrupt.

    :return list[ExtractionPipelineResult]
    """

    async def run_for_all_users(self) -> list[ExtractionPipelineResult]:
        raw_results = await self._extraction.extract_for_all_users()
        normalized_results = await self._normalization.normalize_all(raw_results)

        pipeline_results = []
        for normalized in normalized_results:
            pr = ExtractionPipelineResult(user_id=normalized.user_id)
            pr.skipped_reasons.extend(normalized.skipped_reasons)

            try:
                if normalized.metrics:
                    for metric in normalized.metrics:
                        if metric is not metric.is_duplicate:
                            metric_data = ResearcherMetricCreate(
                                researcher_id=metric.researcher_id,
                                h_index=normalized.metric.h_index,
                                i10_index=normalized.metric.i10_index,
                                total_citations=normalized.metric.total_citations,
                                total_publications=normalized.metric.total_publications,
                                source=normalized.metric.source,
                            )
                            await self._metric_service.create_metric(metric_data)
                            pr.metric_created = True

                if normalized.profile_update:
                    await self._persist_profile_update(normalized, pr)

            except Exception as e:
                logger.error(f"Error on persisting user {normalized.user_id}: {e}")
                pr.errors.append(str(e))

            pipeline_results.append(pr)

        total_metrics = sum(1 for r in pipeline_results if r.metric_created)
        logger.info(
            f"Pipeline ended: {len(pipeline_results)} users, {total_metrics} created metrics."
        )
        return pipeline_results

    async def _persist_profile_update(
            self,
            normalized: NormalizationResult,
            pipeline_result: ExtractionPipelineResult,
    ) -> None:
        try:
            update = normalized.profile_update
            async with self._repos as repos:
                profile = await repos.profiles.get_by_id(update.researcher_id)

                if profile:
                    if update.biography:
                        profile.biography = update.biography

                    if update.keywords:
                        profile.keywords = update.keywords

                    if hasattr(update, 'orcid') and update.orcid:
                        profile.orcid = update.orcid

                    await repos.profiles.save(profile)
                    await repos.commit()

                    pipeline_result.profile_updated = True

        except Exception as e:
            logger.error(f"Error updating profile {normalized.user_id}: {e}")
            pipeline_result.errors.append(f"Profile not updated: {str(e)}")
