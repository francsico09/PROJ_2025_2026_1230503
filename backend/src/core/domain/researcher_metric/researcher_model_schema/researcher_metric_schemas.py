from datetime import datetime

import uuid
from typing import Optional
from pydantic import BaseModel, Field

from src.core.domain.researcher_metric.researcher_model_schema.source_schemas import SourceModel

class MetricPublicationCreate(BaseModel):
    title: str
    times_cited: int
    year: int | None = None
    doi: str | None = None
    source_title: str | None = None

class MetricPublicationResponse(BaseModel):
    title: str
    times_cited: int
    year: Optional[int] = None
    doi: Optional[str] = None
    source_title:   Optional[str] = None

    model_config = {"from_attributes": True}

class ResearcherMetricResponse(BaseModel):
    id: uuid.UUID
    researcher_id: uuid.UUID
    extraction_run_id: uuid.UUID
    source: SourceModel
    date: datetime

    # Commons
    h_index: int
    total_citations: int
    total_publications: int

    # Only Scholar
    i10_index: int | None = None
    h_index_5y: int | None = None
    i10_index_5y: int | None = None
    citations_5y: int | None = None
    cites_per_year: dict | None = None

    publications: list[MetricPublicationResponse] | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ResearcherMetricCreate(BaseModel):
    researcher_id: uuid.UUID
    extraction_run_id: Optional[uuid.UUID] = None
    source: SourceModel
    date: Optional[datetime] = None

    h_index: int
    total_citations: int
    total_publications: int

    i10_index: int | None = None
    h_index_5y: int | None = None
    i10_index_5y: int | None = None
    citations_5y: int | None = None
    cites_per_year: dict | None = None

    publications: list[dict] = []

    model_config = {"from_attributes": True, "populate_by_name": True}

class ResearcherMetricUpdate(BaseModel):
    h_index: Optional[int] = None
    total_citations: Optional[int] = None
    total_publications: Optional[int] = None
    i10_index: Optional[int] = None
    h_index_5y: Optional[int] = None
    i10_index_5y: Optional[int] = None
    citations_5y: Optional[int] = None
    cites_per_year: Optional[dict] = None
    source: Optional[SourceModel] = None

    model_config = {"from_attributes": True, "populate_by_name": True}

class OrgAverageMetricsResponse(BaseModel):
    source:              str
    researcher_count:    int

    h_index:             float
    i10_index:           Optional[float] = None
    total_citations:     float
    total_publications:  float
    h_index_5y:          Optional[float] = None
    i10_index_5y:        Optional[float] = None
    citations_5y:        Optional[float] = None

    model_config = {"from_attributes": True, "populate_by_name": True}