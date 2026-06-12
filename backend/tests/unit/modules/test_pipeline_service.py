import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette import status

from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import (
    ExtractionRun,
    ExtractionStatus,
    ExtractionTrigger,
)
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName
from src.core.domain.researcher_metric.researcher_model_schema.researcher_metric_schemas import (
    ResearcherMetricResponse,
)
from src.core.domain.researcher_metric.researcher_model_schema.source_schemas import SourceModel, SourceNameModel
from src.modules.extraction.service.pipeline_service import ExtractionPipelineResult
from src.modules.normalization.models.metric.normalized_metric import NormalizedMetric
from src.modules.normalization.models.profile.normalized_researcher_profile import NormalizedProfile
from src.modules.normalization.models.result.normalization_result import (
    NormalizationResult,
    RawExtractionResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def profile_id():
    return uuid.uuid4()


@pytest.fixture
def extraction_run(profile_id):
    return ExtractionRun(
        id=uuid.uuid4(),
        researcher_id=profile_id,
        triggered_at=datetime.now(timezone.utc),
        triggered_by=ExtractionTrigger.manual,
        status=ExtractionStatus.completed,
        sources_attempted=[SourceName.scholar],
        sources_succeeded=[SourceName.scholar],
    )


@pytest.fixture
def mock_extraction_service():
    return AsyncMock()


@pytest.fixture
def mock_normalization_service():
    return AsyncMock()


@pytest.fixture
def mock_metric_service():
    return AsyncMock()


@pytest.fixture
def mock_run_service():
    return AsyncMock()


@pytest.fixture
def pipeline_service(
        mock_repos,
        mock_extraction_service,
        mock_normalization_service,
        mock_metric_service,
        mock_run_service,
):
    from src.modules.extraction.service.pipeline_service import PipelineService
    return PipelineService(
        repos=mock_repos,
        extraction_service=mock_extraction_service,
        normalization_service=mock_normalization_service,
        metric_service=mock_metric_service,
        run_service=mock_run_service,
    )


def _make_raw_result(user_id: uuid.UUID, run: ExtractionRun, errors: list[str] = None) -> RawExtractionResult:
    return RawExtractionResult(
        user_id=str(user_id),
        run=run,
        errors=errors or [],
    )


def _make_normalized_result(
        user_id: uuid.UUID,
        run: ExtractionRun,
        metrics: list[NormalizedMetric] = None,
        profile_update: NormalizedProfile = None,
        skipped_reasons: list[str] = None,
) -> NormalizationResult:
    result = NormalizationResult(user_id=str(user_id), run=run)
    result.metrics = metrics or []
    result.profile_update = profile_update
    result.skipped_reasons = skipped_reasons or []
    return result


def _make_normalized_metric(
        researcher_id: uuid.UUID,
        is_duplicate: bool = False,
) -> NormalizedMetric:
    return NormalizedMetric(
        researcher_id=researcher_id,
        source=Source(SourceName.scholar, "https://scholar.google.com"),
        h_index=10,
        total_citations=200,
        total_publications=20,
        is_duplicate=is_duplicate,
    )


def _make_created_metric_response(researcher_id: uuid.UUID, run_id: uuid.UUID) -> ResearcherMetricResponse:
    return ResearcherMetricResponse(
        id=uuid.uuid4(),
        researcher_id=researcher_id,
        extraction_run_id=run_id,
        source=SourceModel(name=SourceNameModel.scholar, url="https://scholar.google.com"),
        date=datetime.now(timezone.utc),
        h_index=10,
        total_citations=200,
        total_publications=20,
    )


def _make_run_response(run: ExtractionRun):
    r = MagicMock()
    r.id = run.id
    return r


# =============================================================================
# run_for_user — extraction failures
# =============================================================================

class TestPipelineServiceRunForUserExtraction:
    """Tests for extraction-stage behaviour in run_for_user."""

    @pytest.mark.asyncio
    async def test_run_for_user_raises_404_when_user_not_found(
            self, pipeline_service, mock_extraction_service, user_id
    ):
        """A ValueError from the extraction service is converted to HTTP 404."""
        # Arrange
        mock_extraction_service.extract_for_user.side_effect = ValueError("User not found")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await pipeline_service.run_for_user(user_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_run_for_user_extraction_errors_forwarded_to_result(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """Errors from the raw extraction result are forwarded onto the pipeline result."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run, errors=["Scholar: no results"])
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run)
        mock_normalization_service.normalize.return_value = normalized

        run_response = _make_run_response(extraction_run)
        mock_run_service.create_run.return_value = run_response

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert "Scholar: no results" in result.errors

    @pytest.mark.asyncio
    async def test_run_for_user_no_extraction_errors_result_errors_empty(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """When extraction produces no errors, pipeline_result.errors starts empty."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run)
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.errors == []


# =============================================================================
# run_for_user — metric creation
# =============================================================================

class TestPipelineServiceRunForUserMetricCreation:
    """Tests for the metric persistence stage of run_for_user."""

    @pytest.mark.asyncio
    async def test_run_for_user_creates_metric_when_not_duplicate(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            mock_metric_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """A non-duplicate metric is created and metric_created is set to True."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        metric = _make_normalized_metric(profile_id, is_duplicate=False)
        normalized = _make_normalized_result(user_id, extraction_run, metrics=[metric])
        mock_normalization_service.normalize.return_value = normalized

        run_response = _make_run_response(extraction_run)
        mock_run_service.create_run.return_value = run_response

        created = _make_created_metric_response(profile_id, extraction_run.id)
        mock_metric_service.create_metric.return_value = created

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.metric_created is True
        mock_metric_service.create_metric.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_for_user_skips_duplicate_metric(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            mock_metric_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """A duplicate metric is not persisted and metric_created remains False."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        metric = _make_normalized_metric(profile_id, is_duplicate=True)
        normalized = _make_normalized_result(user_id, extraction_run, metrics=[metric])
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.metric_created is False
        mock_metric_service.create_metric.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_for_user_metric_created_false_when_no_metrics(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
    mock_metric_service):
        """When normalization produces no metrics, metric_created remains False."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run, metrics=[])
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.metric_created is False
        mock_metric_service.create_metric.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_for_user_multiple_metrics_all_created(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            mock_metric_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """All non-duplicate metrics in a single run are created."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        metrics = [
            _make_normalized_metric(profile_id, is_duplicate=False),
            _make_normalized_metric(profile_id, is_duplicate=False),
        ]
        normalized = _make_normalized_result(user_id, extraction_run, metrics=metrics)
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)
        mock_metric_service.create_metric.return_value = _make_created_metric_response(
            profile_id, extraction_run.id
        )

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert mock_metric_service.create_metric.call_count == 2
        assert len(result.metrics) == 2

    @pytest.mark.asyncio
    async def test_run_for_user_mixed_duplicate_and_new_metrics(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            mock_metric_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """Only non-duplicate metrics are created when the list contains both."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        metrics = [
            _make_normalized_metric(profile_id, is_duplicate=False),
            _make_normalized_metric(profile_id, is_duplicate=True),
            _make_normalized_metric(profile_id, is_duplicate=False),
        ]
        normalized = _make_normalized_result(user_id, extraction_run, metrics=metrics)
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)
        mock_metric_service.create_metric.return_value = _make_created_metric_response(
            profile_id, extraction_run.id
        )

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert mock_metric_service.create_metric.call_count == 2

    @pytest.mark.asyncio
    async def test_run_for_user_metric_appended_to_pipeline_result(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            mock_metric_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """Each created metric is appended to pipeline_result.metrics."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        metric = _make_normalized_metric(profile_id, is_duplicate=False)
        normalized = _make_normalized_result(user_id, extraction_run, metrics=[metric])
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)
        mock_metric_service.create_metric.return_value = _make_created_metric_response(
            profile_id, extraction_run.id
        )

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert len(result.metrics) == 1
        assert isinstance(result.metrics[0], ResearcherMetricResponse)

    @pytest.mark.asyncio
    async def test_run_for_user_duplicate_skipped_reason_forwarded(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """Skipped reasons from normalization are forwarded onto the pipeline result."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(
            user_id, extraction_run,
            skipped_reasons=["Scholar metric from 2024-01-01 already exists."]
        )
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert any("already exists" in r for r in result.skipped_reasons)

    @pytest.mark.asyncio
    async def test_run_for_user_rollback_called_on_metric_creation_error(
            self,
            pipeline_service,
            mock_repos,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            mock_metric_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """When metric creation raises an exception, the transaction is rolled back."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        metric = _make_normalized_metric(profile_id, is_duplicate=False)
        normalized = _make_normalized_result(user_id, extraction_run, metrics=[metric])
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)
        mock_metric_service.create_metric.side_effect = Exception("DB error")

        # Act & Assert
        with pytest.raises(Exception, match="DB error"):
            await pipeline_service.run_for_user(user_id)

        mock_repos.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_for_user_extraction_run_created_via_run_service(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
    ):
        """The extraction run is persisted through the run service exactly once."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run)
        mock_normalization_service.normalize.return_value = normalized

        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        await pipeline_service.run_for_user(user_id)

        # Assert
        mock_run_service.create_run.assert_called_once()


# =============================================================================
# run_for_user — profile update
# =============================================================================

class TestPipelineServiceRunForUserProfileUpdate:
    """Tests for the profile update stage of run_for_user."""

    @pytest.mark.asyncio
    async def test_run_for_user_profile_updated_when_orcid_present(
            self,
            pipeline_service,
            mock_repos,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """When normalization includes a profile_update, profile_updated is set to True."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        profile_update = NormalizedProfile(
            researcher_id=profile_id,
            biography="Updated bio",
            keywords=["NLP"],
            orcid_id="0000-0001-2345-6789",
        )
        normalized = _make_normalized_result(
            user_id, extraction_run, profile_update=profile_update
        )
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        mock_profile = MagicMock()
        mock_repos.profiles.get_by_id.return_value = mock_profile

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.profile_updated is True
        mock_repos.profiles.save.assert_called_once_with(mock_profile)

    @pytest.mark.asyncio
    async def test_run_for_user_profile_not_updated_when_no_profile_update(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
    ):
        """When normalization has no profile_update, profile_updated remains False."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run, profile_update=None)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.profile_updated is False

    @pytest.mark.asyncio
    async def test_run_for_user_profile_update_biography_applied(
            self,
            pipeline_service,
            mock_repos,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """The biography from the profile_update is applied to the stored profile."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        profile_update = NormalizedProfile(researcher_id=profile_id, biography="New bio")
        normalized = _make_normalized_result(user_id, extraction_run, profile_update=profile_update)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        mock_profile = MagicMock()
        mock_repos.profiles.get_by_id.return_value = mock_profile

        # Act
        await pipeline_service.run_for_user(user_id)

        # Assert
        assert mock_profile.biography == "New bio"

    @pytest.mark.asyncio
    async def test_run_for_user_profile_update_keywords_applied(
            self,
            pipeline_service,
            mock_repos,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """The keywords from the profile_update are applied to the stored profile."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        profile_update = NormalizedProfile(researcher_id=profile_id, keywords=["robotics"])
        normalized = _make_normalized_result(user_id, extraction_run, profile_update=profile_update)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        mock_profile = MagicMock()
        mock_repos.profiles.get_by_id.return_value = mock_profile

        # Act
        await pipeline_service.run_for_user(user_id)

        # Assert
        assert mock_profile.keywords == ["robotics"]

    @pytest.mark.asyncio
    async def test_run_for_user_profile_update_skipped_when_profile_not_found(
            self,
            pipeline_service,
            mock_repos,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """When the profile is not found in the DB, the update is skipped gracefully."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        profile_update = NormalizedProfile(researcher_id=profile_id, biography="Bio")
        normalized = _make_normalized_result(user_id, extraction_run, profile_update=profile_update)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        mock_repos.profiles.get_by_id.return_value = None

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.profile_updated is False
        mock_repos.profiles.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_for_user_profile_update_error_appended_to_errors(
            self,
            pipeline_service,
            mock_repos,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
            profile_id,
    ):
        """An exception during profile update is caught and appended to pipeline errors."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        profile_update = NormalizedProfile(researcher_id=profile_id, biography="Bio")
        normalized = _make_normalized_result(user_id, extraction_run, profile_update=profile_update)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        mock_repos.profiles.get_by_id.side_effect = Exception("DB failure")

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert any("Profile not updated" in e for e in result.errors)
        assert result.profile_updated is False


# =============================================================================
# run_for_user — result shape
# =============================================================================

class TestPipelineServiceRunForUserResult:
    """Tests for the shape and type of the result returned by run_for_user."""

    @pytest.mark.asyncio
    async def test_run_for_user_returns_pipeline_result_instance(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
    ):
        """run_for_user returns an ExtractionPipelineResult instance."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert isinstance(result, ExtractionPipelineResult)

    @pytest.mark.asyncio
    async def test_run_for_user_result_carries_user_id(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_run_service,
            user_id,
            extraction_run,
    ):
        """The result's user_id matches the one passed to run_for_user."""
        # Arrange
        raw = _make_raw_result(user_id, extraction_run)
        mock_extraction_service.extract_for_user.return_value = raw

        normalized = _make_normalized_result(user_id, extraction_run)
        mock_normalization_service.normalize.return_value = normalized
        mock_run_service.create_run.return_value = _make_run_response(extraction_run)

        # Act
        result = await pipeline_service.run_for_user(user_id)

        # Assert
        assert result.user_id == user_id


# =============================================================================
# run_for_all_users
# =============================================================================

class TestPipelineServiceRunForAllUsers:
    """Tests for bulk pipeline execution via run_for_all_users."""

    def _make_normalized(self, user_id: uuid.UUID, run: ExtractionRun) -> NormalizationResult:
        return _make_normalized_result(user_id, run)

    @pytest.mark.asyncio
    async def test_run_for_all_users_returns_one_result_per_user(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            extraction_run,
    ):
        """One ExtractionPipelineResult is produced per normalized result."""
        # Arrange
        ids = [uuid.uuid4(), uuid.uuid4()]
        raws = [_make_raw_result(uid, extraction_run) for uid in ids]
        normalized = [_make_normalized_result(uid, extraction_run) for uid in ids]

        mock_extraction_service.extract_for_all_users.return_value = raws
        mock_normalization_service.normalize_all.return_value = normalized

        # Act
        results = await pipeline_service.run_for_all_users()

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_run_for_all_users_empty_when_no_users(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
    ):
        """When there are no users, an empty list is returned."""
        # Arrange
        mock_extraction_service.extract_for_all_users.return_value = []
        mock_normalization_service.normalize_all.return_value = []

        # Act
        results = await pipeline_service.run_for_all_users()

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_run_for_all_users_skipped_reasons_forwarded(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            extraction_run,
    ):
        """Skipped reasons from each NormalizationResult are forwarded onto the pipeline result."""
        # Arrange
        uid = uuid.uuid4()
        raw = _make_raw_result(uid, extraction_run)
        normalized = _make_normalized_result(
            uid, extraction_run, skipped_reasons=["Scholar metric already exists."]
        )

        mock_extraction_service.extract_for_all_users.return_value = [raw]
        mock_normalization_service.normalize_all.return_value = [normalized]

        # Act
        results = await pipeline_service.run_for_all_users()

        # Assert
        assert any("already exists" in r for r in results[0].skipped_reasons)

    @pytest.mark.asyncio
    async def test_run_for_all_users_continues_after_single_user_error(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_metric_service,
            extraction_run,
    ):
        """An exception on one user's persist step does not abort processing of others."""
        # Arrange
        uid_bad = uuid.uuid4()
        uid_good = uuid.uuid4()

        profile_id = uuid.uuid4()
        bad_metric = _make_normalized_metric(profile_id, is_duplicate=False)

        normalized_bad = _make_normalized_result(uid_bad, extraction_run, metrics=[bad_metric])
        normalized_good = _make_normalized_result(uid_good, extraction_run)

        mock_extraction_service.extract_for_all_users.return_value = [
            _make_raw_result(uid_bad, extraction_run),
            _make_raw_result(uid_good, extraction_run),
        ]
        mock_normalization_service.normalize_all.return_value = [normalized_bad, normalized_good]
        mock_metric_service.create_metric.side_effect = Exception("persist error")

        # Act
        results = await pipeline_service.run_for_all_users()

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_run_for_all_users_error_appended_on_failure(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            mock_metric_service,
            extraction_run,
    ):
        """When a user's persist step fails, the error is recorded in that user's result."""
        # Arrange
        uid = uuid.uuid4()
        profile_id = uuid.uuid4()
        metric = _make_normalized_metric(profile_id, is_duplicate=False)

        normalized = _make_normalized_result(uid, extraction_run, metrics=[metric])
        mock_extraction_service.extract_for_all_users.return_value = [_make_raw_result(uid, extraction_run)]
        mock_normalization_service.normalize_all.return_value = [normalized]
        mock_metric_service.create_metric.side_effect = Exception("db error")

        # Act
        results = await pipeline_service.run_for_all_users()

        # Assert
        assert len(results[0].errors) > 0

    @pytest.mark.asyncio
    async def test_run_for_all_users_returns_pipeline_result_instances(
            self,
            pipeline_service,
            mock_extraction_service,
            mock_normalization_service,
            extraction_run,
    ):
        """All items in the returned list are ExtractionPipelineResult instances."""
        # Arrange
        uid = uuid.uuid4()
        mock_extraction_service.extract_for_all_users.return_value = [_make_raw_result(uid, extraction_run)]
        mock_normalization_service.normalize_all.return_value = [_make_normalized_result(uid, extraction_run)]

        # Act
        results = await pipeline_service.run_for_all_users()

        # Assert
        assert all(isinstance(r, ExtractionPipelineResult) for r in results)