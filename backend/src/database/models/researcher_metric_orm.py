import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from src.database.base.base import Base
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric


class ResearcherMetricORM(Base):
    __tablename__ = "researcher_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    researcher_id = Column(UUID(as_uuid=True), ForeignKey("researcher_profiles.id"), nullable=False)
    extraction_run_id = Column(UUID(as_uuid=True), ForeignKey("extraction_runs.id"), nullable=False)
    source = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)

    # Commons
    h_index = Column(Integer, nullable=False)
    total_citations = Column(Integer, nullable=False)
    total_publications = Column(Integer, nullable=False)

    # Scholar
    i10_index = Column(Integer)
    h_index_5y = Column(Integer)
    i10_index_5y = Column(Integer)
    citations_5y = Column(Integer)
    cites_per_year = Column(JSONB)

    # WoS
    publications = Column(JSONB)

    extraction_run = relationship("ExtractionRunORM", back_populates="metrics")
    profile = relationship("ResearcherProfileORM", back_populates="metrics")

    def to_domain(self):
        from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import MetricPublication
        from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName

        source_obj = Source(name=SourceName(self.source), url="")

        publications = [
            MetricPublication(
                title=p["title"],
                times_cited=p["times_cited"],
                year=p.get("year"),
                doi=p.get("doi"),
                source_title=p.get("source_title"),
            )
            for p in (self.publications or [])
        ]

        return ResearcherMetric(
            id=self.id,
            researcher_id=self.researcher_id,
            extraction_run_id=self.extraction_run_id,
            source=source_obj,
            date=self.date,
            h_index=self.h_index,
            total_citations=self.total_citations,
            total_publications=self.total_publications,
            i10_index=self.i10_index,
            h_index_5y=self.h_index_5y,
            i10_index_5y=self.i10_index_5y,
            citations_5y=self.citations_5y,
            cites_per_year=self.cites_per_year,
            publications=publications,
        )

    @staticmethod
    def from_domain(entity):
        publications = [
            {
                "title": p.title,
                "times_cited": p.times_cited,
                "year": p.year,
                "doi": p.doi,
                "source_title": p.source_title,
            }
            for p in (entity.publications or [])
        ]

        return ResearcherMetricORM(
            id=entity.id,
            researcher_id=entity.researcher_id,
            extraction_run_id=entity.extraction_run_id,
            source=entity.source.name.value,
            date=entity.date,
            h_index=entity.h_index,
            total_citations=entity.total_citations,
            total_publications=entity.total_publications,
            i10_index=entity.i10_index,
            h_index_5y=entity.h_index_5y,
            i10_index_5y=entity.i10_index_5y,
            citations_5y=entity.citations_5y,
            cites_per_year=entity.cites_per_year,
            publications=publications if publications else None,
        )