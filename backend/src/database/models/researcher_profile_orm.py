import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from src.database.base.base import Base
from src.database.models.researcher_metric_orm import ResearcherMetricORM




class ResearcherProfileORM(Base):
    __tablename__ = "researcher_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orcid = Column(String)
    scholar_id = Column(String)
    wos_id = Column(String)
    scopus_id = Column(String)
    biography = Column(String)
    affiliation = Column(String)
    keywords = Column(ARRAY(String))

    metrics = relationship(
        "ResearcherMetricORM",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ResearcherMetricORM.date"
    )

    def to_domain(self):
        from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import ResearcherProfile

        return ResearcherProfile(
            id=self.id,
            orcid=self.orcid,
            scholar_id=self.scholar_id,
            wos_id=self.wos_id,
            scopus_id=self.scopus_id,
            biography=self.biography,
            affiliation=self.affiliation,
            keywords=self.keywords or [],
            metrics=[m.to_domain() for m in self.metrics]
        )

    @staticmethod
    def from_domain(entity):
        return ResearcherProfileORM(
            id=entity.id,
            orcid=entity.orcid,
            scholar_id=entity.scholar_id,
            wos_id=entity.wos_id,
            scopus_id=entity.scopus_id,
            biography=entity.biography,
            affiliation=entity.affiliation,
            keywords=entity.keywords,
            metrics=[ResearcherMetricORM.from_domain(m) for m in entity.metrics]
        )