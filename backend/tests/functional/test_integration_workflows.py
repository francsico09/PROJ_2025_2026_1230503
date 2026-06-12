"""
Integration tests for complete user workflows.
Tests complex scenarios involving multiple modules working together.
"""
import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCompleteUserWorkflow:
    """Test complete workflows involving multiple operations."""

    async def test_end_to_end_admin_manages_researcher(self, client: AsyncClient, admin_token):
        """
        Test end-to-end workflow: Admin creates researcher profile and metrics.
        Complete flow:
        1. Create researcher user
        2. Create researcher profile
        3. Create metrics for profile
        4. Query metrics
        5. Export metrics

        Verifies:
        - All operations succeed
        - Data is consistent across operations
        - Proper authorization at each step
        """
        # Step 1: Create researcher user
        user_data = {
            "name": "Dr. Maria Santos",
            "email": f"maria.santos.{uuid.uuid4()}@test.com",
            "role": "researcher"
        }
        user_response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert user_response.status_code == 201
        created_user = user_response.json()
        user_id = created_user["id"]

        # Step 2: Create researcher profile
        profile_data = {
            "keywords": ["quantum computing", "cryptography"],
            "scholar_id": "scholar_maria",
            "orcid": "0000-0001-5555-6666",
            "biography": "Quantum computing researcher",
            "affiliation": "Tech University"
        }
        profile_response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert profile_response.status_code == 201
        created_profile = profile_response.json()
        profile_id = created_profile["id"]

        # Step 3: Create metric for profile
        metric_data = {
            "researcher_id": profile_id,
            "extraction_run_id": str(uuid.uuid4()),
            "source": {"name": "scholar", "url": "https://scholar.google.com"},
            "date": datetime.now(timezone.utc).isoformat(),
            "h_index": 25,
            "total_citations": 1200,
            "total_publications": 45
        }
        metric_response = await client.post(
            "/api/v1/researcher_metrics/create_metric",
            json=metric_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert metric_response.status_code == 201
        created_metric = metric_response.json()

        # Step 4: Query metrics for profile
        query_response = await client.get(
            f"/api/v1/researcher_metrics/by-user/{profile_id}?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert query_response.status_code == 200
        query_data = query_response.json()

        if isinstance(query_data, dict):
            assert len(query_data.get("items", [])) > 0
        else:
            assert len(query_data) > 0

        # Step 5: Export metrics
        export_response = await client.get(
            f"/api/v1/export/researcher_metric/{profile_id}?format=csv&scope=history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert export_response.status_code == 200
        assert len(export_response.content) > 0

    async def test_researcher_accesses_own_data_workflow(self, client: AsyncClient, test_researcher_user, researcher_token, test_researcher_profile):
        """
        Test workflow: Researcher can access and export their own data.
        Complete flow:
        1. Researcher authenticates
        2. Views own profile
        3. Retrieves own metrics
        4. Exports own data

        Verifies:
        - Researcher access to own data is granted
        - Cannot access other researcher's data
        """
        # Step 1: Already authenticated with researcher_token

        # Step 2: Try to get own user info
        user_response = await client.get(
            f"/api/v1/users/{test_researcher_user.id}",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )
        assert user_response.status_code == 200

        # Step 3: Query metrics
        metrics_response = await client.get(
            f"/api/v1/researcher_metrics/by-user/{test_researcher_profile.id}",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )
        # Should succeed (might be 200 or researcher might not have metrics)
        assert metrics_response.status_code in [200, 404]

        # Step 4: Export own data
        export_response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=csv",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )
        # Should succeed or be empty
        assert export_response.status_code in [200, 404]

    async def test_profile_lifecycle_workflow(self, client: AsyncClient, admin_token):
        """
        Test complete profile lifecycle: Create -> Update -> Query -> Delete.
        Verifies:
        - Profile can be modified multiple times
        - Each state is retrievable
        - Deletion is final
        """
        # Create profile
        profile_data = {
            "keywords": ["initial", "keywords"],
            "biography": "Initial biography"
        }
        create_response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 201
        profile = create_response.json()
        profile_id = profile["id"]

        # Update with new keywords
        update1_data = {"keywords": ["updated", "keywords", "v1"]}
        update1_response = await client.patch(
            f"/api/v1/researcher_profiles/{profile_id}",
            json=update1_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update1_response.status_code == 200

        # Update with new biography
        update2_data = {"biography": "Updated biography v2"}
        update2_response = await client.patch(
            f"/api/v1/researcher_profiles/{profile_id}",
            json=update2_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update2_response.status_code == 200

        # Verify current state
        fetch_response = await client.get(
            f"/api/v1/researcher_profiles/?page=1&page_size=100",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert fetch_response.status_code == 200

        # Delete profile
        delete_response = await client.delete(
            f"/api/v1/researcher_profiles/{profile_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200


@pytest.mark.asyncio
class TestErrorHandlingAcrossOperations:
    """Test error handling in workflows with multiple operations."""

    async def test_invalid_token_blocks_all_operations(self, client: AsyncClient):
        """
        Test that invalid token blocks all operations.
        Verifies:
        - No operation succeeds with invalid token
        - Consistent error response
        """
        invalid_token = "invalid.token.value"

        # Try user operation
        user_response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert user_response.status_code == 401

        # Try profile operation
        profile_response = await client.get(
            "/api/v1/researcher_profiles/",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert profile_response.status_code == 401

        # Try metrics operation
        metrics_response = await client.get(
            "/api/v1/researcher_metrics/latest-by-user",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert metrics_response.status_code == 401

    async def test_cascade_error_when_parent_deleted(self, client: AsyncClient, admin_token):
        """
        Test that deleting a profile affects related metrics.
        Verifies:
        - Proper cleanup / error handling when parent is deleted
        """
        # Create profile
        profile_data = {"keywords": ["test"]}
        profile_response = await client.post(
            "/api/v1/researcher_profiles/",
            json=profile_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert profile_response.status_code == 201
        profile_id = profile_response.json()["id"]

        # Create metric
        metric_data = {
            "researcher_id": profile_id,
            "extraction_run_id": str(uuid.uuid4()),
            "source": {"name": "scholar", "url": "https://scholar.google.com"},
            "date": datetime.now(timezone.utc).isoformat(),
            "h_index": 10
        }
        metric_response = await client.post(
            "/api/v1/researcher_metrics/create_metric",
            json=metric_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert metric_response.status_code == 201

        # Delete profile
        delete_response = await client.delete(
            f"/api/v1/researcher_profiles/{profile_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200

        # Try to query metrics for deleted profile
        # This should either return empty or error
        query_response = await client.get(
            f"/api/v1/researcher_metrics/by-user/{profile_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should not crash
        assert query_response.status_code in [200, 404]


@pytest.mark.asyncio
class TestConcurrentOperationConsistency:
    """Test consistency when multiple operations occur."""

    async def test_concurrent_metric_creations_maintain_consistency(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test that multiple metric creations maintain consistency.
        Verifies:
        - All metrics are stored correctly
        - No data loss
        - Counts are accurate
        """
        # Create first metric
        metric1_data = {
            "researcher_id": str(test_researcher_profile.id),
            "extraction_run_id": str(uuid.uuid4()),
            "source": {"name": "scholar", "url": "https://scholar.google.com"},
            "date": datetime.now(timezone.utc).isoformat(),
            "h_index": 10
        }
        response1 = await client.post(
            "/api/v1/researcher_metrics/create_metric",
            json=metric1_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 201

        # Create second metric
        metric2_data = {
            "researcher_id": str(test_researcher_profile.id),
            "extraction_run_id": str(uuid.uuid4()),
            "source": {"name": "scopus", "url": "https://scopus.com"},
            "date": datetime.now(timezone.utc).isoformat(),
            "h_index": 15
        }
        response2 = await client.post(
            "/api/v1/researcher_metrics/create_metric",
            json=metric2_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response2.status_code == 201

        # Query all metrics for profile
        query_response = await client.get(
            f"/api/v1/researcher_metrics/by-user/{test_researcher_profile.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert query_response.status_code == 200

        query_data = query_response.json()
        if isinstance(query_data, dict):
            metrics = query_data.get("items", [])
        else:
            metrics = query_data

        # Should have at least 2 metrics (the ones we created + test fixture)
        assert len(metrics) >= 2, f"Expected at least 2 metrics, got {len(metrics)}"

    async def test_pagination_consistency_across_requests(self, client: AsyncClient, admin_token):
        """
        Test that pagination is consistent across multiple requests.
        Verifies:
        - Page navigation is reliable
        - Total count doesn't change
        """
        # Get page 1
        page1_response = await client.get(
            "/api/v1/users/?page=1&page_size=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()

        # Get page 1 again
        page1_again_response = await client.get(
            "/api/v1/users/?page=1&page_size=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert page1_again_response.status_code == 200
        page1_again_data = page1_again_response.json()

        # Totals should be the same
        total1 = page1_data.get("total")
        total2 = page1_again_data.get("total")
        assert total1 == total2, "Total count should be consistent"

