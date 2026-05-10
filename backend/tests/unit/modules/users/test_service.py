import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.modules.user.model.role.user_role import UserRole
from src.modules.user.schema.user_schemas import UserCreate, UserUpdate
from src.modules.user.service.user_service import UserService


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def make_user(**kwargs):
    u = MagicMock()
    u.id = kwargs.get("id", uuid.uuid4())
    u.name = kwargs.get("name", "Alice")
    u.email = kwargs.get("email", "alice@example.com")
    u.active = kwargs.get("active", True)
    u.role = kwargs.get("role", "researcher")
    u.researcherProfile = kwargs.get("researcherProfile", None)
    return u


def make_repos(user=None, all_users=None, existing_email=None):
    repos = AsyncMock()
    repos.users.get_user_by_id = AsyncMock(return_value=user)
    repos.users.get_user_by_email = AsyncMock(return_value=existing_email)
    repos.users.get_all = AsyncMock(return_value=all_users or [])
    repos.users.save = AsyncMock()
    repos.users.delete = AsyncMock()
    repos.commit = AsyncMock()

    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=repos)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow, repos


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        uow, repos = make_repos(existing_email=None)
        service = UserService(uow)

        data = UserCreate(
            name="Alice",
            email="alice@example.com",
            role=UserRole.researcher,
            researcherProfile=None,
        )

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "src.modules.user.service.user_service.UserResponse.model_validate",
                lambda u: MagicMock(),
            )
            await service.create_user(data)

        repos.users.save.assert_called_once()
        repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_400(self):
        existing = make_user(email="alice@example.com")
        uow, _ = make_repos(existing_email=existing)
        service = UserService(uow)

        data = UserCreate(
            name="Alice",
            email="alice@example.com",
            role=UserRole.researcher,
            researcherProfile=None,
        )

        with pytest.raises(HTTPException) as exc:
            await service.create_user(data)

        assert exc.value.status_code == 400
        assert "Email already exists" in exc.value.detail


# delete_user
class TestDeleteUser:

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        user = make_user()
        uow, repos = make_repos(user=user)
        service = UserService(uow)

        await service.delete_user(user.id)

        repos.users.delete.assert_called_once_with(user.id)
        repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found_raises_404(self):
        uow, _ = make_repos(user=None)
        service = UserService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.delete_user(uuid.uuid4())

        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

class TestUpdateUser:

    @pytest.mark.asyncio
    async def test_update_user_success(self):
        user = make_user()
        uow, repos = make_repos(user=user)
        service = UserService(uow)

        data = UserUpdate(name="Bob")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "src.modules.user.service.user_service.UserResponse.model_validate",
                lambda u: MagicMock(),
            )
            await service.update_user(user.id, data)

        user.update.assert_called_once_with(data)
        repos.users.save.assert_called_once_with(user)
        repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises_404(self):
        uow, _ = make_repos(user=None)
        service = UserService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.update_user(uuid.uuid4(), UserUpdate())

        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

class TestGetUserById:

    @pytest.mark.asyncio
    async def test_returns_user(self):
        user = make_user()
        uow, repos = make_repos(user=user)
        service = UserService(uow)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "src.modules.user.service.user_service.UserResponse.model_validate",
                lambda u: MagicMock(),
            )
            await service.get_user_by_id(user.id)

        repos.users.get_user_by_id.assert_called_once_with(user.id)

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        uow, _ = make_repos(user=None)
        service = UserService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.get_user_by_id(uuid.uuid4())

        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail


# ---------------------------------------------------------------------------
# get_user_by_email
# ---------------------------------------------------------------------------

class TestGetUserByEmail:

    @pytest.mark.asyncio
    async def test_returns_user(self):
        user = make_user()
        uow, repos = make_repos(existing_email=user)
        service = UserService(uow)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "src.modules.user.service.user_service.UserResponse.model_validate",
                lambda u: MagicMock(),
            )
            await service.get_user_by_email(user.email)

        repos.users.get_user_by_email.assert_called_once_with(user.email)

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        uow, _ = make_repos(existing_email=None)
        service = UserService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.get_user_by_email("nope@example.com")

        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

class TestListUsers:

    @pytest.mark.asyncio
    async def test_returns_all_users(self):
        users = [make_user(), make_user()]
        uow, repos = make_repos(all_users=users)
        service = UserService(uow)

        result = await service.list_users()

        assert len(result) == 2
        repos.users.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        uow, repos = make_repos(all_users=[])
        service = UserService(uow)

        result = await service.list_users()

        assert result == []
