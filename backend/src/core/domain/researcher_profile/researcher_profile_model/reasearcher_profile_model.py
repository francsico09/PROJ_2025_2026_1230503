import uuid
from typing import Optional

from pydantic.dataclasses import dataclass

from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric
from src.core.domain.researcher_profile.researcher_profile_schema.researcher_profile_schemas import \
    ResearcherProfileUpdate


@dataclass
class ResearcherProfile:
    id: uuid.UUID
    keywords: list[str]
    metrics: list[ResearcherMetric]

    # External ID's, all optional
    scholar_id: Optional[str] = None
    orcid: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None

    # From ORCID
    biography: Optional[str] = None
    affiliation: Optional[str] = None

    def get_identifier(
            self,
            source: str
    ) -> str | None:
        return {
            'scholar': self.scholar_id,
            'wos':     self.wos_id,
            'scopus':  self.scopus_id,
            'orcid':   self.orcid,
        }.get(source)

    def update(
            self,
            data: ResearcherProfileUpdate
    ):
        if data.orcid is not None:
            self.orcid = data.orcid

        if data.scholar_id is not None:
            self.scholar_id = data.scholar_id

        if data.wos_id is not None:
            self.wos_id = data.wos_id

        if data.scopus_id is not None:
            self.scopus_id = data.scopus_id

        if data.keywords is not None:
            self.keywords = data.keywords

        if data.biography is not None:
            self.biography = data.biography

        if data.affiliation is not None:
            self.affiliation = data.affiliation
