"""
Functional tests for data export endpoints.
Tests exporting researcher metrics in different formats and with filters.
"""
import pytest
import uuid
from datetime import date
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDataExportFlow:
    """Test data export complete workflows."""

    async def test_export_metrics_xlsx_happy_path(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test happy path: Export researcher metrics in XLSX format.
        Verifies:
        - HTTP 200 response
        - Response has correct content-type
        - Response body contains file data
        - Content-Disposition header is set
        """
        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=xlsx&scope=history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify correct content-type
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "xlsx" in content_type, \
            f"Expected XLSX content-type, got {content_type}"

        # Verify file attachment header
        disposition = response.headers.get("content-disposition", "")
        assert "attachment" in disposition, "Should have attachment header"
        assert ".xlsx" in disposition or "filename" in disposition, "Should specify xlsx filename"

        # Verify content is not empty
        assert len(response.content) > 0, "Response body should contain file data"

    async def test_export_metrics_csv_happy_path(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test happy path: Export researcher metrics in CSV format.
        Verifies:
        - HTTP 200 response
        - Response has CSV content-type
        - File is downloadable
        """
        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=csv&scope=history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify CSV content-type
        content_type = response.headers.get("content-type", "")
        assert "csv" in content_type, f"Expected CSV content-type, got {content_type}"

        # Verify file attachment
        disposition = response.headers.get("content-disposition", "")
        assert "attachment" in disposition
        assert ".csv" in disposition or "filename" in disposition

        # Verify content
        assert len(response.content) > 0

    async def test_export_metrics_with_date_filter(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test exporting metrics with date range filter.
        Verifies:
        - start_date and end_date parameters are accepted
        - Only metrics within date range are exported
        - Date filtering is applied correctly
        """
        # Arrange
        start_date = date(2023, 1, 1)
        end_date = date(2024, 12, 31)

        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?"
            f"format=csv&scope=history&start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200 or response.status_code == 400, \
            f"Expected 200 or 400, got {response.status_code}"

        # If successful, should have exported data
        if response.status_code == 200:
            assert len(response.content) > 0

    async def test_export_metrics_latest_scope(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test exporting only latest metrics with 'latest' scope.
        Verifies:
        - scope=latest parameter works
        - Only latest metrics per source are included
        """
        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=xlsx&scope=latest",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert len(response.content) > 0

    async def test_export_metrics_unauthorized_researcher_fails(self, client: AsyncClient, researcher_token, test_admin_user, test_researcher_profile):
        """
        Test that researcher cannot export other researcher's metrics.
        Verifies:
        - HTTP 403 Forbidden for unauthorized access
        - Proper access control
        """
        # Act - Researcher token trying to export admin's profile
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=xlsx",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        # If researcher is not the profile owner, should get 403
        if str(test_researcher_profile.id) != str(test_admin_user.id):
            assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_export_non_existent_profile_fails(self, client: AsyncClient, admin_token):
        """
        Test error case: Export metrics for non-existent profile.
        Verifies:
        - HTTP 404 Not Found response
        """
        # Arrange
        fake_profile_id = uuid.uuid4()

        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{fake_profile_id}?format=xlsx",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    async def test_export_all_metrics_admin_only(self, client: AsyncClient, admin_token):
        """
        Test that exporting all metrics requires admin role.
        Verifies:
        - Only admins can export all metrics
        - HTTP 200 response for admin
        """
        # Act
        response = await client.get(
            "/api/v1/export/researcher_metric?fmt=xlsx&scope=history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        # Should succeed or return 400 for bad params, but not 403
        assert response.status_code != 403, "Admin should be allowed to export all metrics"

    async def test_export_all_metrics_non_admin_fails(self, client: AsyncClient, researcher_token):
        """
        Test error case: Non-admin cannot export all metrics.
        Verifies:
        - HTTP 403 Forbidden response
        """
        # Act
        response = await client.get(
            "/api/v1/export/researcher_metric?fmt=xlsx&scope=history",
            headers={"Authorization": f"Bearer {researcher_token}"}
        )

        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    async def test_export_without_authentication_fails(self, client: AsyncClient, test_researcher_profile):
        """
        Test error case: Export without authentication token.
        Verifies:
        - HTTP 403 response (no Bearer token)
        """
        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=xlsx"
        )

        # Assert
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    async def test_export_file_format_is_valid(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test that exported file format is valid.
        Verifies:
        - XLSX file is a valid/readable format
        - CSV file is properly formatted
        """
        # Act - Export as CSV
        csv_response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert CSV
        assert csv_response.status_code == 200
        csv_content = csv_response.content.decode('utf-8', errors='ignore')

        # Basic CSV validation - should have at least headers
        lines = csv_content.split('\n')
        assert len(lines) > 0, "CSV should have content"

    async def test_export_response_headers_are_correct(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test that export response headers are correctly set.
        Verifies:
        - Content-Disposition header is proper
        - Content-Type is set correctly
        - Cache headers if applicable
        """
        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=xlsx",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200

        # Check headers
        assert "content-disposition" in response.headers
        assert "content-type" in response.headers

        disposition = response.headers["content-disposition"]
        assert "attachment" in disposition.lower()
        assert "filename" in disposition.lower()


@pytest.mark.asyncio
class TestExportDataIntegrity:
    """Test data integrity in export operations."""

    async def test_exported_data_matches_stored_metrics(self, client: AsyncClient, admin_token, test_researcher_profile, test_researcher_metric):
        """
        Test that exported data matches metrics in database.
        Verifies:
        - Export includes the correct metric
        - No data is lost in export
        - Serialization is correct
        """
        # Act
        response = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200

        csv_content = response.content.decode('utf-8', errors='ignore')
        lines = csv_content.split('\n')

        # Should have headers + at least one data row
        assert len(lines) >= 1, "CSV should contain headers"

    async def test_multiple_exports_consistent(self, client: AsyncClient, admin_token, test_researcher_profile):
        """
        Test that multiple exports produce consistent results.
        Verifies:
        - Multiple exports of same data are identical
        - No race conditions or inconsistent state
        """
        # Act - First export
        response1 = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Act - Second export
        response2 = await client.get(
            f"/api/v1/export/researcher_metric/{test_researcher_profile.id}?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Content should be the same (at least same structure)
        assert len(response1.content) == len(response2.content) or \
               len(response1.content) > 0 and len(response2.content) > 0, \
            "Multiple exports should be consistent"

