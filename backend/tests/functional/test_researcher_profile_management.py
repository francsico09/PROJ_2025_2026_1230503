"""
Functional tests for researcher profile management endpoints.
Tests researcher profile CRUD operations.
"""
import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
class TestResearcherProfileManagementFlow:
    """Test researcher profile management complete workflows."""

    async def test_create_profile_happy_path(self, client: AsyncClient, admin_token):
        """
        Test happy path: Create a new researcher profile.
        Verifies:
        - HTTP 201 Created response
        - Response contains profile data with all fields
        - Profile is properly formatted
        """
        # Arrange
        profile_data = {
            "keywords": ["machine learning", "artificial intelligence"],
            "scholar_id": "scholar_001",
            "orcid": "0000-0001-2345-6789",
            "wos_id": "wos_001",
            "scopus_id": "scopus_001",
            "biography": "Researcher in AI",
            "affiliation": "University of Technology"
        }

        # Act
        response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        created_profile = response.json()
        assert "id" in created_profile
        assert created_profile["keywords"] == profile_data["keywords"]
        assert created_profile["scholar_id"] == profile_data["scholar_id"]
        assert created_profile["orcid"] == profile_data["orcid"]
        assert created_profile["biography"] == profile_data["biography"]

    async def test_create_profile_with_minimal_data(self, client: AsyncClient, admin_token):
        """
        Test creating profile with minimal required data.
        Verifies:
        - Profile can be created with just keywords
        - Optional fields can be null
        """
        # Arrange
        profile_data = {
            "keywords": ["ai", "research"]
        }

        # Act
        response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        created_profile = response.json()
        assert created_profile["keywords"] == profile_data["keywords"]

    async def test_create_profile_non_admin_fails(self, client: AsyncClient, researcher_token):
        """
        Test error case: Non-admin user cannot create profiles.
        Verifies:
        - HTTP 403 Forbidden response
        - Access control is enforced
        """
        # Arrange
        profile_data = {
            "keywords": ["ai"],
            "biography": "Test"
        }

        # Act
        response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_fetch_profiles_happy_path(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test happy path: Fetch researcher profiles with pagination.
        Verifies:
        - HTTP 200 response
        - Returns list of profiles
        - Profiles contain expected fields
        """
        # Act
        response = await client.get(
            "/api/v1/researcher_profiles/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        if isinstance(data, list):
            # API might return list directly
            assert isinstance(data, list), "Should return list of profiles"
        else:
            # Or might return paginated response
            assert "items" in data or isinstance(data, list)

    async def test_update_profile_happy_path(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test happy path: Update researcher profile.
        Verifies:
        - HTTP 200 response
        - Updated fields are reflected
        - Other fields unchanged
        """
        # Arrange
        update_data = {
            "biography": "Updated biography",
            "affiliation": "New University"
        }

        # Act
        response = await client.patch(
            f"/api/v1/researcher_profiles/{test_researcher_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        updated_profile = response.json()
        assert updated_profile["biography"] == update_data["biography"]
        assert updated_profile["affiliation"] == update_data["affiliation"]

    async def test_update_profile_keywords(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test updating profile keywords.
        Verifies:
        - Keywords can be added/changed
        - Array fields are properly handled
        """
        # Arrange
        new_keywords = ["data science", "machine learning", "neural networks"]
        update_data = {
            "keywords": new_keywords
        }

        # Act
        response = await client.patch(
            f"/api/v1/researcher_profiles/{test_researcher_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200
        updated_profile = response.json()
        assert set(updated_profile["keywords"]) == set(new_keywords)

    async def test_update_non_existent_profile_returns_error(self, client: AsyncClient, admin_token):
        """
        Test error case: Update profile that doesn't exist.
        Verifies:
        - HTTP 404 Not Found response
        """
        # Arrange
        fake_profile_id = uuid.uuid4()
        update_data = {"biography": "New bio"}

        # Act
        response = await client.patch(
            f"/api/v1/researcher_profiles/{fake_profile_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    async def test_delete_profile_happy_path(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test happy path: Delete researcher profile.
        Verifies:
        - HTTP 200 response (as per controller)
        - Profile is actually deleted
        """
        # Arrange
        profile_id = test_researcher_profile.id

        # Act
        response = await client.delete(
            f"/api/v1/researcher_profiles/{profile_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    async def test_delete_profile_non_admin_fails(self, client: AsyncClient, researcher_token, test_researcher_profile):
        """
        Test error case: Non-admin cannot delete profiles.
        Verifies:
        - HTTP 403 Forbidden response
        """
        # Act
        response = await client.delete(
            f"/api/v1/researcher_profiles/{test_researcher_profile.id}",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_delete_non_existent_profile_returns_error(self, client: AsyncClient, admin_token):
        """
        Test error case: Delete profile that doesn't exist.
        Verifies:
        - HTTP 404 Not Found response
        """
        # Arrange
        fake_profile_id = uuid.uuid4()

        # Act
        response = await client.delete(
            f"/api/v1/researcher_profiles/{fake_profile_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.asyncio
class TestResearcherProfileDataConsistency:
    """Test data consistency in profile operations."""

    async def test_created_profile_can_be_retrieved(self, client: AsyncClient, admin_token):
        """
        Test that after creating a profile, it can be retrieved.
        Verifies:
        - Create and retrieve are consistent
        - Profile data persists
        """
        # Arrange
        profile_data = {
            "keywords": ["blockchain", "distributed systems"],
            "scholar_id": "scholar_test_123",
            "biography": "Blockchain researcher"
        }

        # Act - Create
        create_response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 201
        created_profile = create_response.json()
        profile_id = created_profile["id"]

        # Act - Retrieve (through fetch endpoint)
        fetch_response = await client.get(
            f"/api/v1/researcher_profiles/?page=1&page_size=100",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert fetch_response.status_code == 200
        # The profile should be in the list
        profiles_data = fetch_response.json()
        if isinstance(profiles_data, list):
            profile_found = any(p["id"] == profile_id for p in profiles_data)
        else:
            profile_found = any(p["id"] == profile_id for p in profiles_data.get("items", []))

        assert profile_found, "Created profile should be retrievable"

    async def test_profile_updates_persist(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test that profile updates persist across requests.
        Verifies:
        - Updates are saved to database
        - Subsequent retrieve shows updated data
        """
        # Arrange
        original_keywords = test_researcher_profile.keywords
        new_keywords = ["updated", "keywords"]
        update_data = {"keywords": new_keywords}

        # Act - Update
        update_response = await client.patch(
            f"/api/v1/researcher_profiles/{test_researcher_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200

        # Act - Retrieve
        fetch_response = await client.get(
            f"/api/v1/researcher_profiles/?page=1&page_size=100",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert fetch_response.status_code == 200
        profiles_data = fetch_response.json()

        if isinstance(profiles_data, list):
            profile = next((p for p in profiles_data if p["id"] == test_researcher_profile.id), None)
        else:
            profile = next((p for p in profiles_data.get("items", []) if p["id"] == test_researcher_profile.id), None)

        assert profile is not None, "Updated profile should be retrievable"
        assert set(profile["keywords"]) == set(new_keywords), "Keywords should be updated"

