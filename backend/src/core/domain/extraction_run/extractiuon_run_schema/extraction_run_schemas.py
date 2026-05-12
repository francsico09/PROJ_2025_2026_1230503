import datetime
import uuid

from pydantic import BaseModel

from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionTrigger, \
    ExtractionStatus

from src.core.domain.researcher_metric.researcher_metric_model.source_model import SourceName

class ExtractionRunResponse(BaseModel):
    id: uuid.UUID
    researcher_id: uuid.UUID
    triggered_at: datetime.datetime
    triggered_by: ExtractionTrigger
    status: ExtractionStatus
    sources_attempted: list[SourceName]
    sources_succeeded: list[SourceName]

    model_config = {"from_attributes": True}


class ExtractionRunCreate(BaseModel):
    researcher_id: uuid.UUID
    triggered_at: datetime.datetime
    triggered_by: ExtractionTrigger
    status: ExtractionStatus
    sources_attempted: list[SourceName]
    sources_succeeded: list[SourceName]


class ExtractionRunUpdate(BaseModel):
    status: str | None = None
    sources_attempted: list[SourceName] | None = None
    sources_succeeded: list[SourceName] | None = None