import uuid
from enum import Enum

from pydantic import BaseModel


class ExportFormat(str, Enum):
    csv  = "csv"
    xlsx = "xlsx"


class ExportScope(str, Enum):
    latest  = "latest"
    history = "history"
    custom  = "custom"


class ExportRequest(BaseModel):
    researcher_id: uuid.UUID
    format:        ExportFormat
    scope:         ExportScope