import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from starlette import status

from src.core.repositories.repositories import Repositories

from src.modules.auth.auth import get_current_user
from src.modules.export.service.export_service import ExportService

from src.core.domain.export.export_schema.export_schemas import ExportFormat, ExportScope
from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_model.user_role import UserRole

router = APIRouter(prefix="/export", tags=["Export"])

CONTENT_TYPES = {
    ExportFormat.csv:  "text/csv",
    ExportFormat.xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def get_export_service() -> ExportService:
    return ExportService(Repositories())


@router.get(
    "/researcher_metric/{researcher_id}",
    summary="Export researcher researcher_metric.",
)
async def export_metrics(
        researcher_id: uuid.UUID,
        format:  ExportFormat  = Query(ExportFormat.xlsx),
        scope:   ExportScope   = Query(ExportScope.history),
        start_date: date | None = Query(None),
        end_date: date | None = Query(None),
        current_user: User     = Depends(get_current_user),
        service: ExportService = Depends(get_export_service),
) -> Response:
    if current_user.role != UserRole.admin and str(current_user.id) != str(researcher_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only export your own researcher_metric.",
        )

    data, filename = await service.export(researcher_id, format, scope, start_date, end_date)

    return Response(
        content=data,
        media_type=CONTENT_TYPES[format],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/researcher_metric",
    summary="Export all researcher researcher_metric",
)
async def export_all_metrics(
        fmt: ExportFormat  = Query(ExportFormat.xlsx),
        scope:  ExportScope   = Query(ExportScope.history),
        start_date: date | None = Query(None),
        end_date: date | None = Query(None),
        current_user: User    = Depends(get_current_user),
        service: ExportService = Depends(get_export_service),
) -> Response:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can export all metrics.",
        )

    data, filename = await service.export_all(fmt, scope, start_date, end_date)

    return Response(
        content=data,
        media_type=CONTENT_TYPES[format],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )