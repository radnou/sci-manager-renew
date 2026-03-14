"""Tests for assemblees_generales API — CRUD operations."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# AG endpoints expect UUID sci_ids. We need to seed our fake store with UUID-like IDs.
SCI_UUID = "00000000-0000-0000-0000-000000000001"
SCI2_UUID = "00000000-0000-0000-0000-000000000002"
AG_TABLE = "assemblees_generales"

AG_PAYLOAD = {
    "date_ag": "2026-06-15",
    "type_ag": "ordinaire",
    "exercice_annee": 2025,
    "ordre_du_jour": "Approbation des comptes",
    "quorum_atteint": True,
    "resolutions": "Comptes approves",
    "notes": "RAS",
}


@pytest.fixture(autouse=True)
def _uuid_sci_data(fake_supabase):
    """Seed the store with UUID-based SCI + associe data for AG endpoints."""
    fake_supabase.store["sci"].extend([
        {"id": SCI_UUID, "nom": "SCI Test AG"},
        {"id": SCI2_UUID, "nom": "SCI Test AG 2"},
    ])
    fake_supabase.store["associes"].extend([
        {"id": "assoc-ag-1", "id_sci": SCI_UUID, "user_id": "user-123", "nom": "Test", "role": "gerant"},
        {"id": "assoc-ag-2", "id_sci": SCI2_UUID, "user_id": "user-123", "nom": "Test", "role": "associe"},
    ])


class TestListAssembleesGenerales:
    def test_list_empty(self, client: TestClient, auth_headers: dict):
        response = client.get(f"/api/v1/scis/{SCI_UUID}/assemblees-generales", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_seeded_data(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[AG_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000a1", "id_sci": SCI_UUID, "date_ag": "2026-01-10", "type_ag": "ordinaire",
             "exercice_annee": 2025, "quorum_atteint": True},
            {"id": "00000000-0000-0000-0000-0000000000a2", "id_sci": SCI_UUID, "date_ag": "2026-06-15", "type_ag": "extraordinaire",
             "exercice_annee": 2025, "quorum_atteint": False},
        ]
        response = client.get(f"/api/v1/scis/{SCI_UUID}/assemblees-generales", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["date_ag"] == "2026-06-15"

    def test_list_requires_auth(self, client: TestClient):
        response = client.get(f"/api/v1/scis/{SCI_UUID}/assemblees-generales")
        assert response.status_code in (401, 403)

    def test_list_wrong_sci_returns_404(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/scis/00000000-0000-0000-0000-000000000099/assemblees-generales",
                              headers=auth_headers)
        assert response.status_code == 404


class TestCreateAssembleeGenerale:
    def test_create_success(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales",
            json=AG_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["type_ag"] == "ordinaire"
        assert body["exercice_annee"] == 2025
        assert body["id_sci"] == SCI_UUID

    def test_create_minimal_payload(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales",
            json={"date_ag": "2026-03-01", "type_ag": "ordinaire", "exercice_annee": 2025},
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_create_validation_error(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales",
            json={"date_ag": "2026-01-01", "type_ag": "", "exercice_annee": 1999},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_requires_gerant(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI2_UUID}/assemblees-generales",
            json=AG_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestUpdateAssembleeGenerale:
    def test_update_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[AG_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000a1", "id_sci": SCI_UUID, "date_ag": "2026-01-10", "type_ag": "ordinaire",
             "exercice_annee": 2025, "quorum_atteint": False, "resolutions": None, "notes": None,
             "ordre_du_jour": None, "pv_url": None, "created_at": None},
        ]
        response = client.patch(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/00000000-0000-0000-0000-0000000000a1",
            json={**AG_PAYLOAD, "quorum_atteint": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["quorum_atteint"] is True

    def test_update_not_found(self, client: TestClient, auth_headers: dict):
        response = client.patch(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/00000000-0000-0000-0000-000000000099",
            json=AG_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteAssembleeGenerale:
    def test_delete_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[AG_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000a1", "id_sci": SCI_UUID, "date_ag": "2026-01-10", "type_ag": "ordinaire",
             "exercice_annee": 2025, "quorum_atteint": False},
        ]
        response = client.delete(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/00000000-0000-0000-0000-0000000000a1",
            headers=auth_headers,
        )
        assert response.status_code == 204
        assert len(fake_supabase.store[AG_TABLE]) == 0

    def test_delete_not_found(self, client: TestClient, auth_headers: dict):
        response = client.delete(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/00000000-0000-0000-0000-000000000099",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_requires_gerant(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[AG_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000a1", "id_sci": SCI2_UUID, "date_ag": "2026-01-10", "type_ag": "ordinaire",
             "exercice_annee": 2025, "quorum_atteint": False},
        ]
        response = client.delete(
            f"/api/v1/scis/{SCI2_UUID}/assemblees-generales/00000000-0000-0000-0000-0000000000a1",
            headers=auth_headers,
        )
        assert response.status_code == 403
