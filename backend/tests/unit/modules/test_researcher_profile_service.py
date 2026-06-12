import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from starlette import status

from src.modules.researcher_profile.service.researcher_profile_service import ResearcherProfileService
from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import ResearcherProfile
from src.core.domain.researcher_profile.researcher_profile_schema.researcher_profile_schemas import (
    ResearcherProfileCreate, ResearcherProfileResponse, ResearcherProfileUpdate
)
from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_model.user_role import UserRole
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse


@pytest.fixture
def mock_repos():
    """Cria um mock das repositories com contexto assíncrono."""
    repos = AsyncMock()
    repos.profiles = AsyncMock()
    repos.users = AsyncMock()
    repos.commit = AsyncMock()
    repos.__aenter__ = AsyncMock(return_value=repos)
    repos.__aexit__ = AsyncMock(return_value=None)
    return repos


@pytest.fixture
def researcher_profile_service(mock_repos):
    """Cria uma instância do ResearcherProfileService com mocks."""
    return ResearcherProfileService(repos=mock_repos)


@pytest.fixture
def sample_profile_id():
    """Gera um UUID para testes."""
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
        'wos_id': 'wos_123',
        'scopus_id': 'scopus_123',
        'biography': 'Pesquisador em IA',
        'affiliation': 'Universidade XYZ'
    }

# =============================================================================
# create_profile
# =============================================================================

class TestResearcherProfileServiceCreate:
    """Tests for profile creation via ResearcherProfileService.create_profile."""

    # -------------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_profile_required_fields_only(self, researcher_profile_service, mock_repos):
        """Creating a profile with only required fields (no external IDs) succeeds."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=["AI", "ML"])
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None

        # Act
        result = await researcher_profile_service.create_profile(profile_data)

        # Assert
        assert result.keywords == ["AI", "ML"]
        assert result.scholar_id is None
        assert result.orcid is None
        assert result.scopus_id is None
        assert result.wos_id is None

        mock_repos.profiles.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile_with_all_external_ids(self, researcher_profile_service, mock_repos):
        """Creating a profile with all external IDs succeeds when none already exist."""
        # Arrange
        profile_data = ResearcherProfileCreate(
            keywords=["NLP"],
            scholar_id="scholar_abc",
            orcid="0000-0001-2345-6789",
            scopus_id="scopus_abc",
            wos_id="wos_abc",
        )
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None

        # Act
        result = await researcher_profile_service.create_profile(profile_data)

        # Assert
        assert result.scholar_id == "scholar_abc"
        assert result.orcid == "0000-0001-2345-6789"
        assert result.scopus_id == "scopus_abc"
        assert result.wos_id == "wos_abc"

        mock_repos.profiles.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile_generates_unique_ids(self, researcher_profile_service, mock_repos):
        """Each created profile receives a distinct UUID."""
        # Arrange
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None

        profile_data_1 = ResearcherProfileCreate(keywords=["A"])
        profile_data_2 = ResearcherProfileCreate(keywords=["B"])

        # Act
        result_1 = await researcher_profile_service.create_profile(profile_data_1)
        result_2 = await researcher_profile_service.create_profile(profile_data_2)

        # Assert
        assert result_1.id != result_2.id

    @pytest.mark.asyncio
    async def test_create_profile_metrics_start_empty(self, researcher_profile_service, mock_repos):
        """A newly created profile always has an empty metrics list."""
        # Arrange
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        profile_data = ResearcherProfileCreate(keywords=[])

        # Act
        result = await researcher_profile_service.create_profile(profile_data)

        # Assert
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_create_profile_save_called_before_commit(self, researcher_profile_service, mock_repos):
        """save() must be called before commit()."""
        # Arrange
        call_order = []
        mock_repos.profiles.save.side_effect = lambda _: call_order.append("save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None

        profile_data = ResearcherProfileCreate(keywords=[])

        # Act
        await researcher_profile_service.create_profile(profile_data)

        # Assert
        assert call_order == ["save", "commit"]

    # -------------------------------------------------------------------------
    # Duplicate external IDs
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_scholar_id_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile
    ):
        """Creating a profile with a Scholar ID that already exists raises HTTP 400."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=[], scholar_id="scholar_123")
        mock_repos.profiles.get_by_scholar_id.return_value = sample_profile

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.create_profile(profile_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Scholar ID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_orcid_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile
    ):
        """Creating a profile with an ORCID that already exists raises HTTP 400."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=[], orcid="0000-0001-2345-6789")
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = sample_profile

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.create_profile(profile_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "ORCID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_scopus_id_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile
    ):
        """Creating a profile with a Scopus ID that already exists raises HTTP 400."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=[], scopus_id="scopus_123")
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = sample_profile

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.create_profile(profile_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Scopus ID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_wos_id_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile
    ):
        """Creating a profile with a WoS ID that already exists raises HTTP 400."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=[], wos_id="wos_123")
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = sample_profile

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.create_profile(profile_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "WoS ID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_profile_scholar_id_check_uses_exact_value(self, researcher_profile_service, mock_repos):
        """The Scholar ID uniqueness check is called with the exact value provided."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=[], scholar_id="exact_scholar_id")
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None

        # Act
        await researcher_profile_service.create_profile(profile_data)

        # Assert
        mock_repos.profiles.get_by_scholar_id.assert_called_once_with("exact_scholar_id")

    @pytest.mark.asyncio
    async def test_create_profile_no_external_ids_skips_uniqueness_checks(
            self, researcher_profile_service, mock_repos
    ):
        """When no external IDs are provided, no uniqueness checks are performed."""
        # Arrange
        profile_data = ResearcherProfileCreate(keywords=[])

        # Act
        await researcher_profile_service.create_profile(profile_data)

        # Assert
        mock_repos.profiles.get_by_scholar_id.assert_not_called()
        mock_repos.profiles.get_by_orcid.assert_not_called()
        mock_repos.profiles.get_by_scopus_id.assert_not_called()
        mock_repos.profiles.get_by_wos_id.assert_not_called()


