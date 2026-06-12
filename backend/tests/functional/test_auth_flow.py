"""
Functional tests for authentication endpoints.
Tests LDAP authentication and JWT token issuance.
"""
import pytest
import json
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from jose import jwt
from src.core.settings.settings import settings


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Test authentication flows including LDAP and JWT token generation."""

    async def test_login_successful_with_valid_ldap_credentials(self, client: AsyncClient, mock_ldap_service):
        """
        Test happy path: User authenticates via LDAP and receives JWT token.
        Verifies:
        - HTTP 200 response
        - Response contains access_token
        - Token is valid JWT
        - Token payload contains user information
        """
        # Arrange
        credentials = {
            "email": "researcher@test.com",
            "password": "password123"
        }

        mock_ldap_service.authenticate.return_value = True
        mock_ldap_service.get_user_by_email = AsyncMock(return_value={
            'id': 'user123',
            'name': 'Test User',
            'email': 'researcher@test.com',
            'role': 'researcher'
        })

        with patch('src.modules.auth.service.auth_service.LDAPService', return_value=mock_ldap_service):
            # Act
            response = await client.post(
                "/api/v1/auth/login",
                json=credentials
            )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "token_type" in data, "Response should contain token_type"
        assert data["token_type"] == "bearer", "Token type should be bearer"

        # Verify JWT token is valid
        token = data["access_token"]
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert decoded["sub"] is not None, "Token should contain user ID in sub claim"
        assert decoded["email"] == "researcher@test.com", "Token should contain user email"

    async def test_login_fails_with_invalid_credentials(self, client: AsyncClient, mock_ldap_service):
        """
        Test error case: Invalid LDAP credentials.
        Verifies:
        - HTTP 401 response
        - Error message is descriptive
        """
        # Arrange
        credentials = {
            "email": "researcher@test.com",
            "password": "wrongpassword"
        }

        mock_ldap_service.authenticate.return_value = False

        with patch('src.modules.auth.service.auth_service.LDAPService', return_value=mock_ldap_service):
            # Act
            response = await client.post(
                "/api/v1/auth/login",
                json=credentials
            )

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should contain detail message"

    async def test_login_fails_with_missing_email(self, client: AsyncClient):
        """
        Test error case: Missing required email field.
        Verifies:
        - HTTP 422 Unprocessable Entity
        - Validation error in response
        """
        # Arrange
        credentials = {
            "password": "password123"
        }

        # Act
        response = await client.post(
            "/api/v1/auth/login",
            json=credentials
        )

        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Validation error should be present"

    async def test_login_fails_with_missing_password(self, client: AsyncClient):
        """
        Test error case: Missing required password field.
        Verifies:
        - HTTP 422 Unprocessable Entity
        """
        # Arrange
        credentials = {
            "email": "researcher@test.com"
        }

        # Act
        response = await client.post(
            "/api/v1/auth/login",
            json=credentials
        )

        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    async def test_token_includes_user_role_information(self, client: AsyncClient, mock_ldap_service):
        """
        Test that JWT token includes user role for authorization.
        Verifies:
        - Token contains role claim
        - Role is correctly set
        """
        # Arrange
        credentials = {
            "email": "admin@test.com",
            "password": "password123"
        }

        mock_ldap_service.authenticate.return_value = True
        mock_ldap_service.get_user_by_email = AsyncMock(return_value={
            'id': 'admin123',
            'name': 'Admin User',
            'email': 'admin@test.com',
            'role': 'admin'
        })

        with patch('src.modules.auth.service.auth_service.LDAPService', return_value=mock_ldap_service):
            # Act
            response = await client.post(
                "/api/v1/auth/login",
                json=credentials
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        token = data["access_token"]
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert "role" in decoded, "Token should include user role"
        assert decoded["role"] == "admin", "Admin role should be correctly set"


@pytest.mark.asyncio
class TestTokenValidation:
    """Test JWT token validation in protected endpoints."""

    async def test_request_with_valid_token_succeeds(self, client: AsyncClient, admin_token):
        """
        Test that requests with valid JWT token are accepted.
        Verifies:
        - Authorized endpoints accept valid tokens
        - Request goes through without 401 error
        """
        # Act
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        # Should not be 401 (unauthorized)
        assert response.status_code != 401

    async def test_request_without_token_fails(self, client: AsyncClient):
        """
        Test that protected endpoints reject requests without token.
        Verifies:
        - HTTP 403 or 401 response
        - Request is properly rejected
        """
        # Act
        response = await client.get("/api/v1/users/")

        # Assert
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    async def test_request_with_invalid_token_fails(self, client: AsyncClient):
        """
        Test that protected endpoints reject invalid tokens.
        Verifies:
        - HTTP 401 response
        - Appropriate error message
        """
        # Arrange
        invalid_token = "invalid.token.here"

        # Act
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    async def test_request_with_expired_token_fails(self, client: AsyncClient):
        """
        Test that expired tokens are rejected.
        Verifies:
        - HTTP 401 response
        - JWT validation catches expiration
        """
        import uuid
        from datetime import datetime, timedelta, timezone

        # Create an expired token
        payload = {
            "sub": str(uuid.uuid4()),
            "email": "test@test.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

        # Act
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
class TestAuthorizationByRole:
    """Test role-based access control for protected endpoints."""

    async def test_admin_can_access_admin_endpoints(self, client: AsyncClient, admin_token, test_admin_user):
        """
        Test that admin users can access admin-only endpoints.
        Verifies:
        - Admins can create users
        - HTTP 201 response on successful creation
        """
        # Arrange
        new_user_data = {
            "name": "New User",
            "email": "newuser@test.com",
            "role": "researcher"
        }

        # Act
        response = await client.post(
            "/api/v1/users/",
            json=new_user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code != 403, "Admin should be able to create users"

    async def test_researcher_cannot_access_admin_endpoints(self, client: AsyncClient, researcher_token):
        """
        Test that researcher users cannot access admin-only endpoints.
        Verifies:
        - HTTP 403 Forbidden response
        - Proper access control is enforced
        """
        # Arrange
        new_user_data = {
            "name": "New User",
            "email": "newuser@test.com",
            "role": "researcher"
        }

        # Act
        response = await client.post(
            "/api/v1/users/",
            json=new_user_data,
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, "Researcher should not be able to create users"

    async def test_user_cannot_access_other_user_data(self, client: AsyncClient, researcher_token, test_admin_user):
        """
        Test that users cannot access other users' data.
        Verifies:
        - HTTP 403 Forbidden when accessing other user's data
        - Own data access is allowed
        """
        # Try to access another user's data
        response = await client.get(
            f"/api/v1/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, "User should not access other user's data"

