import datetime
import uuid

from pydantic.dataclasses import dataclass
from enum import Enum

from src.core.domain.researcher_metric.researcher_metric_model.source_model import SourceName


class ExtractionTrigger(str, Enum):
    manual    = 'manual'
    scheduled = 'scheduled'

class ExtractionStatus(str, Enum):
    pending   = 'pending'
    completed = 'completed'
    partial   = 'partial'
    failed    = 'failed'

@dataclass
class ExtractionRun:
    id: uuid.UUID
    researcher_id: uuid.UUID
    triggered_at: datetime.datetime
    triggered_by: ExtractionTrigger
    status: ExtractionStatus
    sources_attempted: list[SourceName]
    sources_succeeded: list[SourceName]
