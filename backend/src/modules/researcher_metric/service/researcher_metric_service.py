import uuid

from fastapi import HTTPException, logger
from starlette import status

from datetime import datetime, timezone

from src.core.repositories.repositories import Repositories
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse
from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    ResearcherMetricCreate, ResearcherMetricResponse, ResearcherMetricUpdate
from src.database.models.researcher_metric_orm import ResearcherMetricORM
from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionRun
from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionTrigger
from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionStatus


class ResearcherMetricService:
    def __init__(self, _repos: Repositories) -> None:
        self._repos = _repos


    async def create_metric(self, metric_data: ResearcherMetricCreate) -> ResearcherMetricResponse:
        async with self._repos as repos:
            profile = await repos.profiles.get_by_user_id(metric_data.researcher_id)

            if not profile:
                print(f"Profile not found for user id: {metric_data.researcher_id}, retrying with profile id")
                retry = await repos.profiles.get_by_id(metric_data.researcher_id)

                if not retry:
                    raise HTTPException(status_code=404, detail="Profile not found with user id or profile id")

                profile = retry

            run: ExtractionRun
            if not metric_data.extraction_run_id:
                run = ExtractionRun(
                    id=uuid.uuid4(),
                    researcher_id=profile.id,
                    triggered_at=datetime.now(timezone.utc),
                    triggered_by=ExtractionTrigger.created_by_admin,
                    status=ExtractionStatus.completed,
                    sources_attempted=[],
                    sources_succeeded=[]
                )

                await repos.extraction_runs.save(run)
                await repos.commit()

            metric = ResearcherMetric(
                id=uuid.uuid4(),
                researcher_id=profile.id,
                extraction_run_id=metric_data.extraction_run_id if metric_data.extraction_run_id else run.id,
                date=datetime.now(timezone.utc),
                h_index=metric_data.h_index,
                total_citations=metric_data.total_citations,
                total_publications=metric_data.total_publications,
                i10_index=metric_data.i10_index,
                i10_index_5y=metric_data.i10_index_5y,
                h_index_5y=metric_data.h_index_5y,
                citations_5y=metric_data.citations_5y,
                cites_per_year=metric_data.cites_per_year,
                publications=metric_data.publications,
                source=Source(SourceName(metric_data.source.name), url=metric_data.source.url),
            )

            profile.metrics.append(metric)
            await repos.profiles.save(profile)
            await repos.commit()

            return ResearcherMetricResponse.model_validate(metric)


    async def delete_metric(self, metric_id: uuid.UUID) -> None:
        """
        Asynchronous function to delete a metric of the system. Only allowed to admins.
        Nothing is returned.

        :param metric_id: id of the metric to be deleted.

        :raises: HTTP_404_NOT_FOUND if the metric is not found
        """

        async with self._repos as repos:
            metric = await repos.metrics.get_by_id(metric_id)
            if not metric:
                raise HTTPException(status_code=404, detail="Metric not found")

            profile = await repos.profiles.get_by_id(metric.researcher_id)
            if profile:
                profile.metrics = [m for m in profile.metrics if m.id != metric_id]
                await repos.profiles.save(profile)

            await repos.metrics.delete(metric_id)
            await repos.commit()


    async def update_metric(
            self,
            metric_id: uuid.UUID,
            metric_data: ResearcherMetricUpdate,
    ) -> ResearcherMetricResponse:
        """
        Asynchronous function to update a metric. Only allowed to admins. If successful,
        the updated metric is returned, else an exception is raised.

        :param metric_id: ResearcherMetric to be updated.
        :param metric_data: data for the update.

        :return ResearcherMetricResponse:

        :raises:
        """

        async with self._repos as repos:
            metric = await repos.metrics.get_by_id(metric_id)

            if not metric:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

            metric.update(metric_data)

            await repos.metrics.save(metric)
            await repos.commit()

            return ResearcherMetricResponse.model_validate(metric)


    async def fetch_metrics(
            self,
            params: PaginationParams
    ) -> PaginatedResponse[ResearcherMetricResponse]:
        async with self._repos as repos:
            result = await repos.metrics.fetch(params)

            return PaginatedResponse(
                items=[ResearcherMetricResponse.model_validate(m) for m in result.items],
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                pages=result.pages,
            )


    async def fetch_metrics_by_user(
            self,
            user_id: uuid.UUID,
            params: PaginationParams,
    ) -> PaginatedResponse[ResearcherMetricResponse]:
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            profile = user.researcherProfile

            if not profile:
                raise HTTPException(status_code=404, detail="ResearcherProfile not found")

            result = await repos.metrics.fetch(
                params=params,
                extra_filters=[ResearcherMetricORM.researcher_id == profile.id]
            )

            return PaginatedResponse(
                items=[ResearcherMetricResponse.model_validate(m) for m in result.items],
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                pages=result.pages,
            )

    async def fetch_latest_by_user(
            self,
            source: str | None = None,
            params: PaginationParams = None
    ) -> PaginatedResponse[ResearcherMetricResponse]:

        async with self._repos as repos:
            return await repos.metrics.fetch_latest_by_user(source, params)