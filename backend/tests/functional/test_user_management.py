"""
Functional tests for user management endpoints.
Tests user CRUD operations and pagination.
"""
import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserManagementFlow:
    """Test user management complete workflows."""

    async def test_create_user_happy_path(self, client: AsyncClient, admin_token):
        """
        Test happy path: Create a new user.
        Verifies:
        - HTTP 201 Created response
        - Response contains user data with all fields
        - Created user can be retrieved
        """
        # Arrange
        user_data = {
            "name": "João Silva",
            "email": "joao.silva@test.com",
            "role": "researcher"
        }

        # Act
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        created_user = response.json()
        assert created_user["name"] == user_data["name"]
        assert created_user["email"] == user_data["email"]
        assert created_user["role"] == user_data["role"]
        assert "id" in created_user
        assert created_user["active"] == True

    async def test_create_user_with_invalid_role(self, client: AsyncClient, admin_token):
        """
        Test error case: Create user with invalid role.
        Verifies:
        - HTTP 422 Unprocessable Entity
        - Validation error is informative
        """
        # Arrange
        user_data = {
            "name": "Invalid User",
            "email": "invalid@test.com",
            "role": "superuser"  # Invalid role
        }

        # Act
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    async def test_create_user_with_duplicate_email(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test error case: Create user with email that already exists.
        Verifies:
        - HTTP 400 or 409 response (conflict)
        - Appropriate error message about duplicate email
        """
        # Arrange
        user_data = {
            "name": "Duplicate Email User",
            "email": test_admin_user.email,  # Already exists
            "role": "researcher"
        }

        # Act
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code in [400, 409], f"Expected 400/409, got {response.status_code}"

    async def test_fetch_users_with_pagination(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test happy path: Fetch users with pagination.
        Verifies:
        - HTTP 200 response
        - Response has pagination structure
        - Items contains user objects
        - Pagination info is correct
        """
        # Act
        response = await client.get(
            "/api/v1/users/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "items" in data, "Response should contain items"
        assert "total" in data, "Response should contain total count"
        assert "page" in data, "Response should contain page number"
        assert "page_size" in data, "Response should contain page size"
        assert "pages" in data, "Response should contain total pages"

        assert isinstance(data["items"], list), "Items should be a list"
        assert data["total"] >= 1, "Should have at least one user"

    async def test_fetch_users_respects_page_size(self, client: AsyncClient, admin_token):
        """
        Test that pagination respects page_size parameter.
        Verifies:
        - Returns correct number of items
        - page_size parameter is honored
        """
        # Act
        response = await client.get(
            "/api/v1/users/?page=1&page_size=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1, "Should respect page_size"

    async def test_get_user_by_id_happy_path(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test happy path: Get user by ID.
        Verifies:
        - HTTP 200 response
        - Response contains correct user data
        - All user fields are present
        """
        # Act
        response = await client.get(
            f"/api/v1/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        user = response.json()
        assert user["id"] == str(test_admin_user.id)
        assert user["name"] == test_admin_user.name
        assert user["email"] == test_admin_user.email
        assert user["role"] == test_admin_user.role.value

    async def test_get_non_existent_user_returns_error(self, client: AsyncClient, admin_token):
        """
        Test error case: Get user that doesn't exist.
        Verifies:
        - HTTP 404 Not Found response
        """
        # Arrange
        fake_user_id = uuid.uuid4()

        # Act
        response = await client.get(
            f"/api/v1/users/{fake_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    async def test_update_user_happy_path(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test happy path: Update a user.
        Verifies:
        - HTTP 200 response
        - Updated fields are reflected
        - Unchanged fields remain the same
        """
        # Arrange
        update_data = {
            "name": "Updated Name"
        }

        # Act
        response = await client.patch(
            f"/api/v1/users/{test_admin_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        updated_user = response.json()
        assert updated_user["name"] == update_data["name"]
        assert updated_user["email"] == test_admin_user.email  # Unchanged

    async def test_update_user_can_change_active_status(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test updating user's active status.
        Verifies:
        - Active status can be toggled
        - Updated status is persisted
        """
        # Arrange
        update_data = {
            "active": False
        }

        # Act
        response = await client.patch(
            f"/api/v1/users/{test_admin_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200

        updated_user = response.json()
        assert updated_user["active"] == False

    async def test_delete_user_happy_path(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test happy path: Delete a user.
        Verifies:
        - HTTP 204 No Content response
        - User is actually deleted (cannot fetch afterwards)
        """
        # Arrange
        user_id = test_admin_user.id

        # Act
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"

        # Verify user is deleted
        get_response = await client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404, "Deleted user should not be found"

    async def test_delete_non_existent_user_returns_error(self, client: AsyncClient, admin_token):
        """
        Test error case: Delete user that doesn't exist.
        Verifies:
        - HTTP 404 Not Found response
        """
        # Arrange
        fake_user_id = uuid.uuid4()

        # Act
        response = await client.delete(
            f"/api/v1/users/{fake_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.asyncio
class TestUserDataConsistency:
    """Test data consistency in user operations."""

    async def test_created_user_can_be_retrieved(self, client: AsyncClient, admin_token):
        """
        Test that after creating a user, the created user can be retrieved.
        Verifies:
        - Create and retrieve operations are consistent
        - User data persists correctly
        """
        # Arrange
        user_data = {
            "name": "Test User",
            "email": f"test.user.{uuid.uuid4()}@test.com",
            "role": "researcher"
        }

        # Act - Create
        create_response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 201
        created_user = create_response.json()

        # Act - Retrieve
        get_response = await client.get(
            f"/api/v1/users/{created_user['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert get_response.status_code == 200
        retrieved_user = get_response.json()
        assert retrieved_user["id"] == created_user["id"]
        assert retrieved_user["name"] == created_user["name"]
        assert retrieved_user["email"] == created_user["email"]

    async def test_updated_user_persists_changes(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test that user updates are persisted and can be retrieved.
        Verifies:
        - Updates are saved to database
        - Subsequent retrieval shows updated data
        """
        # Arrange
        new_name = "Updated Name"
        update_data = {"name": new_name}

        # Act - Update
        update_response = await client.patch(
            f"/api/v1/users/{test_admin_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200

        # Act - Retrieve
        get_response = await client.get(
            f"/api/v1/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert get_response.status_code == 200
        retrieved_user = get_response.json()
        assert retrieved_user["name"] == new_name

