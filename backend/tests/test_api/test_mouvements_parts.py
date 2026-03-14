"""Tests for mouvements_parts API — CRUD operations."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


SCI_UUID = "00000000-0000-0000-0000-000000000001"
SCI2_UUID = "00000000-0000-0000-0000-000000000002"
MP_TABLE = "mouvements_parts"

MP_PAYLOAD = {
    "date_mouvement": "2026-06-01",
    "type_mouvement": "cession",
    "cedant_nom": "Jean Dupont",
    "cessionnaire_nom": "Marie Martin",
    "nb_parts": 10,
    "prix_unitaire": 100.0,
    "prix_total": 1000.0,
    "notes": "Cession amicale",
}


@pytest.fixture(autouse=True)
def _uuid_sci_data(fake_supabase):
    """Seed the store with UUID-based SCI + associe data for MP endpoints."""
    fake_supabase.store["sci"].extend([
        {"id": SCI_UUID, "nom": "SCI Test MP"},
        {"id": SCI2_UUID, "nom": "SCI Test MP 2"},
    ])
    fake_supabase.store["associes"].extend([
        {"id": "assoc-mp-1", "id_sci": SCI_UUID, "user_id": "user-123", "nom": "Test", "role": "gerant"},
        {"id": "assoc-mp-2", "id_sci": SCI2_UUID, "user_id": "user-123", "nom": "Test", "role": "associe"},
    ])


class TestListMouvementsParts:
    def test_list_empty(self, client: TestClient, auth_headers: dict):
        response = client.get(f"/api/v1/scis/{SCI_UUID}/mouvements-parts", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_seeded_data(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[MP_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000b1", "id_sci": SCI_UUID, "date_mouvement": "2026-01-15",
             "type_mouvement": "cession", "cedant_nom": "A", "cessionnaire_nom": "B",
             "nb_parts": 5, "prix_unitaire": 50.0, "prix_total": 250.0},
            {"id": "00000000-0000-0000-0000-0000000000b2", "id_sci": SCI_UUID, "date_mouvement": "2026-06-01",
             "type_mouvement": "donation", "cedant_nom": "C", "cessionnaire_nom": "D",
             "nb_parts": 3, "prix_unitaire": 0.0, "prix_total": 0.0},
        ]
        response = client.get(f"/api/v1/scis/{SCI_UUID}/mouvements-parts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["date_mouvement"] == "2026-06-01"

    def test_list_requires_auth(self, client: TestClient):
        response = client.get(f"/api/v1/scis/{SCI_UUID}/mouvements-parts")
        assert response.status_code in (401, 403)

    def test_list_wrong_sci_returns_404(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/scis/00000000-0000-0000-0000-000000000099/mouvements-parts",
                              headers=auth_headers)
        assert response.status_code == 404


class TestCreateMouvementParts:
    def test_create_success(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/mouvements-parts",
            json=MP_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["type_mouvement"] == "cession"
        assert body["nb_parts"] == 10
        assert body["id_sci"] == SCI_UUID

    def test_create_minimal(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/mouvements-parts",
            json={
                "date_mouvement": "2026-03-01",
                "type_mouvement": "cession",
                "cedant_nom": "X",
                "cessionnaire_nom": "Y",
                "nb_parts": 1,
                "prix_unitaire": 0.0,
                "prix_total": 0.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_create_validation_error(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/mouvements-parts",
            json={"date_mouvement": "2026-01-01", "type_mouvement": "", "cedant_nom": "",
                  "cessionnaire_nom": "", "nb_parts": 0, "prix_unitaire": -1, "prix_total": -1},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_requires_gerant(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI2_UUID}/mouvements-parts",
            json=MP_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestDeleteMouvementParts:
    def test_delete_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[MP_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000b1", "id_sci": SCI_UUID, "date_mouvement": "2026-01-15",
             "type_mouvement": "cession", "cedant_nom": "A", "cessionnaire_nom": "B",
             "nb_parts": 5, "prix_unitaire": 50.0, "prix_total": 250.0},
        ]
        response = client.delete(
            f"/api/v1/scis/{SCI_UUID}/mouvements-parts/00000000-0000-0000-0000-0000000000b1",
            headers=auth_headers,
        )
        assert response.status_code == 204
        assert len(fake_supabase.store[MP_TABLE]) == 0

    def test_delete_not_found(self, client: TestClient, auth_headers: dict):
        response = client.delete(
            f"/api/v1/scis/{SCI_UUID}/mouvements-parts/00000000-0000-0000-0000-000000000099",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_requires_gerant(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store[MP_TABLE] = [
            {"id": "00000000-0000-0000-0000-0000000000b1", "id_sci": SCI2_UUID, "date_mouvement": "2026-01-15",
             "type_mouvement": "cession", "cedant_nom": "A", "cessionnaire_nom": "B",
             "nb_parts": 5, "prix_unitaire": 50.0, "prix_total": 250.0},
        ]
        response = client.delete(
            f"/api/v1/scis/{SCI2_UUID}/mouvements-parts/00000000-0000-0000-0000-0000000000b1",
            headers=auth_headers,
        )
        assert response.status_code == 403
