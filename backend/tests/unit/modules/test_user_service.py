import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from starlette import status

from src.modules.user.service.user_service import UserService
from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_schema.user_schemas import UserCreate, UserResponse, UserUpdate
from src.core.domain.user.user_model.user_role import UserRole
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse


@pytest.fixture
def mock_repos():
    """Cria um mock das repositories com contexto assíncrono."""
    repos = AsyncMock()
    repos.users = AsyncMock()
    repos.commit = AsyncMock()
    repos.__aenter__ = AsyncMock(return_value=repos)
    repos.__aexit__ = AsyncMock(return_value=None)
    return repos


@pytest.fixture
def mock_ldap_service():
    """Cria um mock do serviço LDAP."""
    ldap_service = MagicMock()
    return ldap_service


@pytest.fixture
def user_service(mock_repos, mock_ldap_service):
    """Cria uma instância do UserService com mocks."""
    return UserService(repos=mock_repos, ldap_service=mock_ldap_service)


@pytest.fixture
def sample_user_id():
    """Gera um UUID para testes."""
    return uuid.uuid4()


@pytest.fixture
def sample_user_data(sample_user_id):
    """Cria dados de exemplo para um usuário."""
    return {
        'id': sample_user_id,
        'name': 'João Silva',
        'email': 'joao@example.com',
        'active': True,
        'role': UserRole.researcher,
        'researcherProfile': None
    }


