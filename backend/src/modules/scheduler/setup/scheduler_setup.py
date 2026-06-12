import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.repositories.repositories import Repositories
from src.modules.extraction.extractor.orcid_extractor import OrcidExtractor
from src.modules.extraction.extractor.scholar_extractor import ScholarExtractor
from src.modules.extraction.service.extraction_service import ExtractionService
from src.modules.extraction.service.pipeline_service import PipelineService
from src.modules.normalization.service.normalization_service import NormalizationService
from src.modules.researcher_metric.service.researcher_metric_service import ResearcherMetricService
from src.modules.scheduler.service.scheduler_service import SchedulerService

from src.modules.extraction.extractor.scopus_extractor import ScopusExtractor
from src.modules.extraction.extractor.wos_extractor import WosExtractor

from src.modules.extraction.service.extraction_run_service import ExtractionRunService

logger = logging.getLogger("scheduler")

_scheduler: AsyncIOScheduler | None = None


def _build_pipeline() -> PipelineService:
    """Constrói o pipeline de extracção com todas as dependências."""
    repos = Repositories()
    scholar = ScholarExtractor()
    orcid = OrcidExtractor()
    scopus = ScopusExtractor()
    wos = WosExtractor()

    extraction    = ExtractionService(repos, scholar, orcid, wos, scopus)
    normalization = NormalizationService(repos)
    metrics_svc   = ResearcherMetricService(repos)
    run_svc = ExtractionRunService(repos)

    return PipelineService(repos, extraction, normalization, metrics_svc, run_svc)


def create_scheduler() -> AsyncIOScheduler:
    """Cria e configura o scheduler com o job diário."""
    scheduler = AsyncIOScheduler(timezone="Europe/Lisbon")

    pipeline         = _build_pipeline()
    scheduler_service = SchedulerService(pipeline)

    scheduler.add_job(
        func=scheduler_service.run_daily_extraction,
        trigger=CronTrigger(hour=3, minute=0),  # 03:00 todos os dias
        id="daily_extraction",
        name="Daily researcher metrics extraction",
        replace_existing=True,
        misfire_grace_time=3600,  # tolera até 1h de atraso (ex: container a reiniciar)
    )

    logger.info("Scheduler configured — daily extraction at 03:00 Europe/Lisbon")
    return scheduler


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = create_scheduler()
    _scheduler.start()
    logger.info("Scheduler started")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")