# =============================================================================
# delete_profile
# =============================================================================

class TestResearcherProfileServiceDelete:
    """Tests for profile deletion via ResearcherProfileService.delete_profile."""

    # -------------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_profile_success(self, researcher_profile_service, mock_repos, sample_profile):
        """Deleting an existing profile with no metrics succeeds."""
        # Arrange
        sample_profile.metrics = []
        mock_repos.profiles.get_by_id.return_value = sample_profile

        # Act
        await researcher_profile_service.delete_profile(sample_profile.id)

        # Assert
        mock_repos.profiles.delete.assert_called_once_with(sample_profile.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profile_removes_linked_metrics(
            self, researcher_profile_service, mock_repos, sample_profile, sample_metric
    ):
        """All metrics linked to the profile are deleted before the profile itself."""
        # Arrange
        sample_profile.metrics = [sample_metric]
        mock_repos.profiles.get_by_id.return_value = sample_profile

        # Act
        await researcher_profile_service.delete_profile(sample_profile.id)

        # Assert
        mock_repos.metrics.delete.assert_called_once_with(sample_metric.id)
        mock_repos.profiles.delete.assert_called_once_with(sample_profile.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profile_removes_multiple_metrics(
            self, researcher_profile_service, mock_repos, sample_profile, metric_data
    ):
        """All metrics (not just the first) are deleted when there are several."""
        # Arrange
        from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric

        metric_a = ResearcherMetric(**{**metric_data, "id": uuid.uuid4()})
        metric_b = ResearcherMetric(**{**metric_data, "id": uuid.uuid4()})
        metric_c = ResearcherMetric(**{**metric_data, "id": uuid.uuid4()})

        sample_profile.metrics = [metric_a, metric_b, metric_c]
        mock_repos.profiles.get_by_id.return_value = sample_profile

        # Act
        await researcher_profile_service.delete_profile(sample_profile.id)

        # Assert
        assert mock_repos.metrics.delete.call_count == 3
        deleted_ids = {call.args[0] for call in mock_repos.metrics.delete.call_args_list}
        assert deleted_ids == {metric_a.id, metric_b.id, metric_c.id}

    @pytest.mark.asyncio
    async def test_delete_profile_metrics_deleted_before_profile(
            self, researcher_profile_service, mock_repos, sample_profile, sample_metric
    ):
        """Metrics are deleted before the profile to respect referential integrity."""
        # Arrange
        call_order = []
        sample_profile.metrics = [sample_metric]
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.metrics.delete.side_effect = lambda _: call_order.append("metric")
        mock_repos.profiles.delete.side_effect = lambda _: call_order.append("profile")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await researcher_profile_service.delete_profile(sample_profile.id)

        # Assert
        assert call_order == ["metric", "profile", "commit"]

    @pytest.mark.asyncio
    async def test_delete_profile_no_metrics_skips_metric_deletion(
            self, researcher_profile_service, mock_repos, sample_profile
    ):
        """When a profile has no metrics, the metric repository is never called."""
        # Arrange
        sample_profile.metrics = []
        mock_repos.profiles.get_by_id.return_value = sample_profile

        # Act
        await researcher_profile_service.delete_profile(sample_profile.id)

        # Assert
        mock_repos.metrics.delete.assert_not_called()
        mock_repos.profiles.delete.assert_called_once_with(sample_profile.id)

    # -------------------------------------------------------------------------
    # Not found
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_profile_not_found_raises_404(self, researcher_profile_service, mock_repos):
        """Attempting to delete a non-existent profile raises HTTP 404."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.delete_profile(uuid.uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Profile not found" in exc_info.value.detail
        mock_repos.metrics.delete.assert_not_called()
        mock_repos.profiles.delete.assert_not_called()
        mock_repos.commit.assert_not_called()


# =============================================================================
# update_profile
# =============================================================================

class TestResearcherProfileServiceUpdate:
    """Tests for profile updates via ResearcherProfileService.update_profile."""

    # -------------------------------------------------------------------------
    # Success — allowed fields
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_profile_keywords_success(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user
    ):
        """An admin can update the keywords of a profile."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        profile_update = ResearcherProfileUpdate(keywords=["robotics", "vision"])

        # Act
        result = await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        # Assert
        assert result.keywords == ["robotics", "vision"]
        mock_repos.profiles.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_biography_success(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user
    ):
        """An admin can update the biography of a profile."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        profile_update = ResearcherProfileUpdate(biography="Updated bio.")

        # Act
        result = await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        # Assert
        assert result.biography == "Updated bio."
        mock_repos.profiles.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_external_ids_success_admin(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user
    ):
        """An admin can update all external IDs when none conflict with existing profiles."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        profile_update = ResearcherProfileUpdate(
            scholar_id="new_scholar",
            orcid="0000-0002-9999-0000",
            scopus_id="new_scopus",
            wos_id="new_wos",
        )

        # Act
        result = await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        # Assert
        assert result.scholar_id == "new_scholar"
        assert result.orcid == "0000-0002-9999-0000"
        assert result.scopus_id == "new_scopus"
        assert result.wos_id == "new_wos"
        mock_repos.profiles.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_researcher_can_update_allowed_fields(
            self, researcher_profile_service, mock_repos, sample_profile, sample_user
    ):
        """A researcher can update non-metric fields such as keywords and biography."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        profile_update = ResearcherProfileUpdate(keywords=["updated"])

        # Act
        result = await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_user)

        # Assert
        assert result.keywords == ["updated"]
        mock_repos.profiles.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_save_called_before_commit(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user
    ):
        """save() must be called before commit() during an update."""
        # Arrange
        call_order = []
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        mock_repos.profiles.save.side_effect = lambda _: call_order.append("save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await researcher_profile_service.update_profile(
            sample_profile.id, ResearcherProfileUpdate(keywords=[]), sample_admin_user
        )

        # Assert
        assert call_order == ["save", "commit"]

    # -------------------------------------------------------------------------
    # Researcher cannot update metrics
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_profile_researcher_cannot_update_metrics_raises_403(
            self, researcher_profile_service, mock_repos, sample_profile, sample_user, sample_metric
    ):
        """A researcher attempting to update metrics raises HTTP 403."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        profile_update = ResearcherProfileUpdate(metrics=[sample_metric])

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "admins" in exc_info.value.detail.lower()
        mock_repos.profiles.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_profile_admin_can_update_metrics(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user, sample_metric
    ):
        """An admin is allowed to update metrics on a profile."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = None
        profile_update = ResearcherProfileUpdate(metrics=[sample_metric])

        # Act & Assert — must not raise
        await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)
        mock_repos.profiles.save.assert_called_once()

    # -------------------------------------------------------------------------
    # External ID uniqueness on update
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_scholar_id_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user, profile_data
    ):
        """Updating to a Scholar ID already used by another profile raises HTTP 400."""
        # Arrange
        other_profile = ResearcherProfile(**{**profile_data, "id": uuid.uuid4()})
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = other_profile
        profile_update = ResearcherProfileUpdate(scholar_id="taken_scholar")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Scholar ID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_orcid_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user, profile_data
    ):
        """Updating to an ORCID already used by another profile raises HTTP 400."""
        # Arrange
        other_profile = ResearcherProfile(**{**profile_data, "id": uuid.uuid4()})
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = other_profile
        profile_update = ResearcherProfileUpdate(orcid="0000-0000-0000-0001")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "ORCID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_scopus_id_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user, profile_data
    ):
        """Updating to a Scopus ID already used by another profile raises HTTP 400."""
        # Arrange
        other_profile = ResearcherProfile(**{**profile_data, "id": uuid.uuid4()})
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = other_profile
        profile_update = ResearcherProfileUpdate(scopus_id="taken_scopus")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Scopus ID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_wos_id_raises_400(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user, profile_data
    ):
        """Updating to a WoS ID already used by another profile raises HTTP 400."""
        # Arrange
        other_profile = ResearcherProfile(**{**profile_data, "id": uuid.uuid4()})
        mock_repos.profiles.get_by_id.return_value = sample_profile
        mock_repos.profiles.get_by_scholar_id.return_value = None
        mock_repos.profiles.get_by_orcid.return_value = None
        mock_repos.profiles.get_by_scopus_id.return_value = None
        mock_repos.profiles.get_by_wos_id.return_value = other_profile
        profile_update = ResearcherProfileUpdate(wos_id="taken_wos")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "WoS ID" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_profile_no_external_id_changes_skips_uniqueness_checks(
            self, researcher_profile_service, mock_repos, sample_profile, sample_admin_user
    ):
        """When no external IDs are being updated, no uniqueness checks are performed."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = sample_profile
        profile_update = ResearcherProfileUpdate(keywords=["only keywords changed"])

        # Act
        await researcher_profile_service.update_profile(sample_profile.id, profile_update, sample_admin_user)

        # Assert
        mock_repos.profiles.get_by_scholar_id.assert_not_called()
        mock_repos.profiles.get_by_orcid.assert_not_called()
        mock_repos.profiles.get_by_scopus_id.assert_not_called()
        mock_repos.profiles.get_by_wos_id.assert_not_called()

    # -------------------------------------------------------------------------
    # Not found
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_profile_not_found_raises_404(
            self, researcher_profile_service, mock_repos, sample_admin_user
    ):
        """Attempting to update a non-existent profile raises HTTP 404."""
        # Arrange
        mock_repos.profiles.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await researcher_profile_service.update_profile(
                uuid.uuid4(), ResearcherProfileUpdate(keywords=[]), sample_admin_user
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Profile not found" in exc_info.value.detail
        mock_repos.profiles.save.assert_not_called()
        mock_repos.commit.assert_not_called()


# =============================================================================
# fetch_profiles
# =============================================================================

class TestResearcherProfileServiceFetch:
    """Tests for paginated profile listing via ResearcherProfileService.fetch_profiles."""

    @pytest.mark.asyncio
    async def test_fetch_profiles_returns_correct_items(
            self, researcher_profile_service, mock_repos, sample_profile, pagination_params
    ):
        """The items in the response correspond to the profiles returned by the repository."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_profile]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        result = await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        assert len(result.items) == 1
        assert result.items[0].id == sample_profile.id

    @pytest.mark.asyncio
    async def test_fetch_profiles_returns_correct_pagination_metadata(
            self, researcher_profile_service, mock_repos, sample_profile, pagination_params
    ):
        """total, page, page_size, and pages are forwarded accurately from the repository result."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_profile]
        raw_result.total = 55
        raw_result.page = 3
        raw_result.page_size = 10
        raw_result.pages = 6
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        result = await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        assert result.total == 55
        assert result.page == 3
        assert result.page_size == 10
        assert result.pages == 6

    @pytest.mark.asyncio
    async def test_fetch_profiles_empty_list(self, researcher_profile_service, mock_repos, pagination_params):
        """When there are no profiles, items is empty and total is 0."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        result = await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        assert result.items == []
        assert result.total == 0
        assert result.pages == 0

    @pytest.mark.asyncio
    async def test_fetch_profiles_multiple_items(
            self, researcher_profile_service, mock_repos, profile_data, pagination_params
    ):
        """All profiles in the repository result appear in the response items."""
        # Arrange
        profile_a = ResearcherProfile(**profile_data)
        profile_b = ResearcherProfile(**{**profile_data, "id": uuid.uuid4(), "scholar_id": "scholar_b"})
        profile_c = ResearcherProfile(**{**profile_data, "id": uuid.uuid4(), "scholar_id": "scholar_c"})

        raw_result = MagicMock()
        raw_result.items = [profile_a, profile_b, profile_c]
        raw_result.total = 3
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        result = await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        assert len(result.items) == 3
        result_ids = {p.id for p in result.items}
        assert result_ids == {profile_a.id, profile_b.id, profile_c.id}

    @pytest.mark.asyncio
    async def test_fetch_profiles_returns_paginated_response_type(
            self, researcher_profile_service, mock_repos, pagination_params
    ):
        """The return type is PaginatedResponse."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        result = await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        assert isinstance(result, PaginatedResponse)

    @pytest.mark.asyncio
    async def test_fetch_profiles_items_are_validated_responses(
            self, researcher_profile_service, mock_repos, sample_profile, pagination_params
    ):
        """Each item in the response is a validated ResearcherProfileResponse, not a raw domain object."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_profile]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        result = await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        assert all(isinstance(item, ResearcherProfileResponse) for item in result.items)

    @pytest.mark.asyncio
    async def test_fetch_profiles_passes_pagination_params_to_repo(
            self, researcher_profile_service, mock_repos, pagination_params
    ):
        """The pagination params are forwarded to the repository unchanged."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.profiles.fetch.return_value = raw_result

        # Act
        await researcher_profile_service.fetch_profiles(pagination_params)

        # Assert
        mock_repos.profiles.fetch.assert_called_once_with(pagination_params)