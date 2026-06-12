import uuid
from datetime import datetime, timezone
import pytest

from unittest.mock import AsyncMock, MagicMock
from starlette import status
from fastapi import HTTPException

from src.modules.researcher_metric.service.researcher_metric_service import ResearcherMetricService
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName
from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import (
    ResearcherMetricCreate, ResearcherMetricResponse, ResearcherMetricUpdate
)
from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import ResearcherProfile
from src.core.domain.user.user_model.user_model import User
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse
from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import (
    ExtractionRun, ExtractionStatus, ExtractionTrigger
)
from src.core.domain.user.user_model.user_role import UserRole

from src.core.domain.researcher_metric.researcher_model_schema.source_schemas import SourceModel, \
    SourceNameModel


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
def metric_service(mock_repos):
    """Cria uma instância do ResearcherMetricService com mocks."""
    return ResearcherMetricService(_repos=mock_repos)


@pytest.fixture
def sample_profile_id():
    """Gera um UUID para o perfil."""
    return uuid.uuid4()


@pytest.fixture
def sample_metric_id():
    """Gera um UUID para a métrica."""
    return uuid.uuid4()


@pytest.fixture
def sample_profile_data(sample_profile_id):
    """Cria dados de exemplo para um perfil de pesquisador."""
    return {
        'id': sample_profile_id,
        'keywords': ['machine learning', 'AI'],
        'metrics': [],
        'scholar_id': 'scholar_123',
        'orcid': '0000-0001-2345-6789',
        'wos_id': None,
        'scopus_id': None,
        'biography': None,
        'affiliation': None
    }


@pytest.fixture
def sample_metric_data(sample_metric_id, sample_profile_id):
    """Cria dados de exemplo para uma métrica de pesquisador."""
    return {
        'id': sample_metric_id,
        'researcher_id': sample_profile_id,
        'extraction_run_id': uuid.uuid4(),
        'source': Source(SourceName.scholar, url='https://scholar.google.com'),
        'date': datetime.now(timezone.utc),
        'h_index': 15,
        'total_citations': 500,
        'total_publications': 30,
        'i10_index': 10,
        'i10_index_5y': 8,
        'h_index_5y': 10,
        'citations_5y': 200,
        'cites_per_year': {'2022': 50, '2023': 75},
        'publications': []
    }




# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scholar_source() -> SourceModel:
    return SourceModel(name=SourceNameModel.scholar, url="https://scholar.google.com")


def _make_metric_create(
        researcher_id: uuid.UUID,
        extraction_run_id: uuid.UUID | None = None,
        *,
        h_index: int = 10,
        total_citations: int = 200,
        total_publications: int = 20,
        **kwargs,
) -> ResearcherMetricCreate:
    return ResearcherMetricCreate(
        researcher_id=researcher_id,
        extraction_run_id=extraction_run_id,
        source=_scholar_source(),
        h_index=h_index,
        total_citations=total_citations,
        total_publications=total_publications,
        **kwargs,
    )


# =============================================================================
# create_metric
# =============================================================================

