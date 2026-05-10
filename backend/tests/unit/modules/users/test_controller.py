import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.user.schema.user_schemas import UserResponse
from src.modules.user.controller.user_controller import router, get_user_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user_response(**kwargs) -> UserResponse:
    return UserResponse(
        name=kwargs.get("name", "Alice"),
        email=kwargs.get("email", "alice@example.com"),
        active=kwargs.get("active", True),
        role=kwargs.get("role", 1),
        researcherProfile=kwargs.get("researcherProfile", None),
    )


def make_payload(**kwargs) -> dict:
    return {
        "name": kwargs.get("name", "Alice"),
        "email": kwargs.get("email", "alice@example.com"),
        "role": kwargs.get("role", "researcher"),
        "researcherProfile": kwargs.get("researcherProfile", None),
    }


def build_app(service_mock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_service] = lambda: service_mock

    from src.modules.auth.auth import require_admin
    app.dependency_overrides[require_admin] = lambda: MagicMock()

    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /users/create_user
# ---------------------------------------------------------------------------

class TestCreateUserEndpoint:

    def test_create_user_returns_201(self):
        response_data = make_user_response()
        service = MagicMock()
        service.create_user = AsyncMock(return_value=response_data)
        client = build_app(service)

        response = client.post("/users/create_user", json=make_payload())

        assert response.status_code == 201
        service.create_user.assert_called_once()

    def test_create_user_duplicate_email_returns_400(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.create_user = AsyncMock(
            side_effect=HTTPException(status_code=400, detail="Email already exists")
        )
        client = build_app(service)

        response = client.post("/users/create_user", json=make_payload())

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already exists"

    def test_create_user_invalid_payload_returns_422(self):
        service = MagicMock()
        client = build_app(service)

        response = client.post("/users/create_user", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}
# ---------------------------------------------------------------------------

class TestDeleteUserEndpoint:

    def test_delete_user_returns_204(self):
        service = MagicMock()
        service.delete_user = AsyncMock(return_value=None)
        client = build_app(service)

        response = client.delete(f"/users/{uuid.uuid4()}")

        assert response.status_code == 204
        service.delete_user.assert_called_once()

    def test_delete_user_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.delete_user = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="User not found")
        )
        client = build_app(service)

        response = client.delete(f"/users/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_delete_user_invalid_uuid_returns_422(self):
        service = MagicMock()
        client = build_app(service)

        response = client.delete("/users/not-a-uuid")

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}
# ---------------------------------------------------------------------------

class TestUpdateUserEndpoint:

    def test_update_user_returns_200(self):
        updated = make_user_response(name="Bob")
        service = MagicMock()
        service.update_user = AsyncMock(return_value=updated)
        client = build_app(service)

        response = client.patch(f"/users/{uuid.uuid4()}", json={"name": "Bob"})

        assert response.status_code == 200
        assert response.json()["name"] == "Bob"

    def test_update_user_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.update_user = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="User not found")
        )
        client = build_app(service)

        response = client.patch(f"/users/{uuid.uuid4()}", json={"name": "Bob"})

        assert response.status_code == 404

    def test_update_user_invalid_uuid_returns_422(self):
        service = MagicMock()
        client = build_app(service)

        response = client.patch("/users/not-a-uuid", json={"name": "Bob"})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/by-id/{user_id}
# ---------------------------------------------------------------------------

class TestGetUserByIdEndpoint:

    def test_get_user_by_id_returns_200(self):
        user = make_user_response()
        service = MagicMock()
        service.get_user_by_id = AsyncMock(return_value=user)
        client = build_app(service)

        response = client.get(f"/users/by-id/{user.id}")

        assert response.status_code == 200
        assert response.json()["email"] == user.email

    def test_get_user_by_id_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.get_user_by_id = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="User not found")
        )
        client = build_app(service)

        response = client.get(f"/users/by-id/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_get_user_by_id_invalid_uuid_returns_422(self):
        service = MagicMock()
        client = build_app(service)

        response = client.get("/users/by-id/not-a-uuid")

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/by-email/{email}
# ---------------------------------------------------------------------------

class TestGetUserByEmailEndpoint:

    def test_get_user_by_email_returns_200(self):
        user = make_user_response()
        service = MagicMock()
        service.get_user_by_email = AsyncMock(return_value=user)
        client = build_app(service)

        response = client.get(f"/users/by-email/{user.email}")

        assert response.status_code == 200
        assert response.json()["email"] == user.email

    def test_get_user_by_email_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.get_user_by_email = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="User not found")
        )
        client = build_app(service)

        response = client.get("/users/by-email/nope@example.com")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /users/
# ---------------------------------------------------------------------------

class TestListUsersEndpoint:

    def test_list_users_returns_all(self):
        users = [make_user_response(), make_user_response()]
        service = MagicMock()
        service.list_users = AsyncMock(return_value=users)
        client = build_app(service)

        response = client.get("/users/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_users_returns_empty_list(self):
        service = MagicMock()
        service.list_users = AsyncMock(return_value=[])
        client = build_app(service)

        response = client.get("/users/")

        assert response.status_code == 200
        assert response.json() == []
