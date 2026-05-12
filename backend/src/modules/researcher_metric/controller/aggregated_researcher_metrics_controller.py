from fastapi import APIRouter, Depends, Query
from starlette import status

from src.core.repositories.repositories import Repositories
from src.modules.auth.auth import require_admin

from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    OrgAverageMetricsResponse
from src.core.domain.user.user_model.user_model import User
from src.modules.researcher_metric.service.aggregated_metrics_service import AggregatedMetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

def get_agg_metrics_service() -> AggregatedMetricsService:
    return AggregatedMetricsService(Repositories())


@router.get(
    "/averages",
    response_model=OrgAverageMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get organisation-wide average metrics for a given source",
)
async def get_org_averages(
        source: str | None = Query(None, description="Metric source — e.g. 'scholar' or 'orcid'"),
        service: AggregatedMetricsService = Depends(get_agg_metrics_service),
) -> OrgAverageMetricsResponse:
    if source == "null" or source == "":
        source = None

    return await service.get_org_averages(source)