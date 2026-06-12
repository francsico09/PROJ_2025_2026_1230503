import uuid

from fastapi import APIRouter, Depends, status

from src.core.settings.settings import settings
from src.modules.auth.auth import require_admin, get_current_user
from src.modules.extraction.service.pipeline_service import PipelineService, ExtractionPipelineResult
from src.modules.extraction.extractor.orcid_extractor import OrcidExtractor
from src.modules.extraction.extractor.scholar_extractor import ScholarExtractor
from src.modules.extraction.extractor.wos_extractor import WosExtractor
from src.modules.extraction.extractor.scopus_extractor import ScopusExtractor

from src.core.domain.user.user_model.user_model import User

router = APIRouter(prefix="/extraction", tags=["Extraction"])


def get_pipeline_service() -> PipelineService:
    from src.core.repositories.repositories import Repositories
    from src.modules.extraction.service.extraction_service import ExtractionService
    from src.modules.normalization.service.normalization_service import NormalizationService
    from src.modules.researcher_metric.service.researcher_metric_service import ResearcherMetricService
    from src.modules.extraction.service.extraction_run_service import ExtractionRunService

    repos = Repositories()
    scholar = ScholarExtractor()
    orcid = OrcidExtractor()
    wos = WosExtractor()
    scopus = ScopusExtractor()

    extraction = ExtractionService(repos, scholar, orcid, wos, scopus)
    normalization = NormalizationService(repos)
    metric_service = ResearcherMetricService(repos)
    run_service = ExtractionRunService(repos)

    return PipelineService(repos, extraction, normalization, metric_service, run_service)


@router.post(
    "/run-all",
    status_code=status.HTTP_200_OK,
    summary="runs the extraction pipeline for all active users",
)
async def run_extraction_for_all(
    _: User = Depends(require_admin),
    service: PipelineService = Depends(get_pipeline_service),
) -> dict:
    results = await service.run_for_all_users()
    return {
        "total": len(results),
        "metrics_created": sum(1 for r in results if r.metric_created),
        "profiles_updated": sum(1 for r in results if r.profile_updated),
        "with_errors": sum(1 for r in results if r.errors),
    }


@router.post(
    "/run/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Runs the extractions pipeline for one user",
)
async def run_extraction_for_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
) -> dict:
    if current_user.role.value != 'admin' and current_user.id != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    result: ExtractionPipelineResult = await service.run_for_user(user_id)

    return {
        "user_id": result.user_id,
        "metric_created": result.metric_created,
        "profile_updated": result.profile_updated,
        "skipped": result.skipped_reasons,
        "errors": result.errors,
        "metrics": result.metrics
    }
