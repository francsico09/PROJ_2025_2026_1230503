import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.modules.researcher_profile.service.researcher_profile_service import ResearcherProfileService
from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile
from src.modules.researcher_profile.schema.researcher_profile_schemas import ResearcherProfileResponse
from src.modules.user.model.user_model import User
from src.modules.user.model.role.user_role import UserRole
from src.modules.metrics.model.metric_model import ResearcherMetric
from src.core.repositories.repositories import Repositories

def make_profile(with_metrics: bool = False) -> ResearcherProfile:
    profile = ResearcherProfile()
    profile.id = uuid.uuid4()
    profile.scholar_id = f"scholar_{uuid.uuid4().hex[:6]}"
    profile.orcid = f"0000-0001-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}"
    profile.metrics = MagicMock(spec=ResearcherMetric) if with_metrics else None
    return profile


def make_profile_response(profile: ResearcherProfile) -> ResearcherProfileResponse:
    return ResearcherProfileResponse(
        id=profile.id,
        scholar_id=profile.scholar_id,
        orcid=profile.orcid,
        metrics=profile.metrics,
    )


def make_user(role: UserRole = UserRole.researcher) -> User:
    user = User()
    user.id = uuid.uuid4()
    user.name = "Test"
    user.email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    user.active = True
    user.role = role
    return user


@pytest.fixture
def mock_repositories():
    repos = MagicMock(spec=Repositories)
    repos.researcher_profile_repository = AsyncMock()
    return repos


@pytest.fixture
def profile_service(mock_repositories):
    return ResearcherProfileService(repositories=mock_repositories)


@pytest.fixture
def admin_user():
    return make_user(role=UserRole.admin)


@pytest.fixture
def researcher_user():
    return make_user(role=UserRole.researcher)


# create_profile
class TestCreateProfile:

    @pytest.mark.asyncio
    async def test_admin_can_create_profile(self, profile_service, admin_user, mock_repositories):
        profile = make_profile()
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.create.return_value = expected

        result = await profile_service.create_profile(profile=profile, requesting_user=admin_user)

        mock_repositories.researcher_profile_repository.create.assert_awaited_once_with(profile)
        assert result == expected

    @pytest.mark.asyncio
    async def test_researcher_cannot_create_profile(self, profile_service, researcher_user):
        profile = make_profile()

        with pytest.raises(PermissionError):
            await profile_service.create_profile(profile=profile, requesting_user=researcher_user)

    @pytest.mark.asyncio
    async def test_create_profile_returns_profile_response(self, profile_service, admin_user, mock_repositories):
        profile = make_profile()
        mock_repositories.researcher_profile_repository.create.return_value = make_profile_response(profile)

        result = await profile_service.create_profile(profile=profile, requesting_user=admin_user)

        assert isinstance(result, ResearcherProfileResponse)

    @pytest.mark.asyncio
    async def test_create_profile_metrics_are_none_on_creation(self, profile_service, admin_user, mock_repositories):
        """Métricas são associadas automaticamente — não devem ser definidas na criação."""
        profile = make_profile(with_metrics=False)
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.create.return_value = expected

        result = await profile_service.create_profile(profile=profile, requesting_user=admin_user)

        assert result.metrics is None


# delete_profile
class TestDeleteProfile:

    @pytest.mark.asyncio
    async def test_admin_can_delete_profile(self, profile_service, admin_user, mock_repositories):
        profile = make_profile()
        mock_repositories.researcher_profile_repository.delete.return_value = None

        await profile_service.delete_profile(profile=profile, requesting_user=admin_user)

        mock_repositories.researcher_profile_repository.delete.assert_awaited_once_with(profile)

    @pytest.mark.asyncio
    async def test_researcher_cannot_delete_profile(self, profile_service, researcher_user):
        profile = make_profile()

        with pytest.raises(PermissionError):
            await profile_service.delete_profile(profile=profile, requesting_user=researcher_user)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_profile_raises(self, profile_service, admin_user, mock_repositories):
        ghost = make_profile()
        mock_repositories.researcher_profile_repository.delete.side_effect = ValueError("Profile not found")

        with pytest.raises(ValueError, match="Profile not found"):
            await profile_service.delete_profile(profile=ghost, requesting_user=admin_user)


# update_profile

