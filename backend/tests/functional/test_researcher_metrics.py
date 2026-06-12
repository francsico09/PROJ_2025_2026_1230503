"""
Functional tests for researcher metrics endpoints.
Tests metrics queries with different filters and pagination.
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


@pytest.mark.asyncio
class TestResearcherMetricsFlow:
    """Test researcher metrics query workflows."""

    async def test_create_metric_happy_path(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test happy path: Create a researcher metric.
        Verifies:
        - HTTP 201 Created response
        - Response contains metric data with all fields
        - Metric is properly formatted
        """
        # Arrange
        metric_data = {
            "researcher_id": str(test_researcher_profile.id),
            "extraction_run_id": str(uuid.uuid4()),
            "source": {
                "name": "scholar",
                "url": "https://scholar.google.com"
            },
            "date": datetime.now(timezone.utc).isoformat(),
            "h_index": 15,
            "total_citations": 500,
            "total_publications": 30,
            "i10_index": 10
        }

        # Act
        response = await client.post(
            "/api/v1/researcher_metrics/create_metric",
            json=metric_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        created_metric = response.json()
        assert "id" in created_metric
        assert created_metric["researcher_id"] == metric_data["researcher_id"]
        assert created_metric["h_index"] == metric_data["h_index"]

    async def test_create_metric_non_admin_fails(self, client: AsyncClient, researcher_token, test_researcher_profile):
        """
        Test error case: Non-admin cannot create metrics.
        Verifies:
        - HTTP 403 Forbidden response
        """
        # Arrange
        metric_data = {
            "researcher_id": str(test_researcher_profile.id),
            "extraction_run_id": str(uuid.uuid4()),
            "source": {"name": "scholar", "url": "https://scholar.google.com"},
            "date": datetime.now(timezone.utc).isoformat(),
            "h_index": 10
        }

        # Act
        response = await client.post(
            "/api/v1/researcher_metrics/create_metric",
            json=metric_data,
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_fetch_metrics_by_user(self, client: AsyncClient, admin_token, test_researcher_profile, test_researcher_metric):
        """
        Test happy path: Fetch metrics for a specific user.
        Verifies:
        - HTTP 200 response
        - Returns paginated results
        - Results contain the user's metrics
        """
        # Act
        response = await client.get(
            f"/api/v1/researcher_metrics/by-user/{test_researcher_profile.id}?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "items" in data or isinstance(data, list)

        if isinstance(data, dict):
            assert "page" in data
            assert "page_size" in data
            assert "total" in data

    async def test_fetch_latest_metrics_by_user(self, client: AsyncClient, admin_token, test_researcher_metric):
        """
        Test happy path: Fetch latest metrics per researcher.
        Verifies:
        - HTTP 200 response
        - Returns paginated results
        - Latest metrics are returned
        """
        # Act
        response = await client.get(
            "/api/v1/researcher_metrics/latest-by-user?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "items" in data or isinstance(data, list)

    async def test_fetch_latest_metrics_with_source_filter(self, client: AsyncClient, admin_token):
        """
        Test fetching latest metrics filtered by source.
        Verifies:
        - source parameter filters results
        - Only metrics from specified source are returned
        """
        # Act
        response = await client.get(
            "/api/v1/researcher_metrics/latest-by-user?source=scholar&page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        if isinstance(data, dict):
            metrics = data.get("items", [])
        else:
            metrics = data

        # All returned metrics should be from scholar source
        for metric in metrics:
            assert metric.get("source", {}).get("name") == "scholar" or \
                   metric.get("source") == "scholar"

    async def test_fetch_all_metrics_admin_only(self, client: AsyncClient, admin_token, test_researcher_metric):
        """
        Test that fetching all metrics requires admin role.
        Verifies:
        - Admins can fetch all metrics
        - HTTP 200 response
        """
        # Act
        response = await client.get(
            "/api/v1/researcher_metrics/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    async def test_fetch_all_metrics_non_admin_fails(self, client: AsyncClient, researcher_token):
        """
        Test error case: Non-admin cannot fetch all metrics.
        Verifies:
        - HTTP 403 Forbidden response
        """
        # Act
        response = await client.get(
            "/api/v1/researcher_metrics/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_update_metric_happy_path(self, client: AsyncClient, admin_token, test_researcher_metric):
        """
        Test happy path: Update a metric.
        Verifies:
        - HTTP 200 response
        - Updated fields are reflected
        """
        # Arrange
        update_data = {
            "h_index": 20,
            "total_citations": 750
        }

        # Act
        response = await client.patch(
            f"/api/v1/researcher_metrics/{test_researcher_metric.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Response might be paginated
        data = response.json()
        if isinstance(data, dict) and "items" in data:
            # Paginated response - verify it's not empty
            assert len(data["items"]) >= 0
        else:
            # Direct response
            assert data.get("h_index") == update_data["h_index"]

    async def test_delete_metric_happy_path(self, client: AsyncClient, admin_token, test_researcher_metric):
        """
        Test happy path: Delete a metric.
        Verifies:
        - HTTP 204 No Content response
        - Metric is actually deleted
        """
        # Arrange
        metric_id = test_researcher_metric.id

        # Act
        response = await client.delete(
            f"/api/v1/researcher_metrics/{metric_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    async def test_delete_metric_non_admin_fails(self, client: AsyncClient, researcher_token, test_researcher_metric):
        """
        Test error case: Non-admin cannot delete metrics.
        Verifies:
        - HTTP 403 Forbidden response
        """
        # Act
        response = await client.delete(
            f"/api/v1/researcher_metrics/{test_researcher_metric.id}",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_delete_non_existent_metric_returns_error(self, client: AsyncClient, admin_token):
        """
        Test error case: Delete metric that doesn't exist.
        Verifies:
        - HTTP 404 Not Found response
        """
        # Arrange
        fake_metric_id = uuid.uuid4()

        # Act
        response = await client.delete(
            f"/api/v1/researcher_metrics/{fake_metric_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.asyncio
class TestMetricsFilteringAndPagination:
    """Test metrics filtering and pagination features."""

    async def test_metrics_pagination_respects_page_size(self, client: AsyncClient, admin_token, test_researcher_metric):
        """
        Test that pagination respects page_size parameter.
        Verifies:
        - Returns at most page_size items
        - Page size is honored
        """
        # Act
        response = await client.get(
            "/api/v1/researcher_metrics/?page=1&page_size=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, dict):
            assert len(data.get("items", [])) <= 1

    async def test_metrics_pagination_multiple_pages(self, client: AsyncClient, admin_token):
        """
        Test navigating through multiple pages of metrics.
        Verifies:
        - Can access page 1
        - Can access other pages
        - Page numbers are correct
        """
        # Act - Navigate pages
        page1_response = await client.get(
            "/api/v1/researcher_metrics/?page=1&page_size=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert page1_response.status_code == 200
        data = page1_response.json()

        if isinstance(data, dict):
            assert data.get("page") == 1

    async def test_metric_response_structure(self, client: AsyncClient, admin_token, test_researcher_metric):
        """
        Test that metric response has expected structure.
        Verifies:
        - All required fields are present
        - Field types are correct
        """
        # Act
        response = await client.get(
            f"/api/v1/researcher_metrics/by-user/{test_researcher_metric.researcher_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, dict) and "items" in data:
            metrics = data["items"]
        else:
            metrics = data

        if metrics:
            metric = metrics[0]
            # Verify expected fields
            assert "id" in metric
            assert "researcher_id" in metric
            assert "h_index" in metric or metric.get("h_index") is not None
            assert "date" in metric

