import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest

from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import (
    ExtractionStatus,
    ExtractionTrigger,
)
from src.core.domain.researcher_metric.researcher_metric_model.source_model import SourceName
from src.modules.normalization.models.result.normalization_result import (
    RawExtractionResult,
    RawScholarMetrics,
    RawWosMetrics,
    RawOrcidProfile,
    RawScopusMetrics,
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
def mock_user(user_id):
    user = MagicMock()
    user.id = user_id
    user.name = "Ana Costa"
    user.active = True
    return user


@pytest.fixture
def mock_profile(profile_id):
    profile = MagicMock()
    profile.id = profile_id
    profile.scholar_id = "scholar_abc"
    profile.wos_id = "wos_abc"
    profile.scopus_id = "scopus_abc"
    profile.orcid = "0000-0001-2345-6789"
    profile.keywords = ["AI", "ML"]
    return profile


@pytest.fixture
def raw_scholar():
    return MagicMock(spec=RawScholarMetrics)


@pytest.fixture
def raw_wos():
    return MagicMock(spec=RawWosMetrics)


@pytest.fixture
def raw_scopus():
    return MagicMock(spec=RawScopusMetrics)


@pytest.fixture
def raw_orcid():
    return MagicMock(spec=RawOrcidProfile)


@pytest.fixture
def mock_scholar_extractor(raw_scholar):
    e = MagicMock()
    e.extract.return_value = raw_scholar
    return e


@pytest.fixture
def mock_wos_extractor(raw_wos):
    e = MagicMock()
    e.extract.return_value = raw_wos
    return e


@pytest.fixture
def mock_scopus_extractor(raw_scopus):
    e = MagicMock()
    e.extract.return_value = raw_scopus
    return e


@pytest.fixture
def mock_orcid_extractor(raw_orcid):
    e = MagicMock()
    e.extract_by_id.return_value = raw_orcid
    return e


@pytest.fixture
def extraction_service(
        mock_repos,
        mock_scholar_extractor,
        mock_orcid_extractor,
        mock_wos_extractor,
        mock_scopus_extractor,
):
    from src.modules.extraction.service.extraction_service import ExtractionService
    return ExtractionService(
        repos=mock_repos,
        scholar_extractor=mock_scholar_extractor,
        orcid_extractor=mock_orcid_extractor,
        wos_extractor=mock_wos_extractor,
        scopus_extractor=mock_scopus_extractor,
    )


# =============================================================================
# extract_for_user — user / profile lookup
# =============================================================================

class TestExtractionServiceUserLookup:
    """Tests for user and profile resolution in extract_for_user."""

    @pytest.mark.asyncio
    async def test_extract_raises_when_user_not_found(
            self, extraction_service, mock_repos, user_id
    ):
        """Extracting for a non-existent user raises ValueError."""
        # Arrange
        mock_repos.users.get_by_id.return_value = None
        mock_repos.profiles.get_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=str(user_id)):
            await extraction_service.extract_for_user(user_id)

    @pytest.mark.asyncio
    async def test_extract_raises_when_profile_not_found(
            self, extraction_service, mock_repos, mock_user, user_id
    ):
        """Extracting for a user without a researcher profile raises ValueError."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=str(user_id)):
            await extraction_service.extract_for_user(user_id)

    @pytest.mark.asyncio
    async def test_extract_does_not_call_extractors_when_user_missing(
            self,
            extraction_service,
            mock_repos,
            mock_scholar_extractor,
            mock_wos_extractor,
            mock_scopus_extractor,
            mock_orcid_extractor,
            user_id,
    ):
        """No extractor is called when the user lookup fails."""
        # Arrange
        mock_repos.users.get_by_id.return_value = None
        mock_repos.profiles.get_by_user_id.return_value = None

        # Act
        with pytest.raises(ValueError):
            await extraction_service.extract_for_user(user_id)

        # Assert
        mock_scholar_extractor.extract.assert_not_called()
        mock_wos_extractor.extract.assert_not_called()
        mock_scopus_extractor.extract.assert_not_called()
        mock_orcid_extractor.extract_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_result_carries_user_id(
            self, extraction_service, mock_repos, mock_user, mock_profile, user_id
    ):
        """The RawExtractionResult carries the string representation of the user id."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(user_id)

        # Assert
        assert result.user_id == str(user_id)

    @pytest.mark.asyncio
    async def test_extract_result_run_researcher_id_matches_profile(
            self, extraction_service, mock_repos, mock_user, mock_profile
    ):
        """The ExtractionRun on the result uses the profile's id as researcher_id."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.run.researcher_id == mock_profile.id

    @pytest.mark.asyncio
    async def test_extract_result_is_raw_extraction_result(
            self, extraction_service, mock_repos, mock_user, mock_profile
    ):
        """extract_for_user returns a RawExtractionResult instance."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert isinstance(result, RawExtractionResult)


