from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    OrgAverageMetricsResponse
from src.core.repositories.repositories import Repositories
from src.database.models.researcher_metric_orm import ResearcherMetricORM

class AggregatedMetricsService:

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    async def get_org_averages(self, source: str) -> OrgAverageMetricsResponse:
        async with self._repos as repos:
            session: AsyncSession = repos._session

            row_number = (
                func.row_number()
                .over(
                    partition_by=ResearcherMetricORM.researcher_id,
                    order_by=ResearcherMetricORM.date.desc(),
                )
                .label("rn")
            )

            subq = (
                select(
                    ResearcherMetricORM.researcher_id,
                    ResearcherMetricORM.h_index,
                    ResearcherMetricORM.i10_index,
                    ResearcherMetricORM.total_citations,
                    ResearcherMetricORM.total_publications,
                    ResearcherMetricORM.h_index_5y,
                    ResearcherMetricORM.i10_index_5y,
                    ResearcherMetricORM.citations_5y,
                    row_number,
                )
                .where(ResearcherMetricORM.source == source)
                .subquery()
            )

            latest = select(subq).where(subq.c.rn == 1).subquery()

            avg_query = select(
                func.count(latest.c.researcher_id).label("researcher_count"),
                func.avg(latest.c.h_index).label("h_index"),
                func.avg(latest.c.i10_index).label("i10_index"),
                func.avg(latest.c.total_citations).label("total_citations"),
                func.avg(latest.c.total_publications).label("total_publications"),
                func.avg(latest.c.h_index_5y).label("h_index_5y"),
                func.avg(latest.c.i10_index_5y).label("i10_index_5y"),
                func.avg(latest.c.citations_5y).label("citations_5y"),
            )

            result = (await session.execute(avg_query)).one()

        def _round(val, decimals=1):
            return round(float(val), decimals) if val is not None else None

        return OrgAverageMetricsResponse(
            source=source,
            researcher_count=result.researcher_count or 0,
            h_index=_round(result.h_index) or 0.0,
            i10_index=_round(result.i10_index),
            total_citations=_round(result.total_citations) or 0.0,
            total_publications=_round(result.total_publications) or 0.0,
            h_index_5y=_round(result.h_index_5y),
            i10_index_5y=_round(result.i10_index_5y),
            citations_5y=_round(result.citations_5y),
        )