import datetime
import uuid

from abc import abstractmethod

from dataclasses import dataclass

from src.core.repositories.general_repository import GeneralRepository
from src.modules.metrics.model.researcher_metric_model import ResearcherMetric


@dataclass
class ResearcherMetricRepository(GeneralRepository[ResearcherMetric]):
    @abstractmethod
    def get_by_researcher_id(self, researcher_id: uuid.UUID) -> list[ResearcherMetric]: pass

    @abstractmethod
    def get_by_date(self, date: datetime.date) -> list[ResearcherMetric]: pass

    @abstractmethod
    def get_by_h_index(self, value: int) -> list[ResearcherMetric]: pass

    @abstractmethod
    def get_by_i10_index(self, value: int) -> list[ResearcherMetric]: pass

    @abstractmethod
    def get_by_total_citations(self, value: int) -> list[ResearcherMetric]: pass

    @abstractmethod
    def get_by_total_publications(self, value: int) -> list[ResearcherMetric]: pass