# =============================================================================
# extract_for_user — all sources succeed
# =============================================================================

class TestExtractionServiceAllSourcesSucceed:
    """Tests for the happy path where every extractor returns data."""

    @pytest.mark.asyncio
    async def test_all_sources_in_sources_succeeded(
            self, extraction_service, mock_repos, mock_user, mock_profile
    ):
        """When all extractors return data, all four sources appear in sources_succeeded."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert SourceName.scholar in result.run.sources_succeeded
        assert SourceName.wos in result.run.sources_succeeded
        assert SourceName.scopus in result.run.sources_succeeded
        assert SourceName.orcid in result.run.sources_succeeded

    @pytest.mark.asyncio
    async def test_all_sources_in_sources_attempted(
            self, extraction_service, mock_repos, mock_user, mock_profile
    ):
        """All four sources appear in sources_attempted regardless of outcome."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert SourceName.scholar in result.run.sources_attempted
        assert SourceName.wos in result.run.sources_attempted
        assert SourceName.scopus in result.run.sources_attempted
        assert SourceName.orcid in result.run.sources_attempted

    @pytest.mark.asyncio
    async def test_status_is_completed_when_no_errors(
            self, extraction_service, mock_repos, mock_user, mock_profile
    ):
        """The run status is completed when all sources succeed."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.run.status == ExtractionStatus.completed

    @pytest.mark.asyncio
    async def test_no_errors_when_all_sources_succeed(
            self, extraction_service, mock_repos, mock_user, mock_profile
    ):
        """The errors list is empty when every extractor returns data."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_all_source_data_fields_populated(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            raw_scholar,
            raw_wos,
            raw_scopus,
            raw_orcid,
    ):
        """When all extractors succeed, all data fields on the result are set."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.scholar is raw_scholar
        assert result.wos is raw_wos
        assert result.scopus is raw_scopus
        assert result.orcid is raw_orcid


# =============================================================================
# extract_for_user — individual source failures
# =============================================================================

class TestExtractionServiceSourceFailures:
    """Tests for graceful handling of individual extractor failures."""

    @pytest.mark.asyncio
    async def test_scholar_failure_recorded_in_errors(
            self, extraction_service, mock_repos, mock_user, mock_profile, mock_scholar_extractor
    ):
        """When Scholar returns no data, an error is appended and extraction continues."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_scholar_extractor.extract.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.scholar is None
        assert SourceName.scholar not in result.run.sources_succeeded
        assert any("Scholar" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_wos_failure_recorded_in_errors(
            self, extraction_service, mock_repos, mock_user, mock_profile, mock_wos_extractor
    ):
        """When WoS returns no data, an error is appended and extraction continues."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_wos_extractor.extract.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.wos is None
        assert SourceName.wos not in result.run.sources_succeeded
        assert any("WoS" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_scopus_failure_recorded_in_errors(
            self, extraction_service, mock_repos, mock_user, mock_profile, mock_scopus_extractor
    ):
        """When Scopus returns no data, an error is appended and extraction continues."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_scopus_extractor.extract.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.scopus is None
        assert SourceName.scopus not in result.run.sources_succeeded
        assert any("Scopus" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_orcid_failure_recorded_in_errors(
            self, extraction_service, mock_repos, mock_user, mock_profile, mock_orcid_extractor
    ):
        """When ORCID returns no data, an error is appended and extraction continues."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_orcid_extractor.extract_by_id.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.orcid is None
        assert SourceName.orcid not in result.run.sources_succeeded
        assert any("ORCID" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_status_is_partial_when_some_sources_fail(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_scholar_extractor,
            mock_wos_extractor,
    ):
        """The run status is partial when at least one source succeeds and one fails."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_scholar_extractor.extract.return_value = None
        mock_wos_extractor.extract.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.run.status == ExtractionStatus.partial

    @pytest.mark.asyncio
    async def test_single_source_failure_does_not_stop_other_extractors(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_scholar_extractor,
            mock_wos_extractor,
            mock_scopus_extractor,
            mock_orcid_extractor,
            raw_wos,
            raw_scopus,
            raw_orcid,
    ):
        """A Scholar failure does not prevent WoS, Scopus, and ORCID from being attempted."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_scholar_extractor.extract.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.wos is raw_wos
        assert result.scopus is raw_scopus
        assert result.orcid is raw_orcid
        mock_wos_extractor.extract.assert_called_once()
        mock_scopus_extractor.extract.assert_called_once()
        mock_orcid_extractor.extract_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_sources_fail_status_is_partial(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_scholar_extractor,
            mock_wos_extractor,
            mock_scopus_extractor,
            mock_orcid_extractor,
    ):
        """When every extractor returns None, the run status is partial (errors present)."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_scholar_extractor.extract.return_value = None
        mock_wos_extractor.extract.return_value = None
        mock_scopus_extractor.extract.return_value = None
        mock_orcid_extractor.extract_by_id.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.run.status == ExtractionStatus.partial
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_all_sources_fail_no_data_fields_set(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_scholar_extractor,
            mock_wos_extractor,
            mock_scopus_extractor,
            mock_orcid_extractor,
    ):
        """When every extractor returns None, all data fields on the result remain None."""
        # Arrange
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile
        mock_scholar_extractor.extract.return_value = None
        mock_wos_extractor.extract.return_value = None
        mock_scopus_extractor.extract.return_value = None
        mock_orcid_extractor.extract_by_id.return_value = None

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert result.scholar is None
        assert result.wos is None
        assert result.scopus is None
        assert result.orcid is None


# =============================================================================
# extract_for_user — missing external IDs on profile
# =============================================================================

class TestExtractionServiceMissingIdentifiers:
    """Tests for profiles that are missing one or more external IDs."""

    @pytest.mark.asyncio
    async def test_scholar_falls_back_to_user_name_when_no_scholar_id(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_scholar_extractor,
    ):
        """When scholar_id is absent, Scholar extraction uses the user's name as query."""
        # Arrange
        mock_profile.scholar_id = None
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        await extraction_service.extract_for_user(mock_user.id)

        # Assert
        mock_scholar_extractor.extract.assert_called_once_with(mock_user.name)

    @pytest.mark.asyncio
    async def test_wos_skipped_when_no_wos_id(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_wos_extractor,
    ):
        """When wos_id is absent, the WoS extractor is never called."""
        # Arrange
        mock_profile.wos_id = None
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        mock_wos_extractor.extract.assert_not_called()
        assert result.wos is None

    @pytest.mark.asyncio
    async def test_orcid_skipped_when_no_orcid(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_orcid_extractor,
    ):
        """When orcid is absent, the ORCID extractor is never called."""
        # Arrange
        mock_profile.orcid = None
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        mock_orcid_extractor.extract_by_id.assert_not_called()
        assert result.orcid is None

    @pytest.mark.asyncio
    async def test_scopus_falls_back_to_user_name_when_no_scopus_id(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
            mock_scopus_extractor,
    ):
        """When scopus_id is absent, Scopus extraction uses the user's name as identifier."""
        # Arrange
        mock_profile.scopus_id = None
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        await extraction_service.extract_for_user(mock_user.id)

        # Assert
        mock_scopus_extractor.extract.assert_called_once_with(mock_user.name, mock_user.name)

    @pytest.mark.asyncio
    async def test_wos_not_in_sources_succeeded_when_skipped(
            self,
            extraction_service,
            mock_repos,
            mock_user,
            mock_profile,
    ):
        """When WoS is skipped due to missing id, it still appears in sources_attempted."""
        # Arrange
        mock_profile.wos_id = None
        mock_repos.users.get_by_id.return_value = mock_user
        mock_repos.profiles.get_by_user_id.return_value = mock_profile

        # Act
        result = await extraction_service.extract_for_user(mock_user.id)

        # Assert
        assert SourceName.wos in result.run.sources_attempted
        assert SourceName.wos not in result.run.sources_succeeded


# =============================================================================
# extract_for_all_users
# =============================================================================

class TestExtractionServiceExtractForAllUsers:
    """Tests for bulk extraction via extract_for_all_users."""

    def _make_user(self, active: bool = True, has_profile: bool = True):
        user = MagicMock()
        user.id = uuid.uuid4()
        user.name = "Test User"
        user.active = active
        if has_profile:
            profile = MagicMock()
            profile.id = uuid.uuid4()
            profile.scholar_id = "s_id"
            profile.wos_id = "w_id"
            profile.scopus_id = "sc_id"
            profile.orcid = "0000-0001-0000-0001"
            profile.keywords = []
            user.researcherProfile = profile
        else:
            user.researcherProfile = None
        return user

    @pytest.mark.asyncio
    async def test_extract_for_all_users_returns_one_result_per_active_user(
            self, extraction_service, mock_repos
    ):
        """One result is produced for each active user."""
        # Arrange
        users = [self._make_user(), self._make_user()]
        mock_repos.users.get_all.return_value = users
        mock_repos.users.get_by_id.side_effect = lambda uid: next(u for u in users if u.id == uid)
        mock_repos.profiles.get_by_user_id.side_effect = lambda uid: next(
            (u.researcherProfile for u in users if u.id == uid), None
        )

        # Act
        results = await extraction_service.extract_for_all_users()

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_extract_for_all_users_skips_inactive_users(
            self, extraction_service, mock_repos
    ):
        """Inactive users are skipped and produce no result."""
        # Arrange
        active_user = self._make_user(active=True)
        inactive_user = self._make_user(active=False)
        mock_repos.users.get_all.return_value = [active_user, inactive_user]
        mock_repos.users.get_by_id.return_value = active_user
        mock_repos.profiles.get_by_user_id.return_value = active_user.researcherProfile

        # Act
        results = await extraction_service.extract_for_all_users()

        # Assert
        assert len(results) == 1
        assert results[0].user_id == str(active_user.id)

    @pytest.mark.asyncio
    async def test_extract_for_all_users_empty_list_when_no_users(
            self, extraction_service, mock_repos
    ):
        """When there are no users, an empty list is returned."""
        # Arrange
        mock_repos.users.get_all.return_value = []

        # Act
        results = await extraction_service.extract_for_all_users()

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_extract_for_all_users_continues_after_user_exception(
            self, extraction_service, mock_repos
    ):
        """An exception on one user does not stop extraction for the remaining users."""
        # Arrange
        bad_user = self._make_user()
        good_user = self._make_user()
        mock_repos.users.get_all.return_value = [bad_user, good_user]

        call_count = 0

        async def get_by_id_side_effect(uid):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated failure")
            return good_user

        mock_repos.users.get_by_id.side_effect = get_by_id_side_effect
        mock_repos.profiles.get_by_user_id.return_value = good_user.researcherProfile

        # Act
        results = await extraction_service.extract_for_all_users()

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_extract_for_all_users_failed_user_result_has_error(
            self, extraction_service, mock_repos
    ):
        """A failed user produces a RawExtractionResult with a fatal error message."""
        # Arrange
        bad_user = self._make_user()
        mock_repos.users.get_all.return_value = [bad_user]
        mock_repos.users.get_by_id.side_effect = RuntimeError("boom")

        # Act
        results = await extraction_service.extract_for_all_users()

        # Assert
        assert len(results) == 1
        assert any("fatal error" in e for e in results[0].errors)

    @pytest.mark.asyncio
    async def test_extract_for_all_users_all_active_users_attempted(
            self, extraction_service, mock_repos
    ):
        """All active users are attempted, not just the first."""
        # Arrange
        users = [self._make_user(), self._make_user(), self._make_user()]
        mock_repos.users.get_all.return_value = users
        mock_repos.users.get_by_id.side_effect = lambda uid: next(u for u in users if u.id == uid)
        mock_repos.profiles.get_by_user_id.side_effect = lambda uid: next(
            (u.researcherProfile for u in users if u.id == uid), None
        )

        # Act
        results = await extraction_service.extract_for_all_users()

        # Assert
        assert len(results) == 3
        result_user_ids = {r.user_id for r in results}
        assert result_user_ids == {str(u.id) for u in users}