"""Tests for CSV import API — biens and loyers."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient


SCI_UUID = "00000000-0000-0000-0000-000000000001"
SCI2_UUID = "00000000-0000-0000-0000-000000000002"

PREFIX = f"/api/v1/scis/{SCI_UUID}/import"

VALID_BIENS_CSV = (
    "adresse,ville,code_postal,type_locatif,surface_m2,nb_pieces,loyer_cc,charges\n"
    "12 rue de la Paix,Paris,75001,nu,65,3,1250,180\n"
    "8 rue des Lilas,Lyon,69001,meuble,28,1,750,90\n"
)

VALID_LOYERS_CSV = (
    "adresse_bien,date_loyer,montant,statut\n"
    "12 rue test,2026-01-01,1250,paye\n"
    "12 rue test,2026-02-01,1250,en_attente\n"
)


@pytest.fixture(autouse=True)
def _uuid_sci_data(fake_supabase):
    """Seed store with UUID-based SCI + associe data for import endpoints."""
    fake_supabase.store["sci"].extend([
        {"id": SCI_UUID, "nom": "SCI Import Test"},
        {"id": SCI2_UUID, "nom": "SCI Import Test 2"},
    ])
    fake_supabase.store["associes"].extend([
        {"id": "assoc-imp-1", "id_sci": SCI_UUID, "user_id": "user-123", "nom": "Test Gerant", "role": "gerant"},
        {"id": "assoc-imp-2", "id_sci": SCI2_UUID, "user_id": "user-123", "nom": "Test Associe", "role": "associe"},
    ])


def _csv_upload(content: str, filename: str = "import.csv"):
    return ("file", (filename, io.BytesIO(content.encode("utf-8")), "text/csv"))


# ──────────────────────────────────────────────────────────────
# GET /templates/{type}
# ──────────────────────────────────────────────────────────────

class TestGetTemplate:
    def test_template_biens(self, client: TestClient):
        response = client.get(f"{PREFIX}/templates/biens")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "adresse" in response.text
        assert "ville" in response.text

    def test_template_loyers(self, client: TestClient):
        response = client.get(f"{PREFIX}/templates/loyers")
        assert response.status_code == 200
        assert "adresse_bien" in response.text
        assert "date_loyer" in response.text

    def test_template_invalid_type(self, client: TestClient):
        response = client.get(f"{PREFIX}/templates/invalid")
        assert response.status_code == 400


# ──────────────────────────────────────────────────────────────
# POST /csv — biens import
# ──────────────────────────────────────────────────────────────

class TestImportBiens:
    def test_import_biens_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(VALID_BIENS_CSV)],
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["imported"] == 2
        assert body["skipped"] == 0
        assert body["errors"] == []
        assert body["type"] == "biens"
        # Verify rows inserted into store
        sci_biens = [b for b in fake_supabase.store["biens"] if b.get("id_sci") == SCI_UUID]
        assert len(sci_biens) == 2

    def test_import_biens_missing_columns(self, client: TestClient, auth_headers: dict):
        csv_content = "adresse,ville\n12 rue,Paris\n"
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(csv_content)],
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Colonnes manquantes" in response.json()["error"]

    def test_import_biens_file_too_large(self, client: TestClient, auth_headers: dict):
        large_content = "adresse,ville,code_postal,type_locatif,surface_m2,nb_pieces,loyer_cc,charges\n" + "x" * (6 * 1024 * 1024)
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(large_content)],
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "volumineux" in response.json()["error"]

    def test_import_biens_too_many_rows(self, client: TestClient, auth_headers: dict):
        header = "adresse,ville,code_postal,type_locatif,surface_m2,nb_pieces,loyer_cc,charges\n"
        rows = "".join(f"Rue {i},Paris,75001,nu,50,2,1000,100\n" for i in range(501))
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(header + rows)],
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Trop de lignes" in response.json()["error"]

    def test_import_biens_duplicate_skip(self, client: TestClient, auth_headers: dict, fake_supabase):
        # Seed an existing bien with same adresse+ville
        fake_supabase.store["biens"].append({
            "id": "bien-dup",
            "id_sci": SCI_UUID,
            "adresse": "12 rue de la Paix",
            "ville": "Paris",
            "code_postal": "75001",
        })
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(VALID_BIENS_CSV)],
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["imported"] == 1  # Only Lyon, Paris is duplicate
        assert body["skipped"] == 1

    def test_import_biens_empty_file(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload("")],
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_import_biens_row_validation_error(self, client: TestClient, auth_headers: dict):
        csv_content = "adresse,ville,code_postal,type_locatif,surface_m2,nb_pieces,loyer_cc,charges\n,,,,abc,x,y,z\n"
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(csv_content)],
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["imported"] == 0
        assert len(body["errors"]) == 1


# ──────────────────────────────────────────────────────────────
# POST /csv — loyers import
# ──────────────────────────────────────────────────────────────

class TestImportLoyers:
    def test_import_loyers_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        # Seed a bien to match the address
        fake_supabase.store["biens"].append({
            "id": "bien-match",
            "id_sci": SCI_UUID,
            "adresse": "12 rue test",
            "ville": "Paris",
        })
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "loyers"},
            files=[_csv_upload(VALID_LOYERS_CSV)],
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["imported"] == 2
        assert body["type"] == "loyers"

    def test_import_loyers_unknown_address(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "loyers"},
            files=[_csv_upload(VALID_LOYERS_CSV)],
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["imported"] == 0
        assert len(body["errors"]) == 2
        assert "introuvable" in body["errors"][0]


# ──────────────────────────────────────────────────────────────
# Auth / role checks
# ──────────────────────────────────────────────────────────────

class TestImportAuth:
    def test_import_without_auth(self, client: TestClient):
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "biens"},
            files=[_csv_upload(VALID_BIENS_CSV)],
        )
        assert response.status_code in (401, 403)

    def test_import_as_associe_forbidden(self, client: TestClient, auth_headers: dict):
        prefix_sci2 = f"/api/v1/scis/{SCI2_UUID}/import"
        response = client.post(
            f"{prefix_sci2}/csv",
            data={"type": "biens"},
            files=[_csv_upload(VALID_BIENS_CSV)],
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_import_invalid_type(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"{PREFIX}/csv",
            data={"type": "invalid"},
            files=[_csv_upload(VALID_BIENS_CSV)],
            headers=auth_headers,
        )
        assert response.status_code == 400