class TestResearcherMetricServiceCreate:
    """Tests for metric creation via ResearcherMetricService.create_metric."""

    # -------------------------------------------------------------------------
    # Profile lookup — primary path (by user id)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_metric_required_fields_only(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """Creating a metric with only the required fields succeeds."""
        # Arrange
        metric_data = _make_metric_create(researcher_id=profile_id)
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        mock_repos.profiles.get_by_id.return_value = None

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        assert result.h_index == 10
        assert result.total_citations == 200
        assert result.total_publications == 20

        assert result.i10_index is None
        assert result.h_index_5y is None
        assert result.i10_index_5y is None
        assert result.citations_5y is None
        assert result.cites_per_year is None
        assert result.publications == []

    @pytest.mark.asyncio
    async def test_create_metric_with_scholar_optional_fields(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """Creating a metric with Scholar-specific optional fields stores them correctly."""
        # Arrange
        metric_data = _make_metric_create(
            researcher_id=profile_id,
            i10_index=5,
            i10_index_5y=3,
            h_index_5y=8,
            citations_5y=100,
            cites_per_year={"2022": 40, "2023": 60},
        )
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        mock_repos.profiles.get_by_id.return_value = None

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        assert result.i10_index == 5
        assert result.i10_index_5y == 3
        assert result.h_index_5y == 8
        assert result.citations_5y == 100
        assert result.cites_per_year == {"2022": 40, "2023": 60}

    @pytest.mark.asyncio
    async def test_create_metric_all_fields(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """Creating a metric with every field populated succeeds."""
        # Arrange
        metric_data = _make_metric_create(
            researcher_id=profile_id,
            i10_index=12,
            i10_index_5y=8,
            h_index_5y=9,
            citations_5y=150,
            cites_per_year={"2021": 30, "2022": 55, "2023": 65},
            publications=[{"title": "Paper A", "times_cited": 10}],
        )
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        mock_repos.profiles.get_by_id.return_value = None

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        assert result.h_index == 10
        assert result.i10_index == 12
        assert result.citations_5y == 150
        assert result.cites_per_year == {"2021": 30, "2022": 55, "2023": 65}

    @pytest.mark.asyncio
    async def test_create_metric_generates_unique_ids(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """Each created metric receives a distinct UUID."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile

        # Act
        result_1 = await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))
        result_2 = await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))

        # Assert
        assert result_1.id != result_2.id

    @pytest.mark.asyncio
    async def test_create_metric_date_is_set_automatically(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """A metric creation date is assigned automatically and is timezone-aware."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        before = datetime.now(timezone.utc)

        # Act
        result = await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))

        # Assert
        after = datetime.now(timezone.utc)
        assert before <= result.date <= after

    # -------------------------------------------------------------------------
    # Metric linked to researcher profile
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_metric_is_appended_to_profile(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """After creation the metric is appended to the profile's metrics list."""
        # Arrange
        sample_profile.metrics = []
        mock_repos.profiles.get_by_user_id.return_value = sample_profile

        # Act
        await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))

        # Assert
        assert len(sample_profile.metrics) == 1

    @pytest.mark.asyncio
    async def test_create_metric_profile_saved_after_append(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """The profile is saved after the metric is appended to it."""
        # Arrange
        sample_profile.metrics = []
        mock_repos.profiles.get_by_user_id.return_value = sample_profile

        # Act
        await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))

        # Assert
        mock_repos.profiles.save.assert_called_with(sample_profile)

    @pytest.mark.asyncio
    async def test_create_metric_researcher_id_matches_profile(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """The metric's researcher_id is the profile's id, not the user id passed in."""
        # Arrange
        sample_profile.metrics = []
        mock_repos.profiles.get_by_user_id.return_value = sample_profile

        # Act
        result = await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))

        # Assert
        assert result.researcher_id == sample_profile.id

    # -------------------------------------------------------------------------
    # Extraction run auto-creation
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_metric_without_extraction_run_id_creates_run(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """When no extraction_run_id is supplied, a new ExtractionRun is created and saved."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        metric_data = _make_metric_create(researcher_id=profile_id, extraction_run_id=None)

        # Act
        await metric_service.create_metric(metric_data)

        # Assert
        mock_repos.extraction_runs.save.assert_called_once()
        saved_run = mock_repos.extraction_runs.save.call_args.args[0]
        assert isinstance(saved_run, ExtractionRun)
        assert saved_run.triggered_by == ExtractionTrigger.created_by_admin
        assert saved_run.status == ExtractionStatus.completed
        assert saved_run.researcher_id == sample_profile.id

    @pytest.mark.asyncio
    async def test_create_metric_with_existing_extraction_run_id_skips_run_creation(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """When an extraction_run_id is provided, no new ExtractionRun is created."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        existing_run_id = uuid.uuid4()
        metric_data = _make_metric_create(researcher_id=profile_id, extraction_run_id=existing_run_id)

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        mock_repos.extraction_runs.save.assert_not_called()
        assert result.extraction_run_id == existing_run_id

    @pytest.mark.asyncio
    async def test_create_metric_auto_run_id_is_used_on_metric(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """The metric's extraction_run_id matches the auto-created ExtractionRun's id."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        metric_data = _make_metric_create(researcher_id=profile_id, extraction_run_id=None)

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        saved_run = mock_repos.extraction_runs.save.call_args.args[0]
        assert result.extraction_run_id == saved_run.id

    # -------------------------------------------------------------------------
    # Retry mechanism (profile not found by user id, retried by profile id)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_metric_retries_with_profile_id_when_user_lookup_fails(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """When get_by_user_id returns None, the service retries with get_by_id."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = None
        mock_repos.profiles.get_by_id.return_value = sample_profile
        metric_data = _make_metric_create(researcher_id=profile_id)

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        mock_repos.profiles.get_by_id.assert_called_once_with(profile_id)
        assert result.researcher_id == sample_profile.id

    @pytest.mark.asyncio
    async def test_create_metric_raises_404_when_both_lookups_fail(
            self, metric_service, mock_repos, profile_id
    ):
        """When both get_by_user_id and get_by_id return None, HTTP 404 is raised."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = None
        mock_repos.profiles.get_by_id.return_value = None
        metric_data = _make_metric_create(researcher_id=profile_id)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await metric_service.create_metric(metric_data)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        mock_repos.metrics.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_metric_primary_lookup_called_with_researcher_id(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """The primary profile lookup uses the researcher_id provided in the request."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        metric_data = _make_metric_create(researcher_id=profile_id)

        # Act
        await metric_service.create_metric(metric_data)

        # Assert
        mock_repos.profiles.get_by_user_id.assert_called_once_with(profile_id)

    # -------------------------------------------------------------------------
    # Source
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_metric_source_is_stored_correctly(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """The source name and URL provided are stored on the created metric."""
        # Arrange
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        metric_data = _make_metric_create(researcher_id=profile_id)
        metric_data.source = SourceModel(name=SourceNameModel.scopus, url="https://scopus.com/abc")

        # Act
        result = await metric_service.create_metric(metric_data)

        # Assert
        assert result.source.name == SourceNameModel.scopus
        assert result.source.url == "https://scopus.com/abc"

    # -------------------------------------------------------------------------
    # Persistence order
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_metric_commit_called_after_profile_save(
            self, metric_service, mock_repos, sample_profile, profile_id
    ):
        """The final commit happens after the profile (with appended metric) is saved."""
        # Arrange
        call_order = []
        mock_repos.profiles.get_by_user_id.return_value = sample_profile
        mock_repos.profiles.save.side_effect = lambda _: call_order.append("profile_save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await metric_service.create_metric(_make_metric_create(researcher_id=profile_id))

        # Assert — last two calls must be profile_save then commit
        assert call_order[-2:] == ["profile_save", "commit"]


# =============================================================================
# delete_metric
# =============================================================================

class TestResearcherMetricServiceDelete:
    """Tests for metric deletion via ResearcherMetricService.delete_metric."""

    @pytest.mark.asyncio
    async def test_delete_metric_success(self, metric_service, mock_repos, sample_metric, sample_profile):
        """Deleting an existing metric succeeds."""
        # Arrange
        sample_profile.metrics = [sample_metric]
        mock_repos.metrics.get_by_id.return_value = sample_metric
        mock_repos.profiles.get_by_id.return_value = sample_profile

        # Act
        await metric_service.delete_metric(sample_metric.id)

        # Assert
        mock_repos.metrics.delete.assert_called_once_with(sample_metric.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_metric_removes_it_from_profile_metrics_list(
            self, metric_service, mock_repos, sample_metric, sample_profile
    ):
        """After deletion the metric is no longer present in the profile's metrics list."""
        # Arrange
        sample_profile.metrics = [sample_metric]
        mock_repos.metrics.get_by_id.return_value = sample_metric
        mock_repos.profiles.get_by_id.return_value = sample_profile

        # Act
        await metric_service.delete_metric(sample_metric.id)

        # Assert
        assert sample_metric not in sample_profile.metrics
        mock_repos.profiles.save.assert_called_once_with(sample_profile)

    @pytest.mark.asyncio
    async def test_delete_metric_profile_not_found_still_deletes_metric(
            self, metric_service, mock_repos, sample_metric
    ):
        """If the linked profile cannot be found, the metric is still deleted."""
        # Arrange
        mock_repos.metrics.get_by_id.return_value = sample_metric
        mock_repos.profiles.get_by_id.return_value = None

        # Act
        await metric_service.delete_metric(sample_metric.id)

        # Assert
        mock_repos.metrics.delete.assert_called_once_with(sample_metric.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_metric_not_found_raises_404(self, metric_service, mock_repos):
        """Attempting to delete a non-existent metric raises HTTP 404."""
        # Arrange
        mock_repos.metrics.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await metric_service.delete_metric(uuid.uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Metric not found" in exc_info.value.detail
        mock_repos.metrics.delete.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_metric_delete_called_before_commit(
            self, metric_service, mock_repos, sample_metric, sample_profile
    ):
        """metrics.delete() is called before commit()."""
        # Arrange
        call_order = []
        sample_profile.metrics = [sample_metric]
        mock_repos.metrics.get_by_id.return_value = sample_metric
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.metrics.delete.side_effect = lambda _: call_order.append("delete")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await metric_service.delete_metric(sample_metric.id)

        # Assert
        assert call_order == ["delete", "commit"]


# =============================================================================
# update_metric
# =============================================================================

class TestResearcherMetricServiceUpdate:
    """Tests for metric updates via ResearcherMetricService.update_metric."""

    @pytest.mark.asyncio
    async def test_update_metric_h_index_success(self, metric_service, mock_repos, sample_metric):
        """Updating h_index on an existing metric succeeds."""
        # Arrange
        mock_repos.metrics.get_by_id.return_value = sample_metric
        update = ResearcherMetricUpdate(h_index=99)

        # Act
        result = await metric_service.update_metric(sample_metric.id, update)

        # Assert
        assert result.h_index == 99
        mock_repos.metrics.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_metric_total_citations_success(self, metric_service, mock_repos, sample_metric):
        """Updating total_citations on an existing metric succeeds."""
        # Arrange
        mock_repos.metrics.get_by_id.return_value = sample_metric
        update = ResearcherMetricUpdate(total_citations=9999)

        # Act
        result = await metric_service.update_metric(sample_metric.id, update)

        # Assert
        assert result.total_citations == 9999

    @pytest.mark.asyncio
    async def test_update_metric_multiple_fields(self, metric_service, mock_repos, sample_metric):
        """Multiple fields can be updated in a single call."""
        # Arrange
        mock_repos.metrics.get_by_id.return_value = sample_metric
        update = ResearcherMetricUpdate(h_index=20, total_citations=800, total_publications=40, i10_index=15)

        # Act
        result = await metric_service.update_metric(sample_metric.id, update)

        # Assert
        assert result.h_index == 20
        assert result.total_citations == 800
        assert result.total_publications == 40
        assert result.i10_index == 15

    @pytest.mark.asyncio
    async def test_update_metric_not_found_raises_404(self, metric_service, mock_repos):
        """Attempting to update a non-existent metric raises HTTP 404."""
        # Arrange
        mock_repos.metrics.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await metric_service.update_metric(uuid.uuid4(), ResearcherMetricUpdate(h_index=1))

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Metric not found" in exc_info.value.detail
        mock_repos.metrics.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_metric_save_called_before_commit(self, metric_service, mock_repos, sample_metric):
        """save() is called before commit() during an update."""
        # Arrange
        call_order = []
        mock_repos.metrics.get_by_id.return_value = sample_metric
        mock_repos.metrics.save.side_effect = lambda _: call_order.append("save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await metric_service.update_metric(sample_metric.id, ResearcherMetricUpdate(h_index=5))

        # Assert
        assert call_order == ["save", "commit"]


# =============================================================================
# fetch_metrics
# =============================================================================

class TestResearcherMetricServiceFetch:
    """Tests for paginated metric listing via ResearcherMetricService.fetch_metrics."""

    @pytest.mark.asyncio
    async def test_fetch_metrics_returns_correct_items(
            self, metric_service, mock_repos, sample_metric, pagination_params
    ):
        """The items in the response correspond to the metrics returned by the repository."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_metric]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics(pagination_params)

        # Assert
        assert len(result.items) == 1
        assert result.items[0].id == sample_metric.id

    @pytest.mark.asyncio
    async def test_fetch_metrics_returns_correct_pagination_metadata(
            self, metric_service, mock_repos, sample_metric, pagination_params
    ):
        """total, page, page_size, and pages are forwarded accurately."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_metric]
        raw_result.total = 77
        raw_result.page = 4
        raw_result.page_size = 10
        raw_result.pages = 8
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics(pagination_params)

        # Assert
        assert result.total == 77
        assert result.page == 4
        assert result.page_size == 10
        assert result.pages == 8

    @pytest.mark.asyncio
    async def test_fetch_metrics_empty_list(self, metric_service, mock_repos, pagination_params):
        """When there are no metrics, items is empty and total is 0."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics(pagination_params)

        # Assert
        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_fetch_metrics_returns_paginated_response_type(
            self, metric_service, mock_repos, pagination_params
    ):
        """The return type is PaginatedResponse."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics(pagination_params)

        # Assert
        assert isinstance(result, PaginatedResponse)

    @pytest.mark.asyncio
    async def test_fetch_metrics_items_are_validated_responses(
            self, metric_service, mock_repos, sample_metric, pagination_params
    ):
        """Each item is a validated ResearcherMetricResponse, not a raw domain object."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_metric]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics(pagination_params)

        # Assert
        assert all(isinstance(item, ResearcherMetricResponse) for item in result.items)

    @pytest.mark.asyncio
    async def test_fetch_metrics_passes_pagination_params_to_repo(
            self, metric_service, mock_repos, pagination_params
    ):
        """The pagination params are forwarded to the repository unchanged."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        await metric_service.fetch_metrics(pagination_params)

        # Assert
        mock_repos.metrics.fetch.assert_called_once_with(pagination_params)


# =============================================================================
# fetch_metrics_by_user
# =============================================================================

class TestResearcherMetricServiceFetchByUser:
    """Tests for per-user metric listing via ResearcherMetricService.fetch_metrics_by_user."""

    # -------------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_returns_items_for_correct_user(
            self, metric_service, mock_repos, sample_user, sample_profile, sample_metric, pagination_params
    ):
        """Metrics returned belong to the requested user's profile."""
        # Arrange
        sample_profile.metrics = [sample_metric]
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        raw_result = MagicMock()
        raw_result.items = [sample_metric]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics_by_user(sample_user.id, pagination_params)

        # Assert
        assert len(result.items) == 1
        assert result.items[0].id == sample_metric.id

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_passes_profile_id_filter_to_repo(
            self, metric_service, mock_repos, sample_user, sample_profile, pagination_params
    ):
        """The repository fetch receives an extra filter scoped to the user's profile id."""
        # Arrange
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        await metric_service.fetch_metrics_by_user(sample_user.id, pagination_params)

        # Assert — fetch must have been called with extra_filters
        call_kwargs = mock_repos.metrics.fetch.call_args.kwargs
        assert "extra_filters" in call_kwargs
        assert len(call_kwargs["extra_filters"]) == 1

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_returns_paginated_response_type(
            self, metric_service, mock_repos, sample_user, sample_profile, pagination_params
    ):
        """The return type is PaginatedResponse."""
        # Arrange
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics_by_user(sample_user.id, pagination_params)

        # Assert
        assert isinstance(result, PaginatedResponse)

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_empty_when_no_metrics(
            self, metric_service, mock_repos, sample_user, sample_profile, pagination_params
    ):
        """A user with a profile but no metrics returns an empty list."""
        # Arrange
        sample_profile.metrics = []
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics_by_user(sample_user.id, pagination_params)

        # Assert
        assert result.items == []
        assert result.total == 0

    # -------------------------------------------------------------------------
    # Error cases
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_user_not_found_raises_404(
            self, metric_service, mock_repos, pagination_params
    ):
        """Fetching metrics for a non-existent user raises HTTP 404."""
        # Arrange
        mock_repos.users.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await metric_service.fetch_metrics_by_user(uuid.uuid4(), pagination_params)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail
        mock_repos.metrics.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_user_without_profile_raises_404(
            self, metric_service, mock_repos, sample_user, pagination_params
    ):
        """Fetching metrics for a user with no researcherProfile raises HTTP 404."""
        # Arrange
        sample_user.researcherProfile = None
        mock_repos.users.get_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await metric_service.fetch_metrics_by_user(sample_user.id, pagination_params)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "ResearcherProfile not found" in exc_info.value.detail
        mock_repos.metrics.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_metrics_by_user_items_are_validated_responses(
            self, metric_service, mock_repos, sample_user, sample_profile, sample_metric, pagination_params
    ):
        """Each item is a validated ResearcherMetricResponse, not a raw domain object."""
        # Arrange
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        raw_result = MagicMock()
        raw_result.items = [sample_metric]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.metrics.fetch.return_value = raw_result

        # Act
        result = await metric_service.fetch_metrics_by_user(sample_user.id, pagination_params)

        # Assert
        assert all(isinstance(item, ResearcherMetricResponse) for item in result.items)


# =============================================================================
# fetch_latest_by_user
# =============================================================================

class TestResearcherMetricServiceFetchLatestByUser:
    """Tests for fetch_latest_by_user via ResearcherMetricService."""

    @pytest.mark.asyncio
    async def test_fetch_latest_by_user_delegates_to_repo(
            self, metric_service, mock_repos, pagination_params
    ):
        """fetch_latest_by_user forwards source and params directly to the repository."""
        # Arrange
        expected = MagicMock()
        mock_repos.metrics.fetch_latest_by_user.return_value = expected

        # Act
        result = await metric_service.fetch_latest_by_user(source="scholar", params=pagination_params)

        # Assert
        mock_repos.metrics.fetch_latest_by_user.assert_called_once_with("scholar", pagination_params)
        assert result == expected

    @pytest.mark.asyncio
    async def test_fetch_latest_by_user_no_source_filter(
            self, metric_service, mock_repos, pagination_params
    ):
        """When source is None, it is passed as None to the repository."""
        # Arrange
        mock_repos.metrics.fetch_latest_by_user.return_value = MagicMock()

        # Act
        await metric_service.fetch_latest_by_user(source=None, params=pagination_params)

        # Assert
        mock_repos.metrics.fetch_latest_by_user.assert_called_once_with(None, pagination_params)

    @pytest.mark.asyncio
    async def test_fetch_latest_by_user_with_scholar_source(
            self, metric_service, mock_repos, sample_metric, pagination_params
    ):
        """Filtering by scholar source returns only scholar metrics."""
        # Arrange
        raw = MagicMock()
        raw.items = [sample_metric]
        raw.total = 1
        raw.page = 1
        raw.page_size = 20
        raw.pages = 1
        mock_repos.metrics.fetch_latest_by_user.return_value = raw

        # Act
        result = await metric_service.fetch_latest_by_user(source="scholar", params=pagination_params)

        # Assert
        mock_repos.metrics.fetch_latest_by_user.assert_called_once_with("scholar", pagination_params)

    @pytest.mark.asyncio
    async def test_fetch_latest_by_user_with_scopus_source(
            self, metric_service, mock_repos, metric_data, pagination_params
    ):
        """Filtering by scopus source forwards the correct source string."""
        # Arrange
        scopus_metric = ResearcherMetric(
            **{
                **metric_data,
                "id": uuid.uuid4(),
                "source": Source(SourceName.scopus, url="https://scopus.com"),
            }
        )
        raw = MagicMock()
        raw.items = [scopus_metric]
        raw.total = 1
        raw.page = 1
        raw.page_size = 20
        raw.pages = 1
        mock_repos.metrics.fetch_latest_by_user.return_value = raw

        # Act
        await metric_service.fetch_latest_by_user(source="scopus", params=pagination_params)

        # Assert
        mock_repos.metrics.fetch_latest_by_user.assert_called_once_with("scopus", pagination_params)

    @pytest.mark.asyncio
    async def test_fetch_latest_by_user_default_params(self, metric_service, mock_repos):
        """fetch_latest_by_user can be called with default (None) params."""
        # Arrange
        mock_repos.metrics.fetch_latest_by_user.return_value = MagicMock()

        # Act
        await metric_service.fetch_latest_by_user()

        # Assert
        mock_repos.metrics.fetch_latest_by_user.assert_called_once_with(None, None)