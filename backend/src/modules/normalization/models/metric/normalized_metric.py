import uuid

from typing import Optional
from pydantic.dataclasses import dataclass

from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import MetricPublication
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source


@dataclass
class NormalizedMetric:
    researcher_id: uuid.UUID
    source: Source
    h_index: int
    total_citations: int
    total_publications: int
    is_duplicate: bool = False

    # Só Scholar
    i10_index: Optional[int] = None
    h_index_5y: Optional[int] = None
    i10_index_5y: Optional[int] = None
    citations_5y: Optional[int] = None
    cites_per_year: Optional[dict] = None

    publications: Optional[list[MetricPublication]] = None
