from dataclasses import dataclass

from src.core.repositories.general_repository import GeneralRepository

from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric


@dataclass
class ResearcherMetricRepository(GeneralRepository[ResearcherMetric]): ...
