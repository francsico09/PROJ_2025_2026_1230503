from dataclasses import field
from typing import Optional
from pydantic.dataclasses import dataclass
from src.modules.normalization.models.metric.normalized_metric import NormalizedMetric
from src.modules.normalization.models.profile.normalized_researcher_profile import NormalizedProfile

from src.modules.extraction.model.extraction_run_model import ExtractionRun


@dataclass
class RawScholarMetrics:
    scholar_id: str
    name: str
    h_index: int
    i10_index: int
    total_citations: int
    total_publications: int
    url: str
    h_index_5y: int = 0
    i10_index_5y: int = 0
    citations_5y: int = 0
    cites_per_year: dict = field(default_factory=dict)


@dataclass
class RawWosPublication:
    title: str
    year: int | None
    times_cited: int
    doi: str | None = None
    source_title: str | None = None


@dataclass
class RawWosMetrics:
    user_name: str
    keywords: list[str]
    i10_index: int
    h_index: int
    total_citations: int
    total_publications: int
    url: str

    publications: list[RawWosPublication] = field(default_factory=list)


@dataclass
class RawScopusMetrics:
    scopus_id: str
    h_index: int
    total_citations: int
    total_publications: int
    url: str


@dataclass
class RawOrcidProfile:
    orcid_id: str
    given_name: str
    family_name: str
    email: Optional[str]
    biography: Optional[str]
    keywords: list[str] = field(default_factory=list)

    # External ID's it might contain
    scholar_id: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None


@dataclass
class RawExtractionResult:
    user_id: str
    run: ExtractionRun
    scholar: Optional[RawScholarMetrics] = None
    wos: Optional[RawWosMetrics] = None
    scopus: Optional[RawScopusMetrics] = None
    orcid: Optional[RawOrcidProfile] = None
    errors: list[str] = field(default_factory=list)


@dataclass
class NormalizationResult:
    user_id: str
    run: ExtractionRun
    metrics: list[NormalizedMetric] = field(default_factory=list)
    profile_update: Optional[NormalizedProfile] = None
    skipped_reasons: list[str] = field(default_factory=list)