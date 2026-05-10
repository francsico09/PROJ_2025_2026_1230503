import uuid

from sqlalchemy import select
from sqlalchemy import delete
from datetime import datetime

from src.database.models.researcher_metric_orm import ResearcherMetricORM
from src.modules.metrics.repository.metric_repository import ResearcherMetricRepository
from src.modules.metrics.model.researcher_metric_model import ResearcherMetric

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

"""
Implementation of the abstract methods from the GeneralRepository
and specific entity repository interfaces
"""
class PostgresResearcherMetricRepository(ResearcherMetricRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    """
    Asynchronous function to fetch metrics by researcher id. If there are no metrics associated with 
    the given researcher id, the list is returned empty.
    
    :param researcher_id UUID: internal system id of the researcher which the metrics are
    respective to.
    
    :return list[ResearcherMetric]:
    """
    async def get_by_researcher_id(
            self,
            researcher_id: uuid.UUID
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM).where(
                ResearcherMetricORM.researcher_id == researcher_id
            )
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch metrics by date of collection. If there are no metrics collected on
    that date, the list is returned empty.

    :param date date: date of the metric collection.
    
    :return list[ResearcherMetric]:
    """
    async def get_by_date(
            self,
            date: datetime
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(ResearcherMetricORM.date == date)
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch metrics by h-index. If there are no metrics with h_index equal
    to the value provided, the list is returned empty.
    
    :param value int: value of the required h-index
    
    :return list[ResearcherMetric]:
    """
    async def get_by_h_index(
            self,
            value: int
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(ResearcherMetricORM.h_index == value)
        )
        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch metrics by i10-index. If there are no metrics with i10_index equal
    to the value provided, the list is returned empty.
    
    :param value int: value of the required i10-index

    :return list[ResearcherMetric]:
    """
    async def get_by_i10_index(
            self,
            value: int
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(ResearcherMetricORM.i10_index == value)
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch metrics by total citations. If there are no metrics with total_citaions equal
    to the value provided, the list is returned empty.
    
    :param value int: value of the required total citations

    :return list[ResearcherMetric]:
    """
    async def get_by_total_citations(
            self,
            value: int
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(
                ResearcherMetricORM.total_citations == value
            )
        )
        return [obj.to_domain() for obj in result.scalars().all()]
    """
    Asynchronous function to fetch metrics by total publications. If there are no metrics with total_publications equal
    to the value provided, the list is returned empty.
    
    :param value int: value of the required total_publications

    :return list[ResearcherMetric]:
    """
    async def get_by_total_publications(
            self,
            value: int
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(
                ResearcherMetricORM.total_publications == value
            )
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch metrics by id. If there is no metric with the given id, the return is None.
    
    :param metric_id UUID: internal system id of the metric to be fetched
    
    :return Optional[ResearcherMetric]:
    """
    async def get_by_id(
            self,
            metric_id: uuid.UUID
    ) -> Optional[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
            .where(ResearcherMetricORM.id == metric_id)
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None

    """
    Asynchronous function to fetch all the metrics. If there are no merics, the list is returned empty.

    :return list[ResearcherMetric]:
    """
    async def get_all(
            self
    ) -> list[ResearcherMetric]:
        result = await self._session.execute(
            select(ResearcherMetricORM)
        )

        return [obj.to_domain() for obj in result.scalars().all()]
    """
    Asynchronous function to save the changes made. Returns the saved metric.

    :param entity ResearcherMetric: Metric to be saved

    :return ResearcherMetric:
    """
    async def save(
            self,
            entity: ResearcherMetric
    ) -> ResearcherMetric:
        orm = ResearcherMetricORM.from_domain(entity)

        merged = await self._session.merge(orm)

        try:
            await self._session.flush()
        except Exception as e:
            raise e

        return merged.to_domain()

    """
    Asynchronous function to delete a metric by id.

    :param metric_id UUID: internal system id of the metric to be deleted
    """
    async def delete(
            self,
            metric_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(ResearcherMetricORM).where(ResearcherMetricORM.id == metric_id)
        )

        await self._session.flush()
