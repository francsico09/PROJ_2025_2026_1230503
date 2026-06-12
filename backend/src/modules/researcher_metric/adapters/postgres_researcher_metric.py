import math
import uuid

from sqlalchemy import select, func, desc, asc
from sqlalchemy import delete

from src.database.models.researcher_metric_orm import ResearcherMetricORM
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse
from src.database.models.researcher_profile_orm import ResearcherProfileORM
from src.core.repositories.postgres_base_repository import PostgresBaseRepository
from src.modules.researcher_metric.repository.researcher_metric_repository import ResearcherMetricRepository
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

class PostgresResearcherMetricRepository(PostgresBaseRepository, ResearcherMetricRepository):
    """
    Implementation of the abstract methods from the GeneralRepository
    and specific entity repository interfaces
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch(
            self,
            params: PaginationParams,
            extra_filters: list = None
    ) -> PaginatedResponse:
        """
        Implementations of the fetch method. Returns a paginated and filtered
        result given certain parameters.
        Uses the _fetch_paginated method from the PostgresBaseRepository to
        avoid code repetition.

        :param extra_filters: Optional parameter for more filtering
        :param params: PaginationParams with ordering and filtering information

        :return: PaginatedResponse
        """
        return await self._fetch_paginated(
            model=ResearcherMetricORM,
            params=params,
            search_columns=[
                ResearcherMetricORM.source,
            ],
            joins=[
                ResearcherProfileORM
            ],
            extra_filters=extra_filters,
        )


    async def get_by_id(
            self,
            metric_id: uuid.UUID
    ) -> Optional[ResearcherMetric]:
        """
        Asynchronous function to fetch researcher_metric by id.
        If there is no metric with the given id, the return is None.
        FOR INTERNAL USE ONLY.

        :param metric_id: internal system id of the metric to be fetched

        :return Optional[ResearcherMetric]:
        """

        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(ResearcherMetricORM.id == metric_id)
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None


    async def get_all(
            self
    ) -> list[ResearcherMetric]:
        """
        Asynchronous function to fetch all the researcher_metric.
        If there are no metrics, the list is returned empty.
        FOR INTERNAL USE ONLY.

        :return list[ResearcherMetric]:
        """

        result = await self._session.execute(
            select(ResearcherMetricORM)
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    async def save(
            self,
            entity: ResearcherMetric
    ) -> ResearcherMetric:
        """
        Asynchronous function to save the changes made. Returns the saved metric.

        :param entity: Metric to be saved

        :return ResearcherMetric:
        """

        orm = ResearcherMetricORM.from_domain(entity)

        merged = await self._session.merge(orm)

        try:
            await self._session.flush()
        except Exception as e:
            raise e

        return merged.to_domain()

    async def delete(
            self,
            metric_id: uuid.UUID
    ) -> None:
        """
        Asynchronous function to delete a metric by id.

        :param metric_id: internal system id of the metric to be deleted
        """
        await self._session.execute(
            delete(ResearcherMetricORM).where(ResearcherMetricORM.id == metric_id)
        )

        await self._session.flush()

    async def fetch_latest_by_user(
            self,
            source: str | None = None,
            pagination: PaginationParams = None
    ) -> PaginatedResponse:
        m = ResearcherMetricORM

        subq = (
            select(
                m.researcher_id,
                func.max(m.date).label("max_date")
            )
            .group_by(m.researcher_id)
        )

        if source:
            subq = subq.where(m.source == source)

        subq = subq.subquery()

        base_query = (
            select(m)
            .join(
                subq,
                (m.researcher_id == subq.c.researcher_id) &
                (m.date == subq.c.max_date)
            )
        )

        if source:
            base_query = base_query.where(m.source == source)

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        if pagination:
            column = getattr(m, pagination.sort_by, None)
            if column is None:
                column = m.date

            if pagination.sort_dir == "desc":
                base_query = base_query.order_by(desc(column))
            else:
                base_query = base_query.order_by(asc(column))

            offset = (pagination.page - 1) * pagination.page_size
            base_query = base_query.offset(offset).limit(pagination.page_size)

        result = await self._session.execute(base_query)
        rows = result.scalars().all()

        items = [r.to_domain() for r in rows]

        page_size = pagination.page_size if pagination else 20
        current_page = pagination.page if pagination else 1
        pages = math.ceil(total / page_size) if total > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=current_page,
            page_size=page_size,
            pages=pages
        )

    async def get_by_researcher_id(
            self,
            researcher_id: uuid.UUID
    ) -> list[ResearcherMetric]:
        """
        Asynchronous function to fetch researcher_metric by researcher_id.
        If there are no metrics for the researcher, an empty list is returned.

        :param researcher_id: researcher profile id

        :return list[ResearcherMetric]:
        """
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(ResearcherMetricORM.researcher_id == researcher_id)
        )

        return [obj.to_domain() for obj in result.scalars().all()]
