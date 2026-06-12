import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import (
    ExtractionRun,
    ExtractionStatus,
    ExtractionTrigger,
)
from src.core.domain.extraction_run.extractiuon_run_schema.extraction_run_schemas import (
    ExtractionRunCreate,
    ExtractionRunResponse,
)
from src.core.domain.researcher_metric.researcher_metric_model.source_model import SourceName



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
def extraction_run_service(mock_repos):
    from src.modules.extraction.service.extraction_run_service import ExtractionRunService
    return ExtractionRunService(mock_repos)


@pytest.fixture
def researcher_id():
    return uuid.uuid4()


@pytest.fixture
def run_create(researcher_id):
    return ExtractionRunCreate(
        researcher_id=researcher_id,
        triggered_at=datetime.now(timezone.utc),
        triggered_by=ExtractionTrigger.created_by_admin,
        status=ExtractionStatus.completed,
        sources_attempted=[SourceName.scholar],
        sources_succeeded=[SourceName.scholar],
    )


# =============================================================================
# create_run
# =============================================================================

class TestExtractionRunServiceCreate:
    """Tests for ExtractionRunService.create_run."""

    # -------------------------------------------------------------------------
    # Success — field mapping
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_run_returns_response(self, extraction_run_service, mock_repos, run_create):
        """create_run returns an ExtractionRunResponse on success."""
        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert isinstance(result, ExtractionRunResponse)

    @pytest.mark.asyncio
    async def test_create_run_fields_match_input(self, extraction_run_service, mock_repos, run_create):
        """All fields from ExtractionRunCreate are present on the returned response."""
        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert result.researcher_id == run_create.researcher_id
        assert result.triggered_by == run_create.triggered_by
        assert result.status == run_create.status
        assert result.sources_attempted == run_create.sources_attempted
        assert result.sources_succeeded == run_create.sources_succeeded

    @pytest.mark.asyncio
    async def test_create_run_generates_uuid(self, extraction_run_service, mock_repos, run_create):
        """The created run receives a UUID id."""
        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert isinstance(result.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_create_run_generates_unique_ids(self, extraction_run_service, mock_repos, run_create):
        """Each call to create_run produces a distinct UUID."""
        # Act
        result_1 = await extraction_run_service.create_run(run_create)
        result_2 = await extraction_run_service.create_run(run_create)

        # Assert
        assert result_1.id != result_2.id

    @pytest.mark.asyncio
    async def test_create_run_triggered_at_is_set(self, extraction_run_service, mock_repos, run_create):
        """The triggered_at timestamp on the response is a datetime."""
        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert isinstance(result.triggered_at, datetime)

    # -------------------------------------------------------------------------
    # Success — all trigger and status variants
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    @pytest.mark.parametrize("trigger", list(ExtractionTrigger))
    async def test_create_run_all_trigger_types(
            self, extraction_run_service, mock_repos, run_create, trigger
    ):
        """create_run succeeds for every ExtractionTrigger value."""
        # Arrange
        run_create.triggered_by = trigger

        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert result.triggered_by == trigger

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", list(ExtractionStatus))
    async def test_create_run_all_status_values(
            self, extraction_run_service, mock_repos, run_create, status
    ):
        """create_run succeeds for every ExtractionStatus value."""
        # Arrange
        run_create.status = status

        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert result.status == status

    # -------------------------------------------------------------------------
    # Success — sources edge cases
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_run_empty_sources(self, extraction_run_service, mock_repos, run_create):
        """A run can be created with no sources attempted or succeeded."""
        # Arrange
        run_create.sources_attempted = []
        run_create.sources_succeeded = []

        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert result.sources_attempted == []
        assert result.sources_succeeded == []

    @pytest.mark.asyncio
    async def test_create_run_multiple_sources(self, extraction_run_service, mock_repos, run_create):
        """A run can be created with multiple sources."""
        # Arrange
        run_create.sources_attempted = [SourceName.scholar, SourceName.wos, SourceName.scopus]
        run_create.sources_succeeded = [SourceName.scholar, SourceName.scopus]

        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert SourceName.scholar in result.sources_attempted
        assert SourceName.wos in result.sources_attempted
        assert SourceName.scopus in result.sources_succeeded
        assert SourceName.wos not in result.sources_succeeded

    @pytest.mark.asyncio
    async def test_create_run_succeeded_subset_of_attempted(
            self, extraction_run_service, mock_repos, run_create
    ):
        """sources_succeeded can be a strict subset of sources_attempted (partial run)."""
        # Arrange
        run_create.sources_attempted = [SourceName.scholar, SourceName.wos]
        run_create.sources_succeeded = [SourceName.scholar]
        run_create.status = ExtractionStatus.partial

        # Act
        result = await extraction_run_service.create_run(run_create)

        # Assert
        assert result.status == ExtractionStatus.partial
        assert len(result.sources_succeeded) < len(result.sources_attempted)

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_run_save_is_called(self, extraction_run_service, mock_repos, run_create):
        """extraction_runs.save() is called exactly once."""
        # Act
        await extraction_run_service.create_run(run_create)

        # Assert
        mock_repos.extraction_runs.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_run_commit_is_called(self, extraction_run_service, mock_repos, run_create):
        """commit() is called exactly once after save."""
        # Act
        await extraction_run_service.create_run(run_create)

        # Assert
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_run_save_called_before_commit(
            self, extraction_run_service, mock_repos, run_create
    ):
        """save() is called before commit()."""
        # Arrange
        call_order = []
        mock_repos.extraction_runs.save.side_effect = lambda _: call_order.append("save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await extraction_run_service.create_run(run_create)

        # Assert
        assert call_order == ["save", "commit"]

    @pytest.mark.asyncio
    async def test_create_run_saved_object_is_extraction_run(
            self, extraction_run_service, mock_repos, run_create
    ):
        """The object passed to save() is an ExtractionRun domain object."""
        # Act
        await extraction_run_service.create_run(run_create)

        # Assert
        saved = mock_repos.extraction_runs.save.call_args.args[0]
        assert isinstance(saved, ExtractionRun)

    # -------------------------------------------------------------------------
    # External repos parameter
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_run_accepts_external_repos(
            self, extraction_run_service, mock_repos, run_create
    ):
        """When an external repos is passed, create_run uses it instead of opening a new context."""
        # Act
        result = await extraction_run_service.create_run(run_create, repos=mock_repos)

        # Assert
        assert isinstance(result, ExtractionRunResponse)
        mock_repos.extraction_runs.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_run_external_repos_does_not_open_context_manager(
            self, extraction_run_service, mock_repos, run_create
    ):
        """When repos is provided externally, the service's own context manager is never entered."""
        # Act
        await extraction_run_service.create_run(run_create, repos=mock_repos)

        # Assert — __aenter__ should not have been called
        mock_repos.__aenter__.assert_not_called()