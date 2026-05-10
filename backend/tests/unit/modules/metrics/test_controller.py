import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.metrics.schema.metric_schemas import ResearcherMetricResponse
from src.modules.metrics.controller.researcher_metric_controller import (
    router,
    get_researcher_metric_service,
)
from src.modules.metrics.schema.source_schemas import SourceModel, SourceNameModel


# Helpers
def make_metric_response(**kwargs) -> ResearcherMetricResponse:
    return ResearcherMetricResponse(
        date=kwargs.get("date", datetime.date.today()),
        h_index=kwargs.get("h_index", 10),
        i10_index=kwargs.get("i10_index", 5),
        total_citations=kwargs.get("total_citations", 100),
        total_publications=kwargs.get("total_publications", 20),
        source=kwargs.get("source", SourceModel(name=SourceNameModel.orcid, url="")),
    )


def build_app(service_mock) -> TestClient:
    """
    Cria uma app FastAPI de teste com o serviço e a autenticação substituídos por mocks.
    """
    app = FastAPI()
    app.include_router(router)

    # Substitui o serviço injectado pelo Depends
    app.dependency_overrides[get_researcher_metric_service] = lambda: service_mock

    # Substitui require_admin para não validar JWT nos testes do controller
    from src.modules.auth.auth import require_admin
    app.dependency_overrides[require_admin] = lambda: MagicMock()

    return TestClient(app)


# POST /researcher_metrics/create_metric
class TestCreateMetricEndpoint:

    def test_create_metric_returns_201(self):
        response_data = make_metric_response()
        service = MagicMock()
        service.create_metric = AsyncMock(return_value=response_data)
        client = build_app(service)

        payload = {
            "researcher_id": str(uuid.uuid4()),
            "h_index": 10,
            "i10_index": 5,
            "total_citations": 100,
            "total_publications": 20,
            "source": {
                "name": "scholar",
                "url": "https://scholar.google.com/citations?user=abc123"
            },
        }
        response = client.post("/researcher_metrics/create_metric", json=payload)

        assert response.status_code == 201
        service.create_metric.assert_called_once()

    def test_create_metric_researcher_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.create_metric = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Researcher not found")
        )
        client = build_app(service)

        payload = {
            "researcher_id": str(uuid.uuid4()),
            "h_index": 10,
            "i10_index": 5,
            "total_citations": 100,
            "total_publications": 20,
            "source": {
                "name": "scholar",
                "url": "https://scholar.google.com/citations?user=abc123"
            },
        }
        response = client.post("/researcher_metrics/create_metric", json=payload)

        assert response.status_code == 404
        assert response.json()["detail"] == "Researcher not found"

    def test_create_metric_invalid_payload_returns_422(self):
        service = MagicMock()
        client = build_app(service)

        # falta campos obrigatórios
        response = client.post("/researcher_metrics/create_metric", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /researcher_metrics/{metric_id}
# ---------------------------------------------------------------------------

class TestDeleteMetricEndpoint:

    def test_delete_metric_returns_204(self):
        service = MagicMock()
        service.delete_metric = AsyncMock(return_value=None)
        client = build_app(service)

        response = client.delete(f"/researcher_metrics/{uuid.uuid4()}")

        assert response.status_code == 204
        service.delete_metric.assert_called_once()

    def test_delete_metric_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.delete_metric = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Metric not found")
        )
        client = build_app(service)

        response = client.delete(f"/researcher_metrics/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Metric not found"


# ---------------------------------------------------------------------------
# PATCH /researcher_metrics/{metric_id}
# ---------------------------------------------------------------------------

class TestUpdateMetricEndpoint:

    def test_update_metric_returns_200(self):
        updated = make_metric_response(h_index=99)
        service = MagicMock()
        service.update_metric = AsyncMock(return_value=updated)
        client = build_app(service)

        response = client.patch(
            f"/researcher_metrics/{uuid.uuid4()}",
            json={"h_index": 99},
        )

        assert response.status_code == 200
        assert response.json()["h_index"] == 99

    def test_update_metric_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.update_metric = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Metric not found")
        )
        client = build_app(service)

        response = client.patch(
            f"/researcher_metrics/{uuid.uuid4()}",
            json={"h_index": 99},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /researcher_metrics/by-user/{user_id}
# ---------------------------------------------------------------------------

class TestGetMetricByUserEndpoint:

    def test_get_metrics_by_user_returns_list(self):
        metrics = [make_metric_response(), make_metric_response()]
        service = MagicMock()
        service.get_metric_by_user_id = AsyncMock(return_value=metrics)
        client = build_app(service)

        response = client.get(f"/researcher_metrics/by-user/{uuid.uuid4()}")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_metrics_user_not_found_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.get_metric_by_user_id = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="User not found")
        )
        client = build_app(service)

        response = client.get(f"/researcher_metrics/by-user/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_get_metrics_user_without_profile_returns_404(self):
        from fastapi import HTTPException
        service = MagicMock()
        service.get_metric_by_user_id = AsyncMock(
            side_effect=HTTPException(
                status_code=404, detail="User ResearcherProfile not found"
            )
        )
        client = build_app(service)

        response = client.get(f"/researcher_metrics/by-user/{uuid.uuid4()}")

        assert response.status_code == 404
        assert "ResearcherProfile" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /researcher_metrics/by-date/{date}
# ---------------------------------------------------------------------------

class TestGetMetricByDateEndpoint:

    def test_get_metrics_by_date_returns_list(self):
        metrics = [make_metric_response()]
        service = MagicMock()
        service.get_metric_by_date = AsyncMock(return_value=metrics)
        client = build_app(service)

        response = client.get(f"/researcher_metrics/by-date/2024-01-15")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_metrics_by_date_returns_empty_list(self):
        service = MagicMock()
        service.get_metric_by_date = AsyncMock(return_value=[])
        client = build_app(service)

        response = client.get(f"/researcher_metrics/by-date/2024-01-15")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_metrics_invalid_date_format_returns_422(self):
        service = MagicMock()
        client = build_app(service)

        response = client.get("/researcher_metrics/by-date/not-a-date")

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /researcher_metrics/
# ---------------------------------------------------------------------------

class TestListMetricsEndpoint:

    def test_list_metrics_returns_all(self):
        metrics = [make_metric_response(), make_metric_response(), make_metric_response()]
        service = MagicMock()
        service.list_metrics = AsyncMock(return_value=metrics)
        client = build_app(service)

        response = client.get("/researcher_metrics/")

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_metrics_returns_empty_list(self):
        service = MagicMock()
        service.list_metrics = AsyncMock(return_value=[])
        client = build_app(service)

        response = client.get("/researcher_metrics/")

        assert response.status_code == 200
        assert response.json() == []
