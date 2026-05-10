import datetime
import uuid

from fastapi import APIRouter, status, Depends

from src.core.repositories.repositories import Repositories
from src.modules.auth.auth import require_admin
from src.modules.metrics.schema.metric_schemas import ResearcherMetricResponse, ResearcherMetricUpdate, \
    ResearcherMetricCreate
from src.modules.metrics.service.researcher_metric_service import ResearcherMetricService
from src.modules.user.model.user_model import User

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
    response_model=ResearcherMetricResponse,
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
    response_model=list[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get researcher metric by user id",
)
async def get_metric_by_user_id(
        user_id: uuid.UUID,
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service)
) -> list[ResearcherMetricResponse]:
    return await service.get_metric_by_user_id(user_id)


@router.get(
    "/by-date/{date}",
    response_model=list[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get researcher metric by date",
)
async def get_metric_by_date(
        date: datetime.date,
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service)
) -> list[ResearcherMetricResponse]:
    return await service.get_metric_by_date(date)


@router.get(
    "/",
    response_model=list[ResearcherMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all researcher metrics",
)
async def list_metrics(
        _: User = Depends(require_admin),
        service: ResearcherMetricService = Depends(get_researcher_metric_service),
) -> list[ResearcherMetricResponse]:
    return await service.list_metrics()