class TestUserServiceCreate:
    """Tests for user creation via UserService.create_user."""

    # -------------------------------------------------------------------------
    # Success — required fields only
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_required_fields_only(self, user_service, mock_repos, mock_ldap_service):
        """Creating a user with only the required fields (no researcherProfile) succeeds."""
        # Arrange
        user_create = UserCreate(
            name="Ana Costa",
            email="ana.costa@example.com",
            role=UserRole.researcher,
        )
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        # Act
        result = await user_service.create_user(user_create)

        # Assert
        assert result.name == "Ana Costa"
        assert result.email == "ana.costa@example.com"
        assert result.role == UserRole.researcher
        assert result.researcherProfile is None
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    # -------------------------------------------------------------------------
    # Success — all fields
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_all_fields(self, user_service, mock_repos, mock_ldap_service, sample_profile):
        """Creating a user with all fields, including a researcherProfile, succeeds."""
        # Arrange
        user_create = UserCreate(
            name="Carlos Mendes",
            email="carlos.mendes@example.com",
            role=UserRole.researcher,
            researcherProfile=sample_profile,
        )
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        # Act
        result = await user_service.create_user(user_create)

        # Assert
        assert result.name == "Carlos Mendes"
        assert result.email == "carlos.mendes@example.com"
        assert result.role == UserRole.researcher
        assert result.researcherProfile is not None
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    # -------------------------------------------------------------------------
    # Success — roles
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_with_researcher_role(self, user_service, mock_repos, mock_ldap_service):
        """A user can be created with the researcher role."""
        # Arrange
        user_create = UserCreate(
            name="Researcher User",
            email="researcher@example.com",
            role=UserRole.researcher,
        )
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        # Act
        result = await user_service.create_user(user_create)

        # Assert
        assert result.role == UserRole.researcher
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_with_admin_role(self, user_service, mock_repos, mock_ldap_service):
        """A user can be created with the admin role."""
        # Arrange
        user_create = UserCreate(
            name="Admin User",
            email="admin@example.com",
            role=UserRole.admin,
        )
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        # Act
        result = await user_service.create_user(user_create)

        # Assert
        assert result.role == UserRole.admin
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    # -------------------------------------------------------------------------
    # Active flag
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_is_active_on_creation(self, user_service, mock_repos, mock_ldap_service):
        """A newly created user must always be active regardless of role."""
        # Arrange
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        for role in (UserRole.researcher, UserRole.admin):
            mock_repos.reset_mock()
            user_create = UserCreate(
                name="Some User",
                email=f"{role.value}@example.com",
                role=role,
            )

            # Act
            result = await user_service.create_user(user_create)

            # Assert
            assert result.active is True, f"Expected active=True for role {role}"

    # -------------------------------------------------------------------------
    # UUID generation
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_generates_unique_ids(self, user_service, mock_repos, mock_ldap_service):
        """Each created user receives a distinct UUID."""
        # Arrange
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        user_create_1 = UserCreate(name="User One", email="user1@example.com", role=UserRole.researcher)
        user_create_2 = UserCreate(name="User Two", email="user2@example.com", role=UserRole.researcher)

        # Act
        result_1 = await user_service.create_user(user_create_1)
        result_2 = await user_service.create_user(user_create_2)

        # Assert
        assert result_1.id != result_2.id

    # -------------------------------------------------------------------------
    # LDAP validation
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_email_not_in_ldap_raises_400(self, user_service, mock_repos, mock_ldap_service):
        """Creating a user whose email is not registered in LDAP raises HTTP 400."""
        # Arrange
        user_create = UserCreate(
            name="João Silva",
            email="not-in-ldap@example.com",
            role=UserRole.researcher,
        )
        mock_ldap_service.exists_with_email.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(user_create)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email not registered on LDAP" in exc_info.value.detail
        mock_repos.users.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_ldap_check_uses_exact_email(self, user_service, mock_repos, mock_ldap_service):
        """The LDAP check is called with the exact email provided in the request."""
        # Arrange
        email = "specific.email@example.com"
        user_create = UserCreate(name="Test User", email=email, role=UserRole.researcher)
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        # Act
        await user_service.create_user(user_create)

        # Assert
        mock_ldap_service.exists_with_email.assert_called_once_with(email)

    @pytest.mark.asyncio
    async def test_create_user_ldap_failure_prevents_db_lookup(self, user_service, mock_repos, mock_ldap_service):
        """When LDAP validation fails, the database is never queried for duplicate emails."""
        # Arrange
        user_create = UserCreate(
            name="João Silva",
            email="not-in-ldap@example.com",
            role=UserRole.researcher,
        )
        mock_ldap_service.exists_with_email.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException):
            await user_service.create_user(user_create)

        mock_repos.users.get_by_email.assert_not_called()

    # -------------------------------------------------------------------------
    # Duplicate email
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_400(self, user_service, mock_repos, mock_ldap_service, user_data):
        """Creating a user with an email already in the system raises HTTP 400."""
        # Arrange
        user_create = UserCreate(
            name="Different Name",          # same email, different name — still rejected
            email=user_data["email"],
            role=UserRole.researcher,
        )
        existing_user = User(**user_data)
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = existing_user

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(user_create)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already exists" in exc_info.value.detail
        mock_repos.users.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_same_name_raises_400(
            self, user_service, mock_repos, mock_ldap_service, user_data
    ):
        """Duplicate email is rejected even when the name is also identical."""
        # Arrange
        user_create = UserCreate(
            name=user_data["name"],         # same name AND same email
            email=user_data["email"],
            role=UserRole.researcher,
        )
        existing_user = User(**user_data)
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = existing_user

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(user_create)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already exists" in exc_info.value.detail

    # -------------------------------------------------------------------------
    # Duplicate name (allowed)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_duplicate_name_is_allowed(
            self, user_service, mock_repos, mock_ldap_service, user_data
    ):
        """Two users may share the same name as long as their emails differ."""
        # Arrange
        user_create = UserCreate(
            name=user_data["name"],         # same name as an existing user
            email="different@example.com",  # different email — no conflict
            role=UserRole.researcher,
        )
        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None  # no conflict on the new email

        # Act
        result = await user_service.create_user(user_create)

        # Assert
        assert result.name == user_data["name"]
        assert result.email == "different@example.com"
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    # -------------------------------------------------------------------------
    # Persistence order
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_user_save_called_before_commit(self, user_service, mock_repos, mock_ldap_service):
        """save() must be called before commit() — incorrect order would leave data uncommitted."""
        # Arrange
        call_order = []
        mock_repos.users.save.side_effect = lambda _: call_order.append("save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        mock_ldap_service.exists_with_email.return_value = True
        mock_repos.users.get_by_email.return_value = None

        user_create = UserCreate(name="Test User", email="test@example.com", role=UserRole.researcher)

        # Act
        await user_service.create_user(user_create)

        # Assert
        assert call_order == ["save", "commit"]

# =============================================================================
# delete_user
# =============================================================================

class TestUserServiceDelete:
    """Tests for user deletion via UserService.delete_user."""

    # -------------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_repos, sample_user):
        """Deleting an existing user succeeds and calls delete + commit."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user

        # Act
        await user_service.delete_user(sample_user.id)

        # Assert
        mock_repos.users.delete.assert_called_once_with(sample_user.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_removes_linked_researcher_profile(
            self, user_service, mock_repos, sample_user, sample_profile
    ):
        """When a user has a researcherProfile, it must be deleted along with the user."""
        # Arrange
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        # Act
        await user_service.delete_user(sample_user.id)

        # Assert — the profile and its metrics are deleted before the user
        mock_repos.profiles.delete.assert_called_once_with(sample_profile.id)
        mock_repos.users.delete.assert_called_once_with(sample_user.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_removes_linked_metrics(
            self, user_service, mock_repos, sample_user, sample_profile, sample_metric
    ):
        """All metrics linked to the user's researcherProfile are deleted."""
        # Arrange
        sample_profile.metrics = [sample_metric]
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        # Act
        await user_service.delete_user(sample_user.id)

        # Assert
        mock_repos.metrics.delete.assert_called_once_with(sample_metric.id)
        mock_repos.profiles.delete.assert_called_once_with(sample_profile.id)
        mock_repos.users.delete.assert_called_once_with(sample_user.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_removes_multiple_metrics(
            self, user_service, mock_repos, sample_user, sample_profile, metric_data
    ):
        """All metrics (not just the first) are deleted when there are several."""
        # Arrange
        from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric

        metric_a = ResearcherMetric(**{**metric_data, "id": uuid.uuid4()})
        metric_b = ResearcherMetric(**{**metric_data, "id": uuid.uuid4()})
        sample_profile.metrics = [metric_a, metric_b]
        sample_user.researcherProfile = sample_profile
        mock_repos.users.get_by_id.return_value = sample_user

        # Act
        await user_service.delete_user(sample_user.id)

        # Assert — delete called once per metric
        assert mock_repos.metrics.delete.call_count == 2
        deleted_ids = {call.args[0] for call in mock_repos.metrics.delete.call_args_list}
        assert deleted_ids == {metric_a.id, metric_b.id}

    @pytest.mark.asyncio
    async def test_delete_user_without_profile_skips_profile_and_metric_deletion(
            self, user_service, mock_repos, sample_user
    ):
        """Deleting a user without a researcherProfile does not attempt to delete profiles or metrics."""
        # Arrange
        sample_user.researcherProfile = None
        mock_repos.users.get_by_id.return_value = sample_user

        # Act
        await user_service.delete_user(sample_user.id)

        # Assert
        mock_repos.profiles.delete.assert_not_called()
        mock_repos.metrics.delete.assert_not_called()
        mock_repos.users.delete.assert_called_once_with(sample_user.id)
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_delete_called_before_commit(self, user_service, mock_repos, sample_user):
        """delete() must be called before commit()."""
        # Arrange
        call_order = []
        mock_repos.users.get_by_id.return_value = sample_user
        mock_repos.users.delete.side_effect = lambda _: call_order.append("delete")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")

        # Act
        await user_service.delete_user(sample_user.id)

        # Assert
        assert call_order == ["delete", "commit"]

    # -------------------------------------------------------------------------
    # Not found
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_user_not_found_raises_404(self, user_service, mock_repos):
        """Attempting to delete a non-existent user raises HTTP 404."""
        # Arrange
        mock_repos.users.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user(uuid.uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail
        mock_repos.users.delete.assert_not_called()
        mock_repos.commit.assert_not_called()


# =============================================================================
# update_user
# =============================================================================

class TestUserServiceUpdate:
    """Tests for user updates via UserService.update_user."""

    # -------------------------------------------------------------------------
    # Success — allowed fields
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_user_name_success(self, user_service, mock_repos, mock_ldap_service, sample_user):
        """A user's name can be updated successfully."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        user_update = UserUpdate(name="New Name")

        # Act
        result = await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert result.name == "New Name"
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_email_success(self, user_service, mock_repos, mock_ldap_service, sample_user):
        """A user's email can be updated when the new email exists in LDAP."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        mock_ldap_service.exists_with_email.return_value = True
        user_update = UserUpdate(email="new.email@example.com")

        # Act
        result = await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert result.email == "new.email@example.com"
        mock_ldap_service.exists_with_email.assert_called_once_with("new.email@example.com")
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_role_success(self, user_service, mock_repos, mock_ldap_service, sample_user):
        """A user's role can be updated to admin."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        user_update = UserUpdate(role=UserRole.admin)

        # Act
        result = await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert result.role == UserRole.admin
        mock_repos.users.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_active_flag_success(self, user_service, mock_repos, mock_ldap_service, sample_user):
        """An admin can deactivate a user by setting active=False."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        user_update = UserUpdate(active=False)

        # Act
        result = await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert result.active is False
        mock_repos.users.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_multiple_fields_at_once(
            self, user_service, mock_repos, mock_ldap_service, sample_user
    ):
        """Multiple allowed fields can be updated in a single call."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        mock_ldap_service.exists_with_email.return_value = True
        user_update = UserUpdate(name="Updated Name", email="updated@example.com", role=UserRole.admin)

        # Act
        result = await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert result.name == "Updated Name"
        assert result.email == "updated@example.com"
        assert result.role == UserRole.admin
        mock_repos.users.save.assert_called_once()
        mock_repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_save_called_before_commit(
            self, user_service, mock_repos, mock_ldap_service, sample_user
    ):
        """save() must be called before commit() during an update."""
        # Arrange
        call_order = []
        mock_repos.users.get_by_id.return_value = sample_user
        mock_repos.users.save.side_effect = lambda _: call_order.append("save")
        mock_repos.commit.side_effect = lambda: call_order.append("commit")
        user_update = UserUpdate(name="Order Test")

        # Act
        await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert call_order == ["save", "commit"]

    # -------------------------------------------------------------------------
    # LDAP validation on email update
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_user_email_not_in_ldap_raises_400(
            self, user_service, mock_repos, mock_ldap_service, sample_user
    ):
        """Updating to an email not registered in LDAP raises HTTP 400."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        mock_ldap_service.exists_with_email.return_value = False
        user_update = UserUpdate(email="not-in-ldap@example.com")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user(sample_user.id, user_update)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email not registered on LDAP" in exc_info.value.detail
        mock_repos.users.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_no_email_change_skips_ldap_check(
            self, user_service, mock_repos, mock_ldap_service, sample_user
    ):
        """When email is not being updated, the LDAP service is never called."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user
        user_update = UserUpdate(name="Only Name Change")

        # Act
        await user_service.update_user(sample_user.id, user_update)

        # Assert
        mock_ldap_service.exists_with_email.assert_not_called()

    # -------------------------------------------------------------------------
    # Not found
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises_404(self, user_service, mock_repos, mock_ldap_service):
        """Attempting to update a non-existent user raises HTTP 404."""
        # Arrange
        mock_repos.users.get_by_id.return_value = None
        user_update = UserUpdate(name="Ghost")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user(uuid.uuid4(), user_update)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail
        mock_repos.users.save.assert_not_called()
        mock_repos.commit.assert_not_called()

    # -------------------------------------------------------------------------
    # Own profile / admin authorisation
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_own_profile_as_researcher(
            self, user_service, mock_repos, mock_ldap_service, sample_user
    ):
        """A researcher updating their own profile (same user_id) succeeds for allowed fields."""
        # Arrange — the router would have verified that the caller IS sample_user
        mock_repos.users.get_by_id.return_value = sample_user
        user_update = UserUpdate(name="Self Update")

        # Act
        result = await user_service.update_user(sample_user.id, user_update)

        # Assert
        assert result.name == "Self Update"
        mock_repos.users.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_any_user_as_admin(
            self, user_service, mock_repos, mock_ldap_service, sample_user
    ):
        """An admin can update any user — the service receives any user_id and applies the update."""
        # Arrange — the router has already confirmed the caller is an admin
        target_user = User(
            id=uuid.uuid4(),
            name="Target User",
            email="target@example.com",
            active=True,
            role=UserRole.researcher,
            researcherProfile=None,
        )
        mock_repos.users.get_by_id.return_value = target_user
        user_update = UserUpdate(role=UserRole.admin)

        # Act
        result = await user_service.update_user(target_user.id, user_update)

        # Assert
        assert result.role == UserRole.admin
        mock_repos.users.save.assert_called_once()


# =============================================================================
# get_user_by_id
# =============================================================================

class TestUserServiceGetById:
    """Tests for user retrieval via UserService.get_user_by_id."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_repos, sample_user):
        """Fetching an existing user by ID returns the correct UserResponse."""
        # Arrange
        mock_repos.users.get_by_id.return_value = sample_user

        # Act
        result = await user_service.get_user_by_id(sample_user.id)

        # Assert
        assert result.id == sample_user.id
        assert result.name == sample_user.name
        assert result.email == sample_user.email
        assert result.role == sample_user.role
        assert result.active == sample_user.active
        mock_repos.users.get_by_id.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found_raises_404(self, user_service, mock_repos):
        """Fetching a non-existent user raises HTTP 404."""
        # Arrange
        mock_repos.users.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_by_id(uuid.uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail


# =============================================================================
# fetch_users
# =============================================================================

class TestUserServiceFetchUsers:
    """Tests for paginated user listing via UserService.fetch_users."""

    # -------------------------------------------------------------------------
    # Success — pagination shape
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fetch_users_returns_correct_items(
            self, user_service, mock_repos, sample_user, pagination_params
    ):
        """The items in the response correspond to the users returned by the repository."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_user]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.users.fetch.return_value = raw_result

        # Act
        result = await user_service.fetch_users(pagination_params)

        # Assert
        assert len(result.items) == 1
        assert result.items[0].id == sample_user.id
        assert result.items[0].email == sample_user.email

    @pytest.mark.asyncio
    async def test_fetch_users_returns_correct_pagination_metadata(
            self, user_service, mock_repos, sample_user, pagination_params
    ):
        """total, page, page_size, and pages are forwarded accurately from the repository result."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = [sample_user]
        raw_result.total = 42
        raw_result.page = 3
        raw_result.page_size = 10
        raw_result.pages = 5
        mock_repos.users.fetch.return_value = raw_result

        # Act
        result = await user_service.fetch_users(pagination_params)

        # Assert
        assert result.total == 42
        assert result.page == 3
        assert result.page_size == 10
        assert result.pages == 5

    @pytest.mark.asyncio
    async def test_fetch_users_empty_list(self, user_service, mock_repos, pagination_params):
        """When there are no users, items is empty and total is 0."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.users.fetch.return_value = raw_result

        # Act
        result = await user_service.fetch_users(pagination_params)

        # Assert
        assert result.items == []
        assert result.total == 0
        assert result.pages == 0

    @pytest.mark.asyncio
    async def test_fetch_users_multiple_items(self, user_service, mock_repos, user_data, pagination_params):
        """All users in the repository result appear in the response items."""
        # Arrange
        user_a = User(**user_data)
        user_b = User(**{**user_data, "id": uuid.uuid4(), "email": "b@example.com"})
        user_c = User(**{**user_data, "id": uuid.uuid4(), "email": "c@example.com"})

        raw_result = MagicMock()
        raw_result.items = [user_a, user_b, user_c]
        raw_result.total = 3
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.users.fetch.return_value = raw_result

        # Act
        result = await user_service.fetch_users(pagination_params)

        # Assert
        assert len(result.items) == 3
        result_emails = {u.email for u in result.items}
        assert result_emails == {user_a.email, user_b.email, user_c.email}

    @pytest.mark.asyncio
    async def test_fetch_users_returns_paginated_response_type(
            self, user_service, mock_repos, pagination_params
    ):
        """The return type is PaginatedResponse."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.users.fetch.return_value = raw_result

        # Act
        result = await user_service.fetch_users(pagination_params)

        # Assert
        assert isinstance(result, PaginatedResponse)

    # -------------------------------------------------------------------------
    # exclude_names filter
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fetch_users_passes_exclude_names_to_repo(
            self, user_service, mock_repos, pagination_params
    ):
        """exclude_names is forwarded to the repository unchanged."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.users.fetch.return_value = raw_result
        excluded = ["System", "Bot"]

        # Act
        await user_service.fetch_users(pagination_params, exclude_names=excluded)

        # Assert
        mock_repos.users.fetch.assert_called_once_with(pagination_params, excluded)

    @pytest.mark.asyncio
    async def test_fetch_users_default_exclude_names_is_none(
            self, user_service, mock_repos, pagination_params
    ):
        """When exclude_names is not provided, None is passed to the repository."""
        # Arrange
        raw_result = MagicMock()
        raw_result.items = []
        raw_result.total = 0
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 0
        mock_repos.users.fetch.return_value = raw_result

        # Act
        await user_service.fetch_users(pagination_params)

        # Assert
        mock_repos.users.fetch.assert_called_once_with(pagination_params, None)

    # -------------------------------------------------------------------------
    # Items are UserResponse, not raw User objects
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fetch_users_items_are_validated_responses(
            self, user_service, mock_repos, sample_user, pagination_params
    ):
        """Each item in the response is a validated UserResponse, not a raw User domain object."""
        # Arrange
        from src.core.domain.user.user_schema.user_schemas import UserResponse
        raw_result = MagicMock()
        raw_result.items = [sample_user]
        raw_result.total = 1
        raw_result.page = 1
        raw_result.page_size = 20
        raw_result.pages = 1
        mock_repos.users.fetch.return_value = raw_result

        # Act
        result = await user_service.fetch_users(pagination_params)

        # Assert
        assert all(isinstance(item, UserResponse) for item in result.items)

