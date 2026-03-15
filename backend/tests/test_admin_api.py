"""API tests for admin endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_admin

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_admin():
    """Override get_current_admin for all tests."""
    app.dependency_overrides[get_current_admin] = lambda: "admin-123"
    yield
    app.dependency_overrides.clear()


class TestAdminMetrics:
    @patch("app.api.v1.admin.compute_hero_metrics")
    def test_get_metrics(self, mock_compute):
        mock_compute.return_value = {
            "north_star": {"value": 5, "previous": 3, "trend": "up", "change_pct": 66.7},
            "mrr": {"value": 99.0, "previous": 99.0, "trend": "stable", "change_pct": 0.0},
            "activation_rate": {"value": 25.0, "previous": 25.0, "trend": "stable", "change_pct": 0.0},
            "churn_30d": {"value": 2.0, "previous": 3.0, "trend": "up", "change_pct": -33.3},
            "conversion_rate": {"value": 10.0, "previous": 10.0, "trend": "stable", "change_pct": 0.0},
        }
        resp = client.get("/api/v1/admin/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "north_star" in data
        assert data["north_star"]["value"] == 5

    @patch("app.api.v1.admin.compute_business_alerts")
    def test_get_alerts_empty(self, mock_compute):
        mock_compute.return_value = {"alerts": []}
        resp = client.get("/api/v1/admin/alerts")
        assert resp.status_code == 200
        assert resp.json()["alerts"] == []

    @patch("app.api.v1.admin.compute_business_alerts")
    def test_get_alerts_with_items(self, mock_compute):
        mock_compute.return_value = {
            "alerts": [
                {
                    "type": "low_activation",
                    "severity": "medium",
                    "message": "Taux faible",
                    "detail": "25%",
                    "tooltip": "Tip",
                }
            ]
        }
        resp = client.get("/api/v1/admin/alerts")
        assert resp.status_code == 200
        assert len(resp.json()["alerts"]) == 1

    @patch("app.api.v1.admin.compute_activation_funnel")
    def test_get_funnel(self, mock_compute):
        mock_compute.return_value = {
            "steps": [{"label": "Inscrits", "count": 10, "rate": 100.0}],
            "bottleneck_index": 0,
        }
        resp = client.get("/api/v1/admin/funnel")
        assert resp.status_code == 200
        assert len(resp.json()["steps"]) == 1

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_get_users(self, mock_compute):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        resp = client.get("/api/v1/admin/users?page=1&per_page=10")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_get_users_with_filters(self, mock_compute):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        resp = client.get("/api/v1/admin/users?search=test@example.com&status=power_user&plan=pro&sort=last_activity")
        assert resp.status_code == 200
        mock_compute.assert_called_once_with(
            search="test@example.com",
            status_filter="power_user",
            plan_filter="pro",
            sort="last_activity",
            page=1,
            per_page=50,
        )
