import datetime
import uuid
from typing import Optional

from pydantic.dataclasses import dataclass

from src.modules.metrics.model.source.model import Source
from src.modules.metrics.schema.metric_schemas import ResearcherMetricUpdate

@dataclass
class MetricPublication:
    title: str
    times_cited: int
    year: Optional[int] = None
    doi: Optional[str] = None
    source_title: Optional[str] = None

@dataclass
class ResearcherMetric:
    id: uuid.UUID
    researcher_id: uuid.UUID
    extraction_run_id: uuid.UUID
    source: Source

    # Date of extraction
    date: datetime.datetime

    # Common
    h_index: int
    total_citations: int
    total_publications: int

    # Scholar specific.
    i10_index: int | None = None
    i10_index_5y: int | None = None
    h_index_5y: int | None = None
    citations_5y: int | None = None
    cites_per_year: dict | None = None
    publications: list[MetricPublication] | None = None

    def update(self, data: ResearcherMetricUpdate):
        if data.h_index is not None:
            self.h_index = data.h_index

        if data.i10_index is not None:
            self.i10_index = data.i10_index

        if data.total_citations is not None:
            self.total_citations = data.total_citations

        if data.total_publications is not None:
            self.total_publications = data.total_publications