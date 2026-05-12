import uuid
from typing import Optional

from pydantic import BaseModel

from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import \
    ResearcherMetricResponse


class ResearcherProfileResponse(BaseModel):
    id: uuid.UUID

    scholar_id: Optional[str] = None
    orcid: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None

    metrics: list[ResearcherMetricResponse]
    keywords: list[str]
    biography: str

    model_config = {"from_attributes": True}

class ResearcherProfileCreate(BaseModel):
    keywords: Optional[list[str]] = []

    # External ID's, all optional
    scholar_id: Optional[str] = None
    orcid: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None

    # From ORCID
    biography: Optional[str] = None
    affiliation: Optional[str] = None

    model_config = {"from_attributes": True}

class ResearcherProfileUpdate(BaseModel):
    scholar_id: Optional[str] = None
    orcid: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None

    metrics: Optional[list[ResearcherMetricResponse]] = []
    keywords: Optional[list[str]] = []
    biography: Optional[str] = []
    affiliation: Optional[str] = None

model_config = {"from_attributes": True}

