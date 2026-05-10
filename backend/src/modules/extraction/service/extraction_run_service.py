import datetime
import uuid

from src.core.repositories.repositories import Repositories
from src.modules.metrics.model.source.model import Source, SourceName
from src.modules.metrics.schema.metric_schemas import ResearcherMetricResponse, ResearcherMetricCreate, \
    ResearcherMetricUpdate
from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile
from src.modules.metrics.model.researcher_metric_model import ResearcherMetric
from src.modules.extraction.model.extraction_run_model import ExtractionRun
from src.modules.extraction.schema.extraction_run_schemas import ExtractionRunCreate, ExtractionRunResponse


class ExtractionRunService:
    def __init__(self, _repos: Repositories) -> None:
        self._repos = _repos

    """
    Asynchronous function to create a new metric in the system. Only allowed to admins.
    If successful, the newly added metric is returned, else an exception is raised
    
    :param metric ResearcherMetric: ResearcherMetric to be created.
    
    :return ResearcherMetricResponse:
    
    :raises: HTTP_404_NOT_FOUND if the metric is not found
    """
    async def create_run(
            self,
            run_data: ExtractionRunCreate,
            repos: Repositories = None
    ) -> ExtractionRunResponse:
        if repos is None:
            async with self._repos as r:
                return await self._execute_create_run(run_data, r)
        return await self._execute_create_run(run_data, repos)

    @staticmethod
    async def _execute_create_run(run_data, repos):
        run = ExtractionRun(
            id=uuid.uuid4(),
            researcher_id=run_data.researcher_id,
            triggered_at=datetime.datetime.now(),
            triggered_by=run_data.triggered_by,
            status=run_data.status,
            sources_attempted=run_data.sources_attempted,
            sources_succeeded=run_data.sources_succeeded,
        )
        await repos.extraction_runs.save(run)
        # Note: No commit here! Let the Pipeline decide.
        return ExtractionRunResponse.model_validate(run)
