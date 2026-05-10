import uuid
from typing import Optional

from fastapi import HTTPException
from starlette import status

from datetime import datetime, timezone

from src.core.repositories.repositories import Repositories
from src.modules.metrics.model.source.model import Source, SourceName
from src.modules.metrics.schema.metric_schemas import ResearcherMetricResponse, ResearcherMetricCreate, \
    ResearcherMetricUpdate

from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile

from src.modules.metrics.model.researcher_metric_model import ResearcherMetric


class ResearcherMetricService:
    def __init__(self, _repos: Repositories) -> None:
        self._repos = _repos

    """
    Asynchronous function to create a new metric in the system. Only allowed to admins.
    If successful, the newly added metric is returned, else an exception is raised
    
    :param metric ResearcherMetric: ResearcherMetric to be created.
    
    :return ResearcherMetricResponse:
    
    :raises: HTTP_404_NOT_FOUND if the metric is not found
    """
    async def create_metric(
            self,
            metric_data: ResearcherMetricCreate,
            repos: Optional[Repositories] = None  # Added optional repos
    ) -> ResearcherMetricResponse:
        """
        Asynchronous function to create a new metric.
        Supports external transaction management if 'repos' is passed.
        """
        if repos is None:
            async with self._repos as r:
                result = await self._execute_create_metric(metric_data, r)
                await r.commit()
                return result

        return await self._execute_create_metric(metric_data, repos)

    @staticmethod
    async def _execute_create_metric(
            metric_data: ResearcherMetricCreate,
            repos: Repositories
    ) -> ResearcherMetricResponse:

        researcher = await repos.profiles.get_by_id(metric_data.researcher_id)

        if not researcher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile for researcher not found"
            )

        metric = ResearcherMetric(
            id=uuid.uuid4(),
            researcher_id=metric_data.researcher_id,
            extraction_run_id=metric_data.extraction_run_id,
            date=datetime.now(timezone.utc),

            h_index=metric_data.h_index,
            total_citations=metric_data.total_citations,
            total_publications=metric_data.total_publications,

            i10_index=metric_data.i10_index if metric_data.i10_index else None,
            i10_index_5y=metric_data.i10_index_5y if metric_data.i10_index_5y else None,
            h_index_5y=metric_data.h_index_5y if metric_data.h_index_5y else None,
            citations_5y=metric_data.citations_5y if metric_data.citations_5y else None,
            cites_per_year=metric_data.cites_per_year if metric_data.cites_per_year else None,

            publications=metric_data.publications if metric_data.publications else None,

            source=Source(SourceName(metric_data.source.name), url=metric_data.source.url),
        )

        researcher.metrics.append(metric)

        await repos.profiles.save(researcher)

        return ResearcherMetricResponse.model_validate(metric)
    """
    Asynchronous function to delete a metric of the system. Only allowed to admins.
    Nothing is returned. 
    
    :param ResearcherMetric: ResearcherMetric to be deleted.
    
    :raises: HTTP_404_NOT_FOUND if the metric is not found
    """
    async def delete_metric(
            self,
            metric_id: uuid.UUID
    ) -> None:
        async with self._repos as repos:
            metric = await repos.metrics.get_by_id(metric_id)

            if not metric:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

            researchers = await repos.profiles.get_all()
            researcher: ResearcherProfile

            for r in researchers:
                if metric in r.metrics:
                    researcher = r
                    r.metrics.remove(metric)
                    break

            await repos.metrics.delete(metric.id)
            await repos.profiles.save(researcher)

            await repos.commit()


    """
    Asynchronous function to update a metric. Only allowed to admins. If successful,
    the updated metric is returned, else an exception is raised.
    
    :param metric_id UUID: ResearcherMetric to be updated.
    
    :return ResearcherMetricResponse:
    
    :raises:
    """
    async def update_metric(
            self,
            metric_id: uuid.UUID,
            metric_data: ResearcherMetricUpdate,
    ) -> ResearcherMetricResponse:
        async with self._repos as repos:
            metric = await repos.metrics.get_by_id(metric_id)

            if not metric:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

            metric.update(metric_data)

            await repos.metrics.save(metric)
            await repos.commit()

            return ResearcherMetricResponse.model_validate(metric)

    """
    Asynchronous function to fetch metrics by user id. Only allowed to admins. If there
    are no ResearcherMetrics associated with the user, the list is returned empty.
    
    :param user_id UUID: id of the user which the metrics need to be found.
    
    :return list[ResearcherMetricResponse]:
    """
    async def get_metric_by_user_id(
            self,
            user_id: uuid.UUID,
    ) -> list[ResearcherMetricResponse]:
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            if not user.researcherProfile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User ResearcherProfile not found")

            return [ResearcherMetricResponse.model_validate(m) for m in user.researcherProfile.metrics]

    """
    Asynchronous function to fetch metrics by date of collection. Only allowed to admins. If
    there are no metrics collected on that date, the list is returned empty. 
    
    :param date date: date of collection of the metrics

    :return list[ResearcherMetricResponse]:
    """
    async def get_metric_by_date(
            self,
            date: datetime
    ) -> list[ResearcherMetricResponse]:
        async with self._repos as repos:
            metrics = await repos.metrics.get_by_date(date)

            return [ResearcherMetricResponse.model_validate(m) for m in metrics]

    """
    Asynchronous function to fetch all metrics in the system. Only allowed to admins. If there
    are no metrics on the system, the list is returned empty. 
    
    :return list[ResearcherMetricResponse]: list of all ResearcherMetrics if any, else list is empty
    """
    async def list_metrics(
            self
    ) -> list[ResearcherMetricResponse]:
        async with self._repos as repos:
            metrics = await repos.metrics.get_all()

            return [ResearcherMetricResponse.model_validate(m) for m in metrics]
