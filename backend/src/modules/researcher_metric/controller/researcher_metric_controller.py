import datetime
import uuid

from fastapi import APIRouter, status, Depends

from src.core.repositories.repositories import Repositories
from src.modules.auth.auth import require_admin
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse
from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    ResearcherMetricResponse, ResearcherMetricCreate, ResearcherMetricUpdate
from src.modules.researcher_metric.service.researcher_metric_service import ResearcherMetricService
from src.core.domain.user.user_model.user_model import User

router = APIRouter(prefix="/researcher_metrics", tags=["ResearcherMetric"])

def get_researcher_metric_service() -> ResearcherMetricService:
    return ResearcherMetricService(Repositories())


@router.post(
    "/create_metric",
    response_model=ResearcherMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create researcher metric",
)
async def create_metric(
        metric_data: ResearcherMetricCreate,
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service)
) -> ResearcherMetricResponse:
    return await service.create_metric(metric_data)

@router.delete(
    "/{metric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete researcher metric",
)
async def delete_metric(
        metric_id: uuid.UUID,
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service)
) -> None:
    await service.delete_metric(metric_id)


@router.patch(
    "/{metric_id}",
    response_model=PaginatedResponse[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Update researcher metric",
)
async def update_metric(
        metric_id: uuid.UUID,
        metric_data: ResearcherMetricUpdate,
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service)
) -> ResearcherMetricResponse:
    return await service.update_metric(metric_id, metric_data)

@router.get(
    "/by-user/{user_id}",
    response_model=PaginatedResponse[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get researcher metric by user id",
)
async def fetch_metric_by_user(
        user_id: uuid.UUID,
        service: ResearcherMetricService = Depends(get_researcher_metric_service),
        params: PaginationParams=Depends()
) -> PaginatedResponse[ResearcherMetricResponse]:
    return await service.fetch_metrics_by_user(user_id, params)

@router.get(
    "/",
    response_model=PaginatedResponse[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all researcher researcher_metric",
)
async def fetch_metrics(
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service),
        params: PaginationParams = Depends()
) -> PaginatedResponse[ResearcherMetricResponse]:
    return await service.fetch(params)

@router.get(
    "/latest-by-user",
    response_model=PaginatedResponse[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get latest researcher metric per researcher",
)
async def fetch_latest_by_user(
        source: str | None = None,
        params: PaginationParams = Depends(),
        service: ResearcherMetricService = Depends(get_researcher_metric_service),
):
    return await service.fetch_latest_by_user(source, params)