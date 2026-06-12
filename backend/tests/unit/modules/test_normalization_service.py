import uuid
from dataclasses import field
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import (
    ExtractionRun,
    ExtractionStatus,
    ExtractionTrigger,
)
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import (
    MetricPublication,
    ResearcherMetric,
)
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName
from src.modules.normalization.models.metric.normalized_metric import NormalizedMetric
from src.modules.normalization.models.result.normalization_result import (
    NormalizationResult,
    RawExtractionResult,
    RawOrcidProfile,
    RawScholarMetrics,
    RawWosMetrics,
    RawWosPublication,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repos():
    """Cria um mock das repositories com contexto assíncrono."""
    repos = AsyncMock()
    repos.metrics = AsyncMock()
    repos.profiles = AsyncMock()
    repos.users = AsyncMock()
    repos.extraction_runs = AsyncMock()
    repos.commit = AsyncMock()
    repos.__aenter__ = AsyncMock(return_value=repos)
    repos.__aexit__ = AsyncMock(return_value=None)
    return repos


@pytest.fixture
def researcher_id():
    return uuid.uuid4()


@pytest.fixture
def extraction_run(researcher_id):
    return ExtractionRun(
        id=uuid.uuid4(),
        researcher_id=researcher_id,
        triggered_at=datetime.now(timezone.utc),
        triggered_by=ExtractionTrigger.created_by_admin,
        status=ExtractionStatus.completed,
        sources_attempted=[SourceName.scholar],
        sources_succeeded=[SourceName.scholar],
    )


@pytest.fixture
def normalization_service(mock_repos):
    from src.modules.normalization.service.normalization_service import NormalizationService
    return NormalizationService(mock_repos)


@pytest.fixture
def raw_scholar():
    return RawScholarMetrics(
        scholar_id="scholar_abc",
        name="Ana Costa",
        h_index=15,
        i10_index=20,
        total_citations=500,
        total_publications=30,
        url="https://scholar.google.com/citations?user=scholar_abc",
        h_index_5y=10,
        i10_index_5y=12,
        citations_5y=200,
        cites_per_year={"2022": 80, "2023": 120},
    )


@pytest.fixture
def raw_wos():
    return RawWosMetrics(
        user_name="wos_user",
        keywords=["AI", "ML"],
        i10_index=8,
        h_index=12,
        total_citations=300,
        total_publications=25,
        url="https://wos.example.com/wos_user",
        publications=[
            RawWosPublication(title="Paper A", year=2023, times_cited=50, doi="10.1000/xyz", source_title="Nature"),
            RawWosPublication(title="Paper B", year=2022, times_cited=20, doi=None, source_title=None),
        ],
    )


@pytest.fixture
def raw_orcid():
    return RawOrcidProfile(
        orcid_id="0000-0001-2345-6789",
        given_name="Ana",
        family_name="Costa",
        email="ana@example.com",
        biography="Researcher in AI",
        keywords=["NLP", "deep learning"],
        scholar_id="scholar_abc",
        wos_id="wos_123",
        scopus_id="scopus_456",
    )


@pytest.fixture
def raw_result(researcher_id, extraction_run):
    return RawExtractionResult(
        user_id=str(researcher_id),
        run=extraction_run,
    )


@pytest.fixture
def sample_profile_mock(researcher_id):
    profile = MagicMock()
    profile.id = researcher_id
    return profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_existing_metric(researcher_id: uuid.UUID, source: Source, extraction_date: date) -> MagicMock:
    """Build a mock metric that will be treated as a duplicate for the given date and source."""
    m = MagicMock(spec=ResearcherMetric)
    m.date = extraction_date
    m.source = source
    return m


# =============================================================================
# normalize — researcher profile lookup
# =============================================================================

class TestNormalizationServiceProfileLookup:
    """Tests for profile resolution at the start of normalize()."""

    @pytest.mark.asyncio
    async def test_normalize_skips_when_profile_not_found(
            self, normalization_service, mock_repos, raw_result
    ):
        """When no researcher profile is found, the result is marked as skipped."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = None

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 0
        assert any("not found" in r.lower() for r in result.skipped_reasons)

    @pytest.mark.asyncio
    async def test_normalize_skips_produces_no_metrics_without_profile(
            self, normalization_service, mock_repos, raw_result, raw_scholar
    ):
        """Even with scholar data present, no metrics are produced when profile is missing."""
        # Arrange
        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = None
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 0

    @pytest.mark.asyncio
    async def test_normalize_profile_lookup_uses_user_id(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """The profile lookup uses the user_id from the raw result."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        await normalization_service.normalize(raw_result)

        # Assert
        mock_repos.profiles.get_by_user_id.assert_called_once_with(raw_result.user_id)

    @pytest.mark.asyncio
    async def test_normalize_result_carries_user_id_and_run(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """The NormalizationResult always carries the original user_id and run."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert result.user_id == raw_result.user_id
        assert result.run == raw_result.run


# =============================================================================
# normalize — Scholar metrics
# =============================================================================

class TestNormalizationServiceScholar:
    """Tests for Scholar metric normalisation."""

    @pytest.mark.asyncio
    async def test_normalize_scholar_all_fields(
            self, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock
    ):
        """All Scholar fields are mapped correctly onto the NormalizedMetric."""
        # Arrange
        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 1
        m = result.metrics[0]
        assert m.h_index == raw_scholar.h_index
        assert m.i10_index == raw_scholar.i10_index
        assert m.total_citations == raw_scholar.total_citations
        assert m.total_publications == raw_scholar.total_publications
        assert m.h_index_5y == raw_scholar.h_index_5y
        assert m.i10_index_5y == raw_scholar.i10_index_5y
        assert m.citations_5y == raw_scholar.citations_5y
        assert m.cites_per_year == raw_scholar.cites_per_year
        assert m.source.name == SourceName.scholar

    @pytest.mark.asyncio
    async def test_normalize_scholar_source_url_contains_scholar_id(
            self, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock
    ):
        """The Scholar source URL is built from the scholar_id in the raw data."""
        # Arrange
        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert raw_scholar.scholar_id in result.metrics[0].source.url

    @pytest.mark.asyncio
    async def test_normalize_scholar_researcher_id_matches_profile(
            self, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock
    ):
        """The NormalizedMetric carries the profile's id as researcher_id."""
        # Arrange
        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert result.metrics[0].researcher_id == sample_profile_mock.id

    @pytest.mark.asyncio
    async def test_normalize_no_scholar_produces_no_scholar_metric(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """When raw.scholar is None, no Scholar metric is added to the result."""
        # Arrange
        raw_result.scholar = None
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        scholar_metrics = [m for m in result.metrics if m.source.name == SourceName.scholar]
        assert len(scholar_metrics) == 0


# =============================================================================
# normalize — WoS metrics
# =============================================================================

class TestNormalizationServiceWos:
    """Tests for WoS metric normalisation."""

    @pytest.mark.asyncio
    async def test_normalize_wos_all_fields(
            self, normalization_service, mock_repos, raw_result, raw_wos, sample_profile_mock
    ):
        """All WoS fields are mapped correctly onto the NormalizedMetric."""
        # Arrange
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 1
        m = result.metrics[0]
        assert m.h_index == raw_wos.h_index
        assert m.total_citations == raw_wos.total_citations
        assert m.total_publications == raw_wos.total_publications
        assert m.source.name == SourceName.wos

    @pytest.mark.asyncio
    async def test_normalize_wos_publications_are_converted(
            self, normalization_service, mock_repos, raw_result, raw_wos, sample_profile_mock
    ):
        """WoS publications are converted from RawWosPublication to MetricPublication."""
        # Arrange
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        pubs = result.metrics[0].publications
        assert len(pubs) == 2
        assert all(isinstance(p, MetricPublication) for p in pubs)
        assert pubs[0].title == "Paper A"
        assert pubs[0].times_cited == 50
        assert pubs[0].doi == "10.1000/xyz"
        assert pubs[0].source_title == "Nature"
        assert pubs[1].title == "Paper B"
        assert pubs[1].doi is None

    @pytest.mark.asyncio
    async def test_normalize_wos_publication_fields_preserved(
            self, normalization_service, mock_repos, raw_result, raw_wos, sample_profile_mock
    ):
        """Each publication field (year, doi, source_title) is preserved after conversion."""
        # Arrange
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        pub = result.metrics[0].publications[0]
        assert pub.year == 2023
        assert pub.doi == "10.1000/xyz"
        assert pub.source_title == "Nature"

    @pytest.mark.asyncio
    async def test_normalize_wos_empty_publications(
            self, normalization_service, mock_repos, raw_result, raw_wos, sample_profile_mock
    ):
        """WoS metric with no publications produces an empty publications list."""
        # Arrange
        raw_wos.publications = []
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert result.metrics[0].publications == []

    @pytest.mark.asyncio
    async def test_normalize_wos_source_url_contains_username(
            self, normalization_service, mock_repos, raw_result, raw_wos, sample_profile_mock
    ):
        """The WoS source URL is built from the user_name in the raw data."""
        # Arrange
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert raw_wos.user_name in result.metrics[0].source.url

    @pytest.mark.asyncio
    async def test_normalize_no_wos_produces_no_wos_metric(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """When raw.wos is None, no WoS metric is added to the result."""
        # Arrange
        raw_result.wos = None
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        wos_metrics = [m for m in result.metrics if m.source.name == SourceName.wos]
        assert len(wos_metrics) == 0


# =============================================================================
# normalize — ORCID profile update
# =============================================================================

class TestNormalizationServiceOrcid:
    """Tests for ORCID profile update normalisation."""

    @pytest.mark.asyncio
    async def test_normalize_orcid_profile_update_populated(
            self, normalization_service, mock_repos, raw_result, raw_orcid, sample_profile_mock
    ):
        """When ORCID data is present, profile_update is populated on the result."""
        # Arrange
        raw_result.orcid = raw_orcid
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert result.profile_update is not None
        assert result.profile_update.biography == raw_orcid.biography
        assert result.profile_update.keywords == raw_orcid.keywords
        assert result.profile_update.orcid_id == raw_orcid.orcid_id
        assert result.profile_update.scholar_id == raw_orcid.scholar_id
        assert result.profile_update.wos_id == raw_orcid.wos_id
        assert result.profile_update.scopus_id == raw_orcid.scopus_id

    @pytest.mark.asyncio
    async def test_normalize_orcid_researcher_id_matches_profile(
            self, normalization_service, mock_repos, raw_result, raw_orcid, sample_profile_mock
    ):
        """The profile_update carries the profile's id as researcher_id."""
        # Arrange
        raw_result.orcid = raw_orcid
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert result.profile_update.researcher_id == sample_profile_mock.id

    @pytest.mark.asyncio
    async def test_normalize_no_orcid_profile_update_is_none(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """When raw.orcid is None, profile_update remains None."""
        # Arrange
        raw_result.orcid = None
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert result.profile_update is None

    @pytest.mark.asyncio
    async def test_normalize_orcid_does_not_produce_a_metric(
            self, normalization_service, mock_repos, raw_result, raw_orcid, sample_profile_mock
    ):
        """ORCID data updates the profile but never adds a metric to the result."""
        # Arrange
        raw_result.orcid = raw_orcid
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 0


# =============================================================================
# normalize — multiple sources in one call
# =============================================================================

class TestNormalizationServiceMultipleSources:
    """Tests for normalize() when several sources are present simultaneously."""

    @pytest.mark.asyncio
    async def test_normalize_scholar_and_wos_produces_two_metrics(
            self, normalization_service, mock_repos, raw_result, raw_scholar, raw_wos, sample_profile_mock
    ):
        """When both Scholar and WoS data are present, two metrics are produced."""
        # Arrange
        raw_result.scholar = raw_scholar
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 2
        sources = {m.source.name for m in result.metrics}
        assert SourceName.scholar in sources
        assert SourceName.wos in sources

    @pytest.mark.asyncio
    async def test_normalize_all_sources_scholar_wos_orcid(
            self, normalization_service, mock_repos, raw_result, raw_scholar, raw_wos, raw_orcid, sample_profile_mock
    ):
        """With all three sources, two metrics and one profile_update are produced."""
        # Arrange
        raw_result.scholar = raw_scholar
        raw_result.wos = raw_wos
        raw_result.orcid = raw_orcid
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 2
        assert result.profile_update is not None

    @pytest.mark.asyncio
    async def test_normalize_no_sources_produces_empty_result(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """When all source fields are None, the result has no metrics and no profile_update."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 0
        assert result.profile_update is None
        assert len(result.skipped_reasons) == 0


# =============================================================================
# duplicate detection
# =============================================================================

class TestNormalizationServiceDuplicateDetection:
    """Tests for _is_duplicate_metric() and its effect on normalize()."""

    @pytest.mark.asyncio
    @patch("src.modules.normalization.service.normalization_service.date")
    async def test_scholar_metric_marked_as_duplicate_when_same_date_and_source(
            self, mock_date, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock, researcher_id
    ):
        """A Scholar metric extracted on the same date as an existing one is flagged as duplicate."""
        # Arrange
        today = date(2024, 6, 1)
        mock_date.today.return_value = today

        existing_source = Source(SourceName.scholar, "https://scholar.google.com/citations?user=scholar_abc")
        existing = _make_existing_metric(researcher_id, existing_source, today)

        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = [existing]

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 0
        assert any("Scholar" in r for r in result.skipped_reasons)

    @pytest.mark.asyncio
    @patch("src.modules.normalization.service.normalization_service.date")
    async def test_wos_metric_marked_as_duplicate_when_same_date_and_source(
            self, mock_date, normalization_service, mock_repos, raw_result, raw_wos, sample_profile_mock, researcher_id
    ):
        """A WoS metric extracted on the same date as an existing one is flagged as duplicate."""
        # Arrange
        today = date(2024, 6, 1)
        mock_date.today.return_value = today

        existing_source = Source(SourceName.wos, "https://wos.example.com/wos_user")
        existing = _make_existing_metric(researcher_id, existing_source, today)

        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = [existing]

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 0
        assert any("WoS" in r for r in result.skipped_reasons)

    @pytest.mark.asyncio
    @patch("src.modules.normalization.service.normalization_service.date")
    async def test_metric_not_duplicate_when_different_date(
            self, mock_date, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock, researcher_id
    ):
        """A metric extracted on a different date to the existing one is not a duplicate."""
        # Arrange
        mock_date.today.return_value = date(2024, 6, 2)

        existing_source = Source(SourceName.scholar, "https://scholar.google.com")
        existing = _make_existing_metric(researcher_id, existing_source, date(2024, 6, 1))

        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = [existing]

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 1
        assert result.metrics[0].is_duplicate is False

    @pytest.mark.asyncio
    @patch("src.modules.normalization.service.normalization_service.date")
    async def test_metric_not_duplicate_when_different_source(
            self, mock_date, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock, researcher_id
    ):
        """Same date but different source does not trigger duplicate detection."""
        # Arrange
        today = date(2024, 6, 1)
        mock_date.today.return_value = today

        existing_source = Source(SourceName.wos, "https://wos.example.com")
        existing = _make_existing_metric(researcher_id, existing_source, today)

        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = [existing]

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 1
        assert result.metrics[0].is_duplicate is False

    @pytest.mark.asyncio
    @patch("src.modules.normalization.service.normalization_service.date")
    async def test_duplicate_scholar_does_not_block_wos(
            self, mock_date, normalization_service, mock_repos, raw_result,
            raw_scholar, raw_wos, sample_profile_mock, researcher_id
    ):
        """A duplicate Scholar metric does not prevent a valid WoS metric from being added."""
        # Arrange
        today = date(2024, 6, 1)
        mock_date.today.return_value = today

        existing_source = Source(SourceName.scholar, "https://scholar.google.com/citations?user=scholar_abc")
        existing = _make_existing_metric(researcher_id, existing_source, today)

        raw_result.scholar = raw_scholar
        raw_result.wos = raw_wos
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = [existing]

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 1
        assert result.metrics[0].source.name == SourceName.wos
        assert any("Scholar" in r for r in result.skipped_reasons)

    @pytest.mark.asyncio
    async def test_no_existing_metrics_never_duplicate(
            self, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock
    ):
        """When there are no existing metrics at all, nothing can be a duplicate."""
        # Arrange
        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        result = await normalization_service.normalize(raw_result)

        # Assert
        assert len(result.metrics) == 1
        assert result.metrics[0].is_duplicate is False

    @pytest.mark.asyncio
    @patch("src.modules.normalization.service.normalization_service.date")
    async def test_duplicate_check_uses_researcher_profile_id_not_user_id(
            self, mock_date, normalization_service, mock_repos, raw_result, raw_scholar, sample_profile_mock
    ):
        """The duplicate check queries metrics by the profile's id, not the raw user_id string."""
        # Arrange
        mock_date.today.return_value = date(2024, 6, 1)
        raw_result.scholar = raw_scholar
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        await normalization_service.normalize(raw_result)

        # Assert
        mock_repos.metrics.get_by_researcher_id.assert_called_with(sample_profile_mock.id)


# =============================================================================
# normalize_all
# =============================================================================

class TestNormalizationServiceNormalizeAll:
    """Tests for normalize_all() batch processing."""

    @pytest.mark.asyncio
    async def test_normalize_all_processes_all_results(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """normalize_all processes every item in the input list."""
        # Arrange
        raw_2 = RawExtractionResult(
            user_id=str(uuid.uuid4()),
            run=raw_result.run,
        )
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        results = await normalization_service.normalize_all([raw_result, raw_2])

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_normalize_all_returns_normalization_result_instances(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """Each element returned is a NormalizationResult."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile_mock
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        results = await normalization_service.normalize_all([raw_result])

        # Assert
        assert all(isinstance(r, NormalizationResult) for r in results)

    @pytest.mark.asyncio
    async def test_normalize_all_continues_on_exception(
            self, normalization_service, mock_repos, raw_result, sample_profile_mock
    ):
        """An exception on one item does not abort processing of subsequent items."""
        # Arrange
        raw_good = RawExtractionResult(user_id=str(uuid.uuid4()), run=raw_result.run)

        call_count = 0

        async def get_by_user_id_side_effect(user_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated extraction error")
            return sample_profile_mock

        mock_repos.profiles.get_by_user_id.side_effect = get_by_user_id_side_effect
        mock_repos.metrics.get_by_researcher_id.return_value = []

        # Act
        results = await normalization_service.normalize_all([raw_result, raw_good])

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_normalize_all_failed_item_has_skipped_reason(
            self, normalization_service, mock_repos, raw_result
    ):
        """When an item raises an exception, its result contains a skipped_reason describing the error."""
        # Arrange
        mock_repos.profiles.get_by_user_id.side_effect = RuntimeError("boom")

        # Act
        results = await normalization_service.normalize_all([raw_result])

        # Assert
        assert len(results[0].skipped_reasons) > 0
        assert any("Normalization error" in r for r in results[0].skipped_reasons)

    @pytest.mark.asyncio
    async def test_normalize_all_empty_list_returns_empty(self, normalization_service, mock_repos):
        """Calling normalize_all with an empty list returns an empty list."""
        # Act
        results = await normalization_service.normalize_all([])

        # Assert
        assert results == []

