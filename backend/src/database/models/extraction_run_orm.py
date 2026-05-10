import uuid
import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from src.database.base.base import Base


class ExtractionRunORM(Base):
    __tablename__ = "extraction_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    researcher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("researcher_profiles.id"),
        nullable=False
    )
    triggered_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    triggered_by = Column(String, nullable=False)
    status = Column(String, nullable=False, default='pending')
    sources_attempted = Column(ARRAY(String), nullable=False, default=[])
    sources_succeeded = Column(ARRAY(String), nullable=False, default=[])

    metrics = relationship(
        "ResearcherMetricORM",
        back_populates="extraction_run",
        cascade="all, delete-orphan"
    )

    def to_domain(self):
        from src.modules.extraction.model.extraction_run_model import (ExtractionRun, ExtractionTrigger, ExtractionStatus)
        from src.modules.metrics.model.source.model import SourceName

        return ExtractionRun(
            id=self.id,
            researcher_id=self.researcher_id,
            triggered_at=self.triggered_at,
            triggered_by=ExtractionTrigger(self.triggered_by),
            status=ExtractionStatus(self.status),
            sources_attempted=[SourceName(s) for s in self.sources_attempted],
            sources_succeeded=[SourceName(s) for s in self.sources_succeeded],
        )

    @staticmethod
    def from_domain(entity):
        return ExtractionRunORM(
            id=entity.id,
            researcher_id=entity.researcher_id,
            triggered_at=entity.triggered_at,
            triggered_by=entity.triggered_by.value,
            status=entity.status.value,
            sources_attempted=[s.value for s in entity.sources_attempted],
            sources_succeeded=[s.value for s in entity.sources_succeeded],
        )