class TestUpdateProfile:

    @pytest.mark.asyncio
    async def test_researcher_can_update_scholar_id(self, profile_service, researcher_user, mock_repositories):
        profile = make_profile()
        profile.metrics = None  # sem alteração de métricas
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.update.return_value = expected

        result = await profile_service.update_profile(profile=profile, requesting_user=researcher_user)

        assert result.scholar_id == profile.scholar_id

    @pytest.mark.asyncio
    async def test_researcher_can_update_orcid(self, profile_service, researcher_user, mock_repositories):
        profile = make_profile()
        profile.orcid = "0000-0002-9999-9999"
        profile.metrics = None
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.update.return_value = expected

        result = await profile_service.update_profile(profile=profile, requesting_user=researcher_user)

        assert result.orcid == "0000-0002-9999-9999"

    @pytest.mark.asyncio
    async def test_researcher_cannot_update_metrics(self, profile_service, researcher_user):
        profile = make_profile(with_metrics=True)  # métricas presentes na payload

        with pytest.raises(PermissionError):
            await profile_service.update_profile(profile=profile, requesting_user=researcher_user)

    @pytest.mark.asyncio
    async def test_admin_can_update_metrics(self, profile_service, admin_user, mock_repositories):
        profile = make_profile(with_metrics=True)
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.update.return_value = expected

        result = await profile_service.update_profile(profile=profile, requesting_user=admin_user)

        assert result.metrics is not None

    @pytest.mark.asyncio
    async def test_update_profile_returns_profile_response(self, profile_service, researcher_user, mock_repositories):
        profile = make_profile()
        profile.metrics = None
        mock_repositories.researcher_profile_repository.update.return_value = make_profile_response(profile)

        result = await profile_service.update_profile(profile=profile, requesting_user=researcher_user)

        assert isinstance(result, ResearcherProfileResponse)

    @pytest.mark.asyncio
    async def test_admin_can_update_basic_info(self, profile_service, admin_user, mock_repositories):
        profile = make_profile()
        profile.scholar_id = "scholar_updated"
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.update.return_value = expected

        result = await profile_service.update_profile(profile=profile, requesting_user=admin_user)

        assert result.scholar_id == "scholar_updated"


# get_profile_by_scholar_id
class TestGetProfileByScholarId:

    @pytest.mark.asyncio
    async def test_get_existing_profile_by_scholar_id(self, profile_service, mock_repositories):
        profile = make_profile()
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.get_by_scholar_id.return_value = expected

        result = await profile_service.get_profile_by_scholar_id(profile.scholar_id)

        mock_repositories.researcher_profile_repository.get_by_scholar_id.assert_awaited_once_with(profile.scholar_id)
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_profile_by_unknown_scholar_id_raises(self, profile_service, mock_repositories):
        mock_repositories.researcher_profile_repository.get_by_scholar_id.side_effect = ValueError("Not found")

        with pytest.raises(ValueError):
            await profile_service.get_profile_by_scholar_id("inexistente")

    @pytest.mark.asyncio
    async def test_get_profile_by_scholar_id_returns_response(self, profile_service, mock_repositories):
        profile = make_profile()
        mock_repositories.researcher_profile_repository.get_by_scholar_id.return_value = make_profile_response(profile)

        result = await profile_service.get_profile_by_scholar_id(profile.scholar_id)

        assert isinstance(result, ResearcherProfileResponse)


# get_profile_by_orcid
class TestGetProfileByOrcid:

    @pytest.mark.asyncio
    async def test_get_existing_profile_by_orcid(self, profile_service, mock_repositories):
        profile = make_profile()
        expected = make_profile_response(profile)
        mock_repositories.researcher_profile_repository.get_by_orcid.return_value = expected

        result = await profile_service.get_profile_by_orcid(profile.orcid)

        mock_repositories.researcher_profile_repository.get_by_orcid.assert_awaited_once_with(profile.orcid)
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_profile_by_unknown_orcid_raises(self, profile_service, mock_repositories):
        mock_repositories.researcher_profile_repository.get_by_orcid.side_effect = ValueError("Not found")

        with pytest.raises(ValueError):
            await profile_service.get_profile_by_orcid("0000-0000-0000-0000")

    @pytest.mark.asyncio
    async def test_get_profile_by_orcid_returns_response(self, profile_service, mock_repositories):
        profile = make_profile()
        mock_repositories.researcher_profile_repository.get_by_orcid.return_value = make_profile_response(profile)

        result = await profile_service.get_profile_by_orcid(profile.orcid)

        assert isinstance(result, ResearcherProfileResponse)


# list_profiles
class TestListProfiles:

    @pytest.mark.asyncio
    async def test_list_profiles_returns_all_profiles(self, profile_service, mock_repositories):
        profiles = [make_profile_response(make_profile()) for _ in range(4)]
        mock_repositories.researcher_profile_repository.list_all.return_value = profiles

        result = await profile_service.list_profiles()

        mock_repositories.researcher_profile_repository.list_all.assert_awaited_once()
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_list_profiles_returns_list_of_response(self, profile_service, mock_repositories):
        mock_repositories.researcher_profile_repository.list_all.return_value = [
            make_profile_response(make_profile()),
        ]

        result = await profile_service.list_profiles()

        assert all(isinstance(p, ResearcherProfileResponse) for p in result)

    @pytest.mark.asyncio
    async def test_list_profiles_empty_returns_empty_list(self, profile_service, mock_repositories):
        mock_repositories.researcher_profile_repository.list_all.return_value = []

        result = await profile_service.list_profiles()

        assert result == []
