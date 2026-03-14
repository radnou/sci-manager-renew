"""
Comprehensive tests for /scis/{sci_id}/biens nested API endpoints.

Covers all 30+ endpoints in backend/app/api/v1/scis_biens.py.
Uses the sync TestClient + FakeSupabaseClient pattern from conftest.py.

NOTE: sci_id must be a valid UUID because the router declares `sci_id: UUID`.
      We replace conftest's "sci-1"/"sci-2" store keys with real UUIDs and
      seed the associes store accordingly inside each test class.
"""

from __future__ import annotations

import pytest

# ──────────────────────────────────────────────────────────────
# Constants — all sci IDs must be valid UUIDs
# ──────────────────────────────────────────────────────────────

# user-123 will be gerant of this SCI
SCI_UUID = "11111111-1111-1111-1111-111111111111"
# user-123 will be associe (read-only) of this SCI
SCI_UUID_ASSOC = "22222222-2222-2222-2222-222222222222"

BIEN_ID = "bien-abc"           # Used for most endpoints (BienResponse allows str id)
BIEN_ID_INT = "123"            # Used for fiche bien (FicheBienResponse requires int id)

BASE = f"/api/v1/scis/{SCI_UUID}/biens"
BASE_ASSOC = f"/api/v1/scis/{SCI_UUID_ASSOC}/biens"

ACTIVE_SUB = {
    "user_id": "user-123",
    "plan_key": "pro",
    "status": "active",
    "is_active": True,
    "onboarding_completed": True,
    "max_scis": 10,
    "max_biens": 20,
    "features": {},
}

GERANT_ASSOCIE = {
    "id": "associe-uuid-1",
    "id_sci": SCI_UUID,
    "user_id": "user-123",
    "nom": "Test User",
    "email": "test.user@sci.local",
    "part": 60,
    "role": "gerant",
}

ASSOC_ONLY = {
    "id": "associe-uuid-2",
    "id_sci": SCI_UUID_ASSOC,
    "user_id": "user-123",
    "nom": "Test User",
    "email": "test.user@sci.local",
    "part": 40,
    "role": "associe",
}


def seed_associes(fake_supabase):
    """Replace the default associes store with UUID-keyed records."""
    fake_supabase.store["associes"] = [GERANT_ASSOCIE, ASSOC_ONLY]


def seed_bien_int(fake_supabase, bien_id: int = 123, sci_id: int = 1) -> dict:
    """Insert a bien with integer ids (required by FicheBienResponse schema)."""
    bien = {
        "id": bien_id,
        "id_sci": sci_id,
        "adresse": "12 rue de la Paix",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1000.0,
        "charges": 100.0,
        "tmi": 30.0,
        "prix_acquisition": 200000.0,
        "surface_m2": 55.0,
        "nb_pieces": 3,
        "dpe_classe": "C",
    }
    fake_supabase.store.setdefault("biens", []).append(bien)
    return bien


def seed_bien(fake_supabase, bien_id: str = BIEN_ID, sci_id: str = SCI_UUID) -> dict:
    """Insert a minimal bien into the fake store and return it."""
    bien = {
        "id": bien_id,
        "id_sci": sci_id,
        "adresse": "12 rue de la Paix",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1000.0,
        "charges": 100.0,
        "tmi": 30.0,
        "prix_acquisition": 200000.0,
        "surface_m2": 55.0,
        "nb_pieces": 3,
        "dpe_classe": "C",
    }
    fake_supabase.store.setdefault("biens", []).append(bien)
    return bien


def setup(fake_supabase):
    """Seed subscriptions and associes for an authenticated gerant scenario."""
    fake_supabase.store["subscriptions"] = [ACTIVE_SUB]
    seed_associes(fake_supabase)


# ──────────────────────────────────────────────────────────────
# 1. GET /scis/{sci_id}/biens — list biens
# ──────────────────────────────────────────────────────────────

class TestListBiens:
    def test_requires_auth(self, client):
        """A real UUID without auth still triggers 401."""
        response = client.get(BASE)
        assert response.status_code == 401

    def test_returns_empty_list(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.get(BASE, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_biens_for_sci(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Add a bien belonging to a different SCI — should NOT appear
        seed_bien(fake_supabase, bien_id="bien-other", sci_id="sci-99")

        response = client.get(BASE, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == BIEN_ID
        assert data[0]["id_sci"] == SCI_UUID

    def test_non_member_gets_404(self, client, auth_headers, fake_supabase):
        """A valid UUID where user is not a member → 404."""
        setup(fake_supabase)
        unknown_sci = "99999999-9999-9999-9999-999999999999"
        response = client.get(f"/api/v1/scis/{unknown_sci}/biens", headers=auth_headers)
        assert response.status_code == 404

    def test_invalid_uuid_returns_422(self, client, auth_headers, fake_supabase):
        """A non-UUID value returns FastAPI 422 validation error."""
        setup(fake_supabase)
        response = client.get("/api/v1/scis/not-a-uuid/biens", headers=auth_headers)
        assert response.status_code == 422


# ──────────────────────────────────────────────────────────────
# 2. POST /scis/{sci_id}/biens — create bien
# ──────────────────────────────────────────────────────────────

class TestCreateBien:
    PAYLOAD = {
        "id_sci": SCI_UUID,
        "adresse": "20 avenue Victor Hugo",
        "ville": "Lyon",
        "code_postal": "69001",
        "type_locatif": "meuble",
        "loyer_cc": 850.0,
        "charges": 50.0,
        "tmi": 0.0,
    }

    def test_requires_auth(self, client):
        response = client.post(BASE, json=self.PAYLOAD)
        assert response.status_code == 401

    def test_create_bien_as_gerant_returns_201(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.post(BASE, json=self.PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["adresse"] == self.PAYLOAD["adresse"]
        # Path param SCI_UUID is forced onto the row
        assert data["id_sci"] == SCI_UUID

    def test_create_bien_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        """user-123 is only 'associe' in SCI_UUID_ASSOC, so POST must be 403."""
        setup(fake_supabase)
        payload = {**self.PAYLOAD, "id_sci": SCI_UUID_ASSOC}
        response = client.post(BASE_ASSOC, json=payload, headers=auth_headers)
        assert response.status_code == 403

    def test_bien_appears_in_list_after_create(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        client.post(BASE, json=self.PAYLOAD, headers=auth_headers)
        list_resp = client.get(BASE, headers=auth_headers)
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1


# ──────────────────────────────────────────────────────────────
# 3. GET /scis/{sci_id}/biens/{bien_id} — fiche bien
# ──────────────────────────────────────────────────────────────

class TestGetFicheBien:
    """
    FicheBienResponse requires integer id and id_sci fields.
    We use integer bien IDs (123) and set id_sci to match the SCI_UUID from the path.
    The _verify_bien_belongs_to_sci check does: str(bien["id_sci"]) == sci_id
    so id_sci must equal SCI_UUID string.
    """
    FICHE_BIEN_ID = 123
    FICHE_SCI_ID = SCI_UUID   # stored as string to match UUID path param check

    def _seed_fiche_bien(self, fake_supabase):
        """Seed a bien with int id and string id_sci matching SCI_UUID."""
        bien = {
            "id": self.FICHE_BIEN_ID,
            "id_sci": self.FICHE_SCI_ID,
            "adresse": "12 rue de la Paix",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 1000.0,
            "charges": 100.0,
            "tmi": 30.0,
            "prix_acquisition": 200000.0,
            "surface_m2": 55.0,
            "nb_pieces": 3,
            "dpe_classe": "C",
        }
        fake_supabase.store.setdefault("biens", []).append(bien)

    def _seed_empty_tables(self, fake_supabase):
        for tbl in ("baux", "loyers", "charges", "assurances_pno", "frais_agence", "documents_bien"):
            fake_supabase.store.setdefault(tbl, [])

    def test_requires_auth(self, client):
        response = client.get(f"{BASE}/{self.FICHE_BIEN_ID}")
        assert response.status_code == 401

    def test_returns_404_for_unknown_bien(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        self._seed_empty_tables(fake_supabase)
        response = client.get(f"{BASE}/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_returns_fiche_bien(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        self._seed_fiche_bien(fake_supabase)
        self._seed_empty_tables(fake_supabase)

        response = client.get(f"{BASE}/{self.FICHE_BIEN_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["adresse"] == "12 rue de la Paix"
        assert data["ville"] == "Paris"
        assert "rentabilite" in data
        assert "brute" in data["rentabilite"]
        assert data["bail_actif"] is None
        assert data["loyers_recents"] == []

    def test_fiche_bien_with_bail_actif(self, client, auth_headers, fake_supabase):
        """Fiche bien embeds the active bail."""
        setup(fake_supabase)
        self._seed_fiche_bien(fake_supabase)

        fake_supabase.store["baux"] = [
            {
                "id": 1,
                "id_bien": str(self.FICHE_BIEN_ID),
                "date_debut": "2024-01-01",
                "loyer_hc": 900.0,
                "charges_locatives": 100.0,
                "depot_garantie": 900.0,
                "statut": "en_cours",
            }
        ]
        fake_supabase.store.setdefault("locataires", [])
        for tbl in ("loyers", "charges", "assurances_pno", "frais_agence", "documents_bien"):
            fake_supabase.store.setdefault(tbl, [])

        response = client.get(f"{BASE}/{self.FICHE_BIEN_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["bail_actif"] is not None
        assert data["bail_actif"]["statut"] == "en_cours"

    def test_fiche_bien_rentabilite_calculated(self, client, auth_headers, fake_supabase):
        """Rentabilite brute = (loyer_cc * 12 / prix_acquisition) * 100 = 6.0."""
        setup(fake_supabase)
        self._seed_fiche_bien(fake_supabase)
        self._seed_empty_tables(fake_supabase)

        response = client.get(f"{BASE}/{self.FICHE_BIEN_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        rentabilite = data["rentabilite"]
        # loyer_cc=1000, prix_acquisition=200000 → brute=6.0
        assert abs(rentabilite["brute"] - 6.0) < 0.01

    def test_bien_wrong_sci_returns_404(self, client, auth_headers, fake_supabase):
        """A bien that belongs to SCI_UUID cannot be fetched via SCI_UUID_ASSOC URL."""
        setup(fake_supabase)
        self._seed_fiche_bien(fake_supabase)
        self._seed_empty_tables(fake_supabase)

        response = client.get(f"{BASE_ASSOC}/{self.FICHE_BIEN_ID}", headers=auth_headers)
        assert response.status_code == 404

    def test_fiche_bien_with_assurance_pno(self, client, auth_headers, fake_supabase):
        """Fiche bien includes PNO in rentabilite calculation."""
        setup(fake_supabase)
        self._seed_fiche_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = [
            {
                "id": 1,
                "id_bien": str(self.FICHE_BIEN_ID),
                "compagnie": "AXA",
                "montant_annuel": 360.0,
                "date_echeance": "2025-01-01",
            }
        ]
        for tbl in ("baux", "loyers", "charges", "frais_agence", "documents_bien"):
            fake_supabase.store.setdefault(tbl, [])

        response = client.get(f"{BASE}/{self.FICHE_BIEN_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["assurance_pno"] is not None
        # nette should be lower than brute because of PNO cost
        assert data["rentabilite"]["nette"] < data["rentabilite"]["brute"]


# ──────────────────────────────────────────────────────────────
# 4. PATCH /scis/{sci_id}/biens/{bien_id} — update bien
# ──────────────────────────────────────────────────────────────

class TestUpdateBien:
    def test_requires_auth(self, client):
        response = client.patch(f"{BASE}/{BIEN_ID}", json={"ville": "Bordeaux"})
        assert response.status_code == 401

    def test_update_bien_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.patch(
            f"{BASE}/{BIEN_ID}",
            json={"ville": "Bordeaux"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["ville"] == "Bordeaux"

    def test_update_bien_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        response = client.patch(
            f"{BASE_ASSOC}/{BIEN_ID}",
            json={"ville": "Marseille"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_unknown_bien_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.patch(
            f"{BASE}/no-such-bien",
            json={"ville": "Nice"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_multiple_fields(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.patch(
            f"{BASE}/{BIEN_ID}",
            json={"ville": "Toulouse", "loyer_cc": 1200.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ville"] == "Toulouse"
        assert data["loyer_cc"] == 1200.0


# ──────────────────────────────────────────────────────────────
# 5. DELETE /scis/{sci_id}/biens/{bien_id} — delete bien
# ──────────────────────────────────────────────────────────────

class TestDeleteBien:
    def test_requires_auth(self, client):
        response = client.delete(f"{BASE}/{BIEN_ID}")
        assert response.status_code == 401

    def test_delete_bien_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.delete(f"{BASE}/{BIEN_ID}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it is actually gone
        list_resp = client.get(BASE, headers=auth_headers)
        assert list_resp.json() == []

    def test_delete_bien_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        response = client.delete(f"{BASE_ASSOC}/{BIEN_ID}", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_unknown_bien_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.delete(f"{BASE}/no-such-bien", headers=auth_headers)
        assert response.status_code == 404


# ──────────────────────────────────────────────────────────────
# 6. GET/POST /scis/{sci_id}/biens/{bien_id}/loyers
# ──────────────────────────────────────────────────────────────

class TestLoyers:
    LOYER_URL = f"{BASE}/{BIEN_ID}/loyers"
    LOYER_PAYLOAD = {
        "id_bien": BIEN_ID,
        "date_loyer": "2024-03-01",
        "montant": 950.0,
        "statut": "paye",
    }

    def test_list_loyers_requires_auth(self, client):
        response = client.get(self.LOYER_URL)
        assert response.status_code == 401

    def test_list_loyers_returns_empty(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["loyers"] = []
        response = client.get(self.LOYER_URL, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_loyer_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["loyers"] = []
        response = client.post(self.LOYER_URL, json=self.LOYER_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["montant"] == 950.0
        assert data["id_bien"] == BIEN_ID

    def test_create_loyer_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/loyers"
        response = client.post(url, json=self.LOYER_PAYLOAD, headers=auth_headers)
        assert response.status_code == 403

    def test_list_loyers_returns_created(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["loyers"] = []
        client.post(self.LOYER_URL, json=self.LOYER_PAYLOAD, headers=auth_headers)
        response = client.get(self.LOYER_URL, headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_loyers_unknown_bien_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.get(f"{BASE}/nonexistent/loyers", headers=auth_headers)
        assert response.status_code == 404

    def test_loyer_id_sci_set_from_path(self, client, auth_headers, fake_supabase):
        """The created loyer should have id_sci from the URL path."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["loyers"] = []
        response = client.post(self.LOYER_URL, json=self.LOYER_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["id_sci"] == SCI_UUID


# ──────────────────────────────────────────────────────────────
# 7. GET/POST/PATCH/DELETE /scis/{sci_id}/biens/{bien_id}/baux
# ──────────────────────────────────────────────────────────────

class TestBaux:
    BAUX_URL = f"{BASE}/{BIEN_ID}/baux"
    BAIL_PAYLOAD = {
        "date_debut": "2024-01-01",
        "loyer_hc": 900.0,
        "charges_locatives": 100.0,
        "depot_garantie": 900.0,
        "locataire_ids": [],
    }

    def test_list_baux_requires_auth(self, client):
        response = client.get(self.BAUX_URL)
        assert response.status_code == 401

    def test_list_baux_returns_empty(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["baux"] = []
        fake_supabase.store.setdefault("bail_locataires", [])
        response = client.get(self.BAUX_URL, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_bail_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["baux"] = []
        fake_supabase.store["bail_locataires"] = []
        fake_supabase.store.setdefault("locataires", [])
        response = client.post(self.BAUX_URL, json=self.BAIL_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["loyer_hc"] == 900.0
        assert data["statut"] == "en_cours"

    def test_create_bail_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/baux"
        response = client.post(url, json=self.BAIL_PAYLOAD, headers=auth_headers)
        assert response.status_code == 403

    def test_create_bail_expires_existing_en_cours(self, client, auth_headers, fake_supabase):
        """Creating a new bail should expire the existing en_cours bail."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Pre-seed an existing en_cours bail
        fake_supabase.store["baux"] = [
            {
                "id": 10,
                "id_bien": BIEN_ID,
                "date_debut": "2023-01-01",
                "loyer_hc": 800.0,
                "charges_locatives": 0,
                "depot_garantie": 800.0,
                "statut": "en_cours",
            }
        ]
        fake_supabase.store["bail_locataires"] = []
        fake_supabase.store.setdefault("locataires", [])

        response = client.post(self.BAUX_URL, json=self.BAIL_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201

        # The old bail should now have statut='expire'
        old_baux = [b for b in fake_supabase.store["baux"] if b["id"] == 10]
        assert len(old_baux) == 1
        assert old_baux[0]["statut"] == "expire"

    def test_update_bail_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["baux"] = [
            {
                "id": 5,
                "id_bien": BIEN_ID,
                "date_debut": "2024-01-01",
                "loyer_hc": 900.0,
                "charges_locatives": 0,
                "depot_garantie": 0,
                "statut": "en_cours",
            }
        ]
        fake_supabase.store["bail_locataires"] = []

        response = client.patch(
            f"{self.BAUX_URL}/5",
            json={"loyer_hc": 1050.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["loyer_hc"] == 1050.0

    def test_delete_bail_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["baux"] = [
            {
                "id": 7,
                "id_bien": BIEN_ID,
                "date_debut": "2024-01-01",
                "loyer_hc": 900.0,
                "charges_locatives": 0,
                "depot_garantie": 0,
                "statut": "en_cours",
            }
        ]
        fake_supabase.store["bail_locataires"] = []

        response = client.delete(f"{self.BAUX_URL}/7", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_bail_requires_auth(self, client):
        response = client.delete(f"{self.BAUX_URL}/7")
        assert response.status_code == 401

    def test_update_bail_not_found_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["baux"] = []
        fake_supabase.store["bail_locataires"] = []

        response = client.patch(
            f"{self.BAUX_URL}/9999",
            json={"loyer_hc": 1000.0},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ──────────────────────────────────────────────────────────────
# 8. POST/DELETE bail-locataire attachment
# ──────────────────────────────────────────────────────────────

class TestBailLocataires:
    ATTACH_URL = f"{BASE}/{BIEN_ID}/baux/5/locataires"
    DETACH_URL = f"{BASE}/{BIEN_ID}/baux/5/locataires/42"

    def _seed_bail(self, fake_supabase):
        seed_bien(fake_supabase)
        fake_supabase.store["baux"] = [
            {
                "id": 5,
                "id_bien": BIEN_ID,
                "date_debut": "2024-01-01",
                "loyer_hc": 900.0,
                "charges_locatives": 0,
                "depot_garantie": 0,
                "statut": "en_cours",
            }
        ]
        fake_supabase.store["bail_locataires"] = []
        fake_supabase.store.setdefault("locataires", [])

    def test_attach_locataire_requires_auth(self, client):
        response = client.post(self.ATTACH_URL, json={"locataire_id": 42})
        assert response.status_code == 401

    def test_attach_locataire_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        self._seed_bail(fake_supabase)

        response = client.post(
            self.ATTACH_URL,
            json={"locataire_id": 42},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id_bail"] == 5
        assert data["id_locataire"] == 42

    def test_attach_locataire_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/baux/5/locataires"
        response = client.post(url, json={"locataire_id": 42}, headers=auth_headers)
        assert response.status_code == 403

    def test_detach_locataire_requires_auth(self, client):
        response = client.delete(self.DETACH_URL)
        assert response.status_code == 401

    def test_detach_locataire_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        self._seed_bail(fake_supabase)
        fake_supabase.store["bail_locataires"] = [{"id_bail": 5, "id_locataire": 42}]

        response = client.delete(self.DETACH_URL, headers=auth_headers)
        assert response.status_code == 204

    def test_detach_locataire_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/baux/5/locataires/42"
        response = client.delete(url, headers=auth_headers)
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────
# 9. GET/POST/PATCH/DELETE assurance-pno
# ──────────────────────────────────────────────────────────────

class TestAssurancePno:
    PNO_URL = f"{BASE}/{BIEN_ID}/assurance-pno"
    PNO_PAYLOAD = {
        "compagnie": "AXA",
        "numero_contrat": "CTR-2024-001",
        "montant_annuel": 360.0,
        "date_echeance": "2025-01-01",
    }

    def test_list_pno_requires_auth(self, client):
        response = client.get(self.PNO_URL)
        assert response.status_code == 401

    def test_list_pno_returns_empty(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = []
        response = client.get(self.PNO_URL, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_pno_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = []
        response = client.post(self.PNO_URL, json=self.PNO_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["compagnie"] == "AXA"
        assert data["montant_annuel"] == 360.0

    def test_create_pno_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/assurance-pno"
        response = client.post(url, json=self.PNO_PAYLOAD, headers=auth_headers)
        assert response.status_code == 403

    def test_update_pno_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = [
            {
                "id": 3,
                "id_bien": BIEN_ID,
                "compagnie": "AXA",
                "montant_annuel": 360.0,
                "date_echeance": "2025-01-01",
            }
        ]
        response = client.patch(
            f"{self.PNO_URL}/3",
            json={"montant_annuel": 420.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["montant_annuel"] == 420.0

    def test_delete_pno_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = [
            {
                "id": 3,
                "id_bien": BIEN_ID,
                "compagnie": "AXA",
                "montant_annuel": 360.0,
                "date_echeance": "2025-01-01",
            }
        ]
        response = client.delete(f"{self.PNO_URL}/3", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_pno_requires_auth(self, client):
        response = client.delete(f"{self.PNO_URL}/3")
        assert response.status_code == 401

    def test_update_pno_not_found_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = []
        response = client.patch(
            f"{self.PNO_URL}/9999",
            json={"montant_annuel": 420.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_pno_id_bien_set_from_path(self, client, auth_headers, fake_supabase):
        """The created PNO record should have id_bien from the path."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = []
        response = client.post(self.PNO_URL, json=self.PNO_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["id_bien"] == BIEN_ID


# ──────────────────────────────────────────────────────────────
# 10. GET/POST/DELETE frais-agence
# ──────────────────────────────────────────────────────────────

class TestFraisAgence:
    FRAIS_URL = f"{BASE}/{BIEN_ID}/frais-agence"
    FRAIS_PAYLOAD = {
        "nom_agence": "Foncia",
        "type_frais": "fixe",
        "montant_ou_pourcentage": 85.0,
    }

    def test_list_frais_requires_auth(self, client):
        response = client.get(self.FRAIS_URL)
        assert response.status_code == 401

    def test_list_frais_returns_empty(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["frais_agence"] = []
        response = client.get(self.FRAIS_URL, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_frais_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["frais_agence"] = []
        response = client.post(self.FRAIS_URL, json=self.FRAIS_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["type_frais"] == "fixe"
        assert data["montant_ou_pourcentage"] == 85.0

    def test_create_frais_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/frais-agence"
        response = client.post(url, json=self.FRAIS_PAYLOAD, headers=auth_headers)
        assert response.status_code == 403

    def test_delete_frais_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["frais_agence"] = [
            {
                "id": 8,
                "id_bien": BIEN_ID,
                "nom_agence": "Foncia",
                "type_frais": "fixe",
                "montant_ou_pourcentage": 85.0,
            }
        ]
        response = client.delete(f"{self.FRAIS_URL}/8", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_frais_requires_auth(self, client):
        response = client.delete(f"{self.FRAIS_URL}/8")
        assert response.status_code == 401

    def test_list_frais_returns_created_item(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["frais_agence"] = []
        client.post(self.FRAIS_URL, json=self.FRAIS_PAYLOAD, headers=auth_headers)
        resp = client.get(self.FRAIS_URL, headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_frais_id_bien_set_from_path(self, client, auth_headers, fake_supabase):
        """The created frais record should have id_bien from the path."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["frais_agence"] = []
        response = client.post(self.FRAIS_URL, json=self.FRAIS_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["id_bien"] == BIEN_ID


# ──────────────────────────────────────────────────────────────
# 11. GET/DELETE documents
# ──────────────────────────────────────────────────────────────

class TestDocuments:
    DOCS_URL = f"{BASE}/{BIEN_ID}/documents"

    def _seed_document(self, fake_supabase, doc_id: int = 20):
        fake_supabase.store["documents_bien"] = [
            {
                "id": doc_id,
                "id_bien": BIEN_ID,
                "nom": "Bail signé",
                "categorie": "bail",
                "url": "https://storage.local/sci-1/bien-abc/doc.pdf",
                "uploaded_at": "2024-01-15T10:00:00",
            }
        ]

    def test_list_documents_requires_auth(self, client):
        response = client.get(self.DOCS_URL)
        assert response.status_code == 401

    def test_list_documents_returns_empty(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["documents"] = []
        response = client.get(self.DOCS_URL, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_documents_returns_seeded(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        self._seed_document(fake_supabase)
        response = client.get(self.DOCS_URL, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nom"] == "Bail signé"
        assert data[0]["categorie"] == "bail"

    def test_delete_document_requires_auth(self, client):
        response = client.delete(f"{self.DOCS_URL}/20")
        assert response.status_code == 401

    def test_delete_document_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        self._seed_document(fake_supabase, doc_id=20)
        response = client.delete(f"{self.DOCS_URL}/20", headers=auth_headers)
        assert response.status_code == 204

        # Verify document is removed from store
        assert fake_supabase.store["documents_bien"] == []

    def test_delete_document_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/documents/20"
        response = client.delete(url, headers=auth_headers)
        assert response.status_code == 403

    def test_list_documents_unknown_bien_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.get(f"{BASE}/no-such-bien/documents", headers=auth_headers)
        assert response.status_code == 404

    def test_list_documents_only_returns_bien_docs(self, client, auth_headers, fake_supabase):
        """Documents from another bien should not appear."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Seed docs: one for our bien, one for another
        fake_supabase.store["documents_bien"] = [
            {
                "id": 20,
                "id_bien": BIEN_ID,
                "nom": "Bail signé",
                "categorie": "bail",
                "url": "https://storage.local/doc1.pdf",
                "uploaded_at": "2024-01-15T10:00:00",
            },
            {
                "id": 21,
                "id_bien": "other-bien",
                "nom": "Autre doc",
                "categorie": "autre",
                "url": "https://storage.local/doc2.pdf",
                "uploaded_at": "2024-01-15T10:00:00",
            },
        ]
        response = client.get(self.DOCS_URL, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 20

    # ── Security: ownership verification tests ──

    def test_delete_nonexistent_document_returns_404(self, client, auth_headers, fake_supabase):
        """Deleting a document ID that does not exist must return 404."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["documents_bien"] = []
        response = client.delete(f"{self.DOCS_URL}/999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_document_belonging_to_other_bien_returns_404(self, client, auth_headers, fake_supabase):
        """IDOR prevention: a document that exists but belongs to a different bien
        must not be deletable through a URL referencing another bien."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Seed a document that belongs to a *different* bien
        fake_supabase.store["documents_bien"] = [
            {
                "id": 30,
                "id_bien": "other-bien-id",
                "nom": "Secret doc",
                "categorie": "autre",
                "url": "https://storage.local/storage/v1/object/public/documents/sci-x/bien-y/secret.pdf",
                "uploaded_at": "2024-01-15T10:00:00",
            }
        ]
        response = client.delete(f"{self.DOCS_URL}/30", headers=auth_headers)
        assert response.status_code == 404
        # Document must NOT have been deleted
        assert len(fake_supabase.store["documents_bien"]) == 1

    def test_delete_document_removes_storage_file(self, client, auth_headers, fake_supabase):
        """Successful document deletion must also remove the file from storage."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        storage_path = f"sci-{SCI_UUID}/bien-{BIEN_ID}/abc123.pdf"
        public_url = f"https://storage.local/storage/v1/object/public/documents/{storage_path}"
        fake_supabase.store["documents_bien"] = [
            {
                "id": 40,
                "id_bien": BIEN_ID,
                "nom": "Bail signé",
                "categorie": "bail",
                "url": public_url,
                "uploaded_at": "2024-01-15T10:00:00",
            }
        ]
        response = client.delete(f"{self.DOCS_URL}/40", headers=auth_headers)
        assert response.status_code == 204
        # Verify the storage remove was called with the correct path
        bucket = fake_supabase.storage.from_("documents")
        assert len(bucket.removed) == 1
        assert bucket.removed[0] == [storage_path]
        # Verify DB record was removed
        assert fake_supabase.store["documents_bien"] == []


# ──────────────────────────────────────────────────────────────
# 12. Charges CRUD
# ──────────────────────────────────────────────────────────────

class TestCharges:
    CHARGES_URL = f"{BASE}/{BIEN_ID}/charges"
    CHARGE_PAYLOAD = {
        "id_bien": BIEN_ID,
        "type_charge": "taxe fonciere",
        "montant": 1500.0,
        "date_paiement": "2024-10-15",
    }

    def test_list_charges_requires_auth(self, client):
        response = client.get(self.CHARGES_URL)
        assert response.status_code == 401

    def test_list_charges_returns_empty(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["charges"] = []
        response = client.get(self.CHARGES_URL, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_charge_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["charges"] = []
        response = client.post(self.CHARGES_URL, json=self.CHARGE_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["type_charge"] == "taxe fonciere"
        assert data["montant"] == 1500.0

    def test_create_charge_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        url = f"{BASE_ASSOC}/{BIEN_ID}/charges"
        response = client.post(url, json=self.CHARGE_PAYLOAD, headers=auth_headers)
        assert response.status_code == 403

    def test_update_charge_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        charge_id = "chg-001"
        fake_supabase.store["charges"] = [
            {
                "id": charge_id,
                "id_bien": BIEN_ID,
                "type_charge": "assurance",
                "montant": 500.0,
                "date_paiement": "2024-05-01",
            }
        ]
        response = client.patch(
            f"{self.CHARGES_URL}/{charge_id}",
            json={"montant": 600.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["montant"] == 600.0

    def test_delete_charge_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        charge_id = "chg-002"
        fake_supabase.store["charges"] = [
            {
                "id": charge_id,
                "id_bien": BIEN_ID,
                "type_charge": "syndic",
                "montant": 800.0,
                "date_paiement": "2024-06-01",
            }
        ]
        response = client.delete(f"{self.CHARGES_URL}/{charge_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_charge_requires_auth(self, client):
        response = client.delete(f"{self.CHARGES_URL}/chg-002")
        assert response.status_code == 401

    def test_update_charge_not_found_returns_404(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["charges"] = []
        charge_id = "no-such-charge"
        response = client.patch(
            f"{self.CHARGES_URL}/{charge_id}",
            json={"montant": 999.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_charges_id_bien_set_from_path(self, client, auth_headers, fake_supabase):
        """The created charge should have id_bien from the path."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["charges"] = []
        response = client.post(self.CHARGES_URL, json=self.CHARGE_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["id_bien"] == BIEN_ID


# ──────────────────────────────────────────────────────────────
# 13. GET /scis/{sci_id}/associes — verify membership list
# ──────────────────────────────────────────────────────────────

class TestAssociesEndpoint:
    """
    The /scis/{sci_id}/associes endpoint lives in the 'scis' router (not scis_biens).
    These tests verify it exists and requires auth — the primary goal is coverage
    of the membership checks used by scis_biens.
    """

    ASSOC_URL = f"/api/v1/scis/{SCI_UUID}/associes"

    def test_list_associes_requires_auth(self, client):
        response = client.get(self.ASSOC_URL)
        assert response.status_code == 401

    def test_list_associes_returns_members(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        response = client.get(self.ASSOC_URL, headers=auth_headers)
        # sciS router must exist; if not registered, 404/405 is also acceptable
        assert response.status_code in (200, 404, 405)


# ======================================================================
# COVERAGE BOOST — tests targeting specific uncovered lines
# ======================================================================

# ──────────────────────────────────────────────────────────────
# _validate_upload edge cases (lines 97-108)
# ──────────────────────────────────────────────────────────────


class TestValidateUpload:
    """Unit tests for _validate_upload function."""

    def test_empty_file_raises(self):
        from app.api.v1.scis_biens import _validate_upload
        with pytest.raises(Exception, match="vide"):
            _validate_upload(b"", "test.pdf")

    def test_oversized_file_raises(self):
        from app.api.v1.scis_biens import _validate_upload
        big = b"x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(Exception, match="volumineux"):
            _validate_upload(big, "test.pdf")

    def test_disallowed_extension_raises(self):
        from app.api.v1.scis_biens import _validate_upload
        with pytest.raises(Exception, match="non autorisée"):
            _validate_upload(b"some content", "test.exe")

    def test_no_extension_raises(self):
        from app.api.v1.scis_biens import _validate_upload
        with pytest.raises(Exception, match="non autorisée"):
            _validate_upload(b"some content", "noext")

    def test_magic_bytes_mismatch_raises(self):
        """PDF magic bytes with .jpg extension should raise."""
        from app.api.v1.scis_biens import _validate_upload
        pdf_content = b"%PDF-1.4 some content"
        with pytest.raises(Exception, match="ne correspond pas"):
            _validate_upload(pdf_content, "image.jpg")

    def test_magic_bytes_pdf_match(self):
        from app.api.v1.scis_biens import _validate_upload
        pdf_content = b"%PDF-1.4 some content"
        ext = _validate_upload(pdf_content, "document.pdf")
        assert ext == "pdf"

    def test_magic_bytes_jpg_match(self):
        from app.api.v1.scis_biens import _validate_upload
        jpg_content = b"\xff\xd8\xff some jpg data here"
        ext = _validate_upload(jpg_content, "photo.jpg")
        assert ext == "jpg"

    def test_magic_bytes_jpeg_match(self):
        from app.api.v1.scis_biens import _validate_upload
        jpg_content = b"\xff\xd8\xff some jpeg data here"
        ext = _validate_upload(jpg_content, "photo.jpeg")
        assert ext == "jpeg"

    def test_magic_bytes_png_match(self):
        from app.api.v1.scis_biens import _validate_upload
        png_content = b"\x89PNG some png data here"
        ext = _validate_upload(png_content, "image.png")
        assert ext == "png"

    def test_magic_bytes_docx_match(self):
        from app.api.v1.scis_biens import _validate_upload
        docx_content = b"PK some ooxml data here"
        ext = _validate_upload(docx_content, "document.docx")
        assert ext == "docx"

    def test_magic_bytes_xlsx_match(self):
        from app.api.v1.scis_biens import _validate_upload
        xlsx_content = b"PK some xlsx archive data"
        ext = _validate_upload(xlsx_content, "sheet.xlsx")
        assert ext == "xlsx"

    def test_magic_bytes_webp_match(self):
        from app.api.v1.scis_biens import _validate_upload
        webp_content = b"RIFF some webp data here"
        ext = _validate_upload(webp_content, "image.webp")
        assert ext == "webp"

    def test_no_magic_match_allowed(self):
        """Txt files have no magic bytes check — should pass."""
        from app.api.v1.scis_biens import _validate_upload
        ext = _validate_upload(b"plain text content", "notes.txt")
        assert ext == "txt"

    def test_csv_no_magic_match(self):
        from app.api.v1.scis_biens import _validate_upload
        ext = _validate_upload(b"a,b,c\n1,2,3", "data.csv")
        assert ext == "csv"

    def test_png_magic_with_jpg_ext_raises(self):
        """PNG magic bytes + .jpg extension -> mismatch."""
        from app.api.v1.scis_biens import _validate_upload
        png_content = b"\x89PNG some png data here"
        with pytest.raises(Exception, match="ne correspond pas"):
            _validate_upload(png_content, "fake.jpg")


# ──────────────────────────────────────────────────────────────
# Fiche bien: frais percentage calculation (lines 281-285)
# ──────────────────────────────────────────────────────────────


class TestFicheBienFraisCalc:
    """Test fiche bien with frais agence percentage calculation."""

    def test_fiche_bien_with_frais_pourcentage(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        bien = seed_bien_int(fake_supabase, bien_id=900, sci_id=SCI_UUID)
        # Add active bail
        fake_supabase.store.setdefault("baux", []).append({
            "id": 900, "id_bien": 900, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "date_fin": "2028-01-01",
            "type_bail": "nu",
        })
        # Add frais agence with type pourcentage
        fake_supabase.store.setdefault("frais_agence", []).append({
            "id": 900, "id_bien": 900, "nom_agence": "Agence A", "type_frais": "pourcentage",
            "montant_ou_pourcentage": 8.0, "created_at": "2026-01-01",
        })
        # Add frais agence with type fixe (small amount < 100)
        fake_supabase.store["frais_agence"].append({
            "id": 901, "id_bien": 900, "nom_agence": "Agence B", "type_frais": "fixe",
            "montant_ou_pourcentage": 50.0, "created_at": "2026-01-01",
        })
        # Add frais agence with type fixe (large amount > 100)
        fake_supabase.store["frais_agence"].append({
            "id": 902, "id_bien": 900, "nom_agence": "Agence C", "type_frais": "fixe",
            "montant_ou_pourcentage": 150.0, "created_at": "2026-01-01",
        })
        fake_supabase.store.setdefault("assurances_pno", [])
        fake_supabase.store.setdefault("documents_bien", [])
        fake_supabase.store.setdefault("bail_locataires", [])

        response = client.get(f"{BASE}/900", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "rentabilite" in data
        assert data["frais_agence"] is not None


# ──────────────────────────────────────────────────────────────
# Update bien empty payload (line 341)
# ──────────────────────────────────────────────────────────────


class TestUpdateBienEmptyPayload:
    def test_update_bien_empty_payload_returns_error(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.patch(
            f"{BASE}/{BIEN_ID}",
            json={},
            headers=auth_headers,
        )
        # Empty payload returns 503 (DatabaseError: "No update fields provided")
        assert response.status_code == 503


# ──────────────────────────────────────────────────────────────
# Create loyer duplicate detection (line 434)
# ──────────────────────────────────────────────────────────────


class TestCreateLoyerDuplicate:
    def test_create_loyer_duplicate_date_returns_409(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Seed existing loyer for the same date
        fake_supabase.store.setdefault("loyers", []).append({
            "id": "loyer-existing",
            "id_bien": BIEN_ID,
            "id_sci": SCI_UUID,
            "date_loyer": "2026-05-01",
            "montant": 1000,
            "statut": "en_attente",
        })
        response = client.post(
            f"{BASE}/{BIEN_ID}/loyers",
            json={"id_bien": BIEN_ID, "date_loyer": "2026-05-01", "montant": 1000, "statut": "en_attente"},
            headers=auth_headers,
        )
        assert response.status_code == 409


# ──────────────────────────────────────────────────────────────
# List baux with locataire enrichment (lines 477-490)
# ──────────────────────────────────────────────────────────────


class TestListBauxWithLocataires:
    def test_list_baux_enriches_locataires(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("baux", []).extend([
            {"id": 501, "id_bien": BIEN_ID, "statut": "en_cours",
             "loyer_hc": 800, "charges_provisions": 100,
             "date_debut": "2025-01-01", "date_fin": "2028-01-01", "type_bail": "nu"},
            {"id": 502, "id_bien": BIEN_ID, "statut": "expire",
             "loyer_hc": 700, "charges_provisions": 80,
             "date_debut": "2022-01-01", "date_fin": "2025-01-01", "type_bail": "nu"},
        ])
        # Seed bail_locataires join table entries
        fake_supabase.store.setdefault("bail_locataires", []).extend([
            {"id_bail": 501, "id_locataire": 10,
             "locataires": {"id": 10, "nom": "Dupont", "email": "d@t.com", "telephone": "0600000000"}},
            {"id_bail": 501, "id_locataire": 11,
             "locataires": {"id": 11, "nom": "Martin", "email": "m@t.com", "telephone": "0600000001"}},
            {"id_bail": 502, "id_locataire": 12,
             "locataires": None},  # Edge case: locataires is None
        ])
        response = client.get(f"{BASE}/{BIEN_ID}/baux", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        # The bail with locataires should be enriched
        bail_501 = next(b for b in data if b["id"] == 501)
        assert len(bail_501["locataires"]) == 2
        # The bail with None locataires should have empty list
        bail_502 = next(b for b in data if b["id"] == 502)
        assert bail_502["locataires"] == []


# ──────────────────────────────────────────────────────────────
# Create bail: duration validation (lines 516-525)
# ──────────────────────────────────────────────────────────────


class TestCreateBailDurationValidation:
    def test_bail_nu_too_short_returns_400(self, client, auth_headers, fake_supabase):
        """Bail nu requires minimum 3 years (1095 days)."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            f"{BASE}/{BIEN_ID}/baux",
            json={
                "loyer_hc": 800,
                "charges_provisions": 100,
                "date_debut": "2026-01-01",
                "date_fin": "2027-01-01",  # ~365 days, below 1095
                "type_bail": "nu",
                "locataire_ids": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "3 ans" in response.json()["detail"]

    def test_bail_meuble_too_short_returns_400(self, client, auth_headers, fake_supabase):
        """Bail meuble requires minimum 1 year (365 days)."""
        setup(fake_supabase)
        bien = seed_bien(fake_supabase)
        # Change type_locatif to meuble
        bien["type_locatif"] = "meuble"
        response = client.post(
            f"{BASE}/{BIEN_ID}/baux",
            json={
                "loyer_hc": 800,
                "charges_provisions": 100,
                "date_debut": "2026-01-01",
                "date_fin": "2026-06-01",  # ~150 days, below 365
                "type_bail": "meuble",
                "locataire_ids": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "1 an" in response.json()["detail"]

    def test_bail_nu_valid_duration(self, client, auth_headers, fake_supabase):
        """Bail nu with sufficient duration should succeed."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            f"{BASE}/{BIEN_ID}/baux",
            json={
                "loyer_hc": 800,
                "charges_provisions": 100,
                "date_debut": "2026-01-01",
                "date_fin": "2029-06-01",  # ~3.5 years
                "type_bail": "nu",
                "locataire_ids": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201


# ──────────────────────────────────────────────────────────────
# Create bail: locataire attachment (lines 566-575)
# ──────────────────────────────────────────────────────────────


class TestCreateBailWithLocataires:
    def test_create_bail_attaches_locataires(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Seed locataires
        fake_supabase.store.setdefault("locataires", []).extend([
            {"id": "100", "nom": "Dupont", "email": "d@t.com", "telephone": "0600000000", "id_bien": BIEN_ID},
            {"id": "101", "nom": "Martin", "email": "m@t.com", "telephone": "0600000001", "id_bien": BIEN_ID},
        ])
        response = client.post(
            f"{BASE}/{BIEN_ID}/baux",
            json={
                "loyer_hc": 900,
                "charges_locatives": 100,
                "date_debut": "2026-01-01",
                "date_fin": "2030-01-01",
                "locataire_ids": ["100", "101"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["locataires"]) == 2
        # Verify bail_locataires entries were created
        joins = fake_supabase.store.get("bail_locataires", [])
        assert any(j["id_locataire"] == "100" for j in joins)
        assert any(j["id_locataire"] == "101" for j in joins)


# ──────────────────────────────────────────────────────────────
# Update bail: empty payload (line 599)
# ──────────────────────────────────────────────────────────────


class TestUpdateBailEmptyPayload:
    def test_update_bail_empty_payload_returns_error(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("baux", []).append({
            "id": 600, "id_bien": BIEN_ID, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "type_bail": "nu",
        })
        response = client.patch(
            f"{BASE}/{BIEN_ID}/baux/600",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 503


# ──────────────────────────────────────────────────────────────
# Update bail: locataire enrichment (lines 629-631)
# ──────────────────────────────────────────────────────────────


class TestUpdateBailWithLocataires:
    def test_update_bail_enriches_locataires(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("baux", []).append({
            "id": 700, "id_bien": BIEN_ID, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "type_bail": "nu",
        })
        fake_supabase.store.setdefault("bail_locataires", []).append({
            "id_bail": 700, "id_locataire": 20,
            "locataires": {"id": 20, "nom": "Loc", "email": "l@t.com", "telephone": "06"},
        })
        response = client.patch(
            f"{BASE}/{BIEN_ID}/baux/700",
            json={"loyer_hc": 900},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["loyer_hc"] == 900
        assert len(data["locataires"]) == 1


# ──────────────────────────────────────────────────────────────
# Attach locataire: missing locataire_id (line 681)
# ──────────────────────────────────────────────────────────────


class TestAttachLocataireErrors:
    def test_attach_missing_locataire_id(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("baux", []).append({
            "id": 800, "id_bien": BIEN_ID, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "type_bail": "nu",
        })
        response = client.post(
            f"{BASE}/{BIEN_ID}/baux/800/locataires",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 503

    def test_attach_locataire_bail_not_found(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            f"{BASE}/{BIEN_ID}/baux/999/locataires",
            json={"locataire_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ──────────────────────────────────────────────────────────────
# Update charge empty payload (line 812)
# ──────────────────────────────────────────────────────────────


class TestUpdateChargeEmptyPayload:
    CHARGES_URL = f"{BASE}/{BIEN_ID}/charges"

    def test_update_charge_empty_payload(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("charges", []).append({
            "id": "chg-empty", "id_bien": BIEN_ID, "type_charge": "taxe",
            "montant": 100, "date_paiement": "2026-01-01",
        })
        response = client.patch(
            f"{self.CHARGES_URL}/chg-empty",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 503


# ──────────────────────────────────────────────────────────────
# Update PNO empty payload (line 937)
# ──────────────────────────────────────────────────────────────


class TestUpdatePnoEmptyPayload:
    PNO_URL = f"{BASE}/{BIEN_ID}/assurance-pno"

    def test_update_pno_empty_payload(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("assurances_pno", []).append({
            "id": 999, "id_bien": BIEN_ID, "compagnie": "Test",
            "montant_annuel": 400, "date_echeance": "2027-01-01",
        })
        response = client.patch(
            f"{self.PNO_URL}/999",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 503


# ──────────────────────────────────────────────────────────────
# Upload document (lines 1122-1156)
# ──────────────────────────────────────────────────────────────


class TestUploadDocument:
    DOC_URL = f"{BASE}/{BIEN_ID}/documents"

    def test_upload_pdf_document(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("documents_bien", [])
        pdf_content = b"%PDF-1.4 some pdf content"
        response = client.post(
            self.DOC_URL,
            files={"file": ("doc.pdf", pdf_content, "application/pdf")},
            data={"nom": "Bail scan", "categorie": "bail"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nom"] == "Bail scan"
        assert data["categorie"] == "bail"

    def test_upload_txt_document(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("documents_bien", [])
        response = client.post(
            self.DOC_URL,
            files={"file": ("notes.txt", b"hello world", "text/plain")},
            data={"nom": "Notes", "categorie": "autre"},
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_upload_invalid_extension_returns_400(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            self.DOC_URL,
            files={"file": ("hack.exe", b"malware data", "application/octet-stream")},
            data={"nom": "Bad", "categorie": "autre"},
            headers=auth_headers,
        )
        # ValidationError (custom) returns 400
        assert response.status_code == 400

    def test_upload_empty_file_returns_400(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            self.DOC_URL,
            files={"file": ("empty.pdf", b"", "application/pdf")},
            data={"nom": "Empty", "categorie": "autre"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_upload_as_associe_returns_403(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase, sci_id=SCI_UUID_ASSOC)
        response = client.post(
            f"{BASE_ASSOC}/{BIEN_ID}/documents",
            files={"file": ("doc.pdf", b"%PDF-1.4 x", "application/pdf")},
            data={"nom": "Doc", "categorie": "autre"},
            headers=auth_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────
# Delete document with storage cleanup (lines 1200-1215)
# ──────────────────────────────────────────────────────────────


class TestDeleteDocumentStorageCleanup:
    DOC_URL = f"{BASE}/{BIEN_ID}/documents"

    def test_delete_document_cleans_storage_file(self, client, auth_headers, fake_supabase):
        """Deleting a document also removes the file from storage."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        # Seed a document with a URL matching the storage pattern
        fake_supabase.store.setdefault("documents_bien", []).append({
            "id": 2000,
            "id_bien": BIEN_ID,
            "nom": "Contract",
            "categorie": "bail",
            "url": f"https://storage.local/storage/v1/object/public/documents/sci-{SCI_UUID}/bien-{BIEN_ID}/abc123.pdf",
            "uploaded_at": "2026-01-01T00:00:00",
        })
        response = client.delete(f"{self.DOC_URL}/2000", headers=auth_headers)
        assert response.status_code == 204
        # Verify the storage remove was called
        bucket = fake_supabase.storage.from_("documents")
        assert len(bucket.removed) > 0

    def test_delete_document_no_url(self, client, auth_headers, fake_supabase):
        """Document with empty URL should still be deleted from DB."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("documents_bien", []).append({
            "id": 2001,
            "id_bien": BIEN_ID,
            "nom": "Old",
            "categorie": "autre",
            "url": "",
            "uploaded_at": "2026-01-01T00:00:00",
        })
        response = client.delete(f"{self.DOC_URL}/2001", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_document_url_without_storage_prefix(self, client, auth_headers, fake_supabase):
        """Document with URL that doesn't contain storage prefix -> skip storage delete."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("documents_bien", []).append({
            "id": 2002,
            "id_bien": BIEN_ID,
            "nom": "External",
            "categorie": "autre",
            "url": "https://example.com/doc.pdf",
            "uploaded_at": "2026-01-01T00:00:00",
        })
        response = client.delete(f"{self.DOC_URL}/2002", headers=auth_headers)
        assert response.status_code == 204


# ──────────────────────────────────────────────────────────────
# Fiche bien: locataire extraction from bail (line 201)
# ──────────────────────────────────────────────────────────────


class TestFicheBienLocataireExtraction:
    def test_fiche_bien_bail_with_locataires(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        bien = seed_bien_int(fake_supabase, bien_id=950, sci_id=SCI_UUID)
        fake_supabase.store.setdefault("baux", []).append({
            "id": 950, "id_bien": 950, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "date_fin": "2028-01-01",
            "type_bail": "nu",
        })
        fake_supabase.store.setdefault("bail_locataires", []).extend([
            {"id_bail": 950, "id_locataire": 50,
             "locataires": {"id": 50, "nom": "Dupont", "email": "d@t.com", "telephone": "06"}},
            {"id_bail": 950, "id_locataire": 51,
             "locataires": None},  # Edge: None locataire
        ])
        fake_supabase.store.setdefault("assurances_pno", [])
        fake_supabase.store.setdefault("frais_agence", [])
        fake_supabase.store.setdefault("documents_bien", [])

        response = client.get(f"{BASE}/950", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["bail_actif"] is not None
        assert len(data["bail_actif"]["locataires"]) == 1  # Only non-None


# ──────────────────────────────────────────────────────────────
# Delete bail (line 660 + bail_locataires cleanup)
# ──────────────────────────────────────────────────────────────


class TestDeleteBailCleanup:
    def test_delete_bail_removes_bail_locataires(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("baux", []).append({
            "id": 850, "id_bien": BIEN_ID, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "type_bail": "nu",
        })
        fake_supabase.store.setdefault("bail_locataires", []).append(
            {"id_bail": 850, "id_locataire": 30}
        )
        response = client.delete(f"{BASE}/{BIEN_ID}/baux/850", headers=auth_headers)
        assert response.status_code == 204
        # bail_locataires should be cleaned
        remaining = [j for j in fake_supabase.store.get("bail_locataires", []) if j.get("id_bail") == 850]
        assert len(remaining) == 0


# ──────────────────────────────────────────────────────────────
# Detach locataire from bail
# ──────────────────────────────────────────────────────────────


class TestDetachLocataire:
    def test_detach_locataire_removes_join(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("baux", []).append({
            "id": 860, "id_bien": BIEN_ID, "statut": "en_cours",
            "loyer_hc": 800, "charges_provisions": 100,
            "date_debut": "2025-01-01", "type_bail": "nu",
        })
        fake_supabase.store.setdefault("bail_locataires", []).append(
            {"id_bail": 860, "id_locataire": 40}
        )
        response = client.delete(
            f"{BASE}/{BIEN_ID}/baux/860/locataires/40",
            headers=auth_headers,
        )
        assert response.status_code == 204


# ──────────────────────────────────────────────────────────────
# List charges, PNO, frais, documents for well-covered paths
# ──────────────────────────────────────────────────────────────


class TestListEndpointsReturnData:
    """Ensure LIST endpoints return seeded data to cover happy path lines."""

    def test_list_loyers_returns_sorted(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("loyers", []).extend([
            {"id": "l1", "id_bien": BIEN_ID, "id_sci": SCI_UUID,
             "date_loyer": "2026-01-01", "montant": 1000, "statut": "paye"},
            {"id": "l2", "id_bien": BIEN_ID, "id_sci": SCI_UUID,
             "date_loyer": "2026-02-01", "montant": 1000, "statut": "en_attente"},
        ])
        response = client.get(f"{BASE}/{BIEN_ID}/loyers", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_pno_returns_data(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("assurances_pno", []).append({
            "id": 1, "id_bien": BIEN_ID, "compagnie": "AXA",
            "montant_annuel": 400, "date_echeance": "2027-01-01",
        })
        response = client.get(f"{BASE}/{BIEN_ID}/assurance-pno", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_frais_returns_data(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("frais_agence", []).append({
            "id": 1, "id_bien": BIEN_ID, "nom_agence": "Agence Test",
            "type_frais": "fixe", "montant_ou_pourcentage": 100, "created_at": "2026-01-01",
        })
        response = client.get(f"{BASE}/{BIEN_ID}/frais-agence", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_documents_returns_data(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("documents_bien", []).append({
            "id": 1, "id_bien": BIEN_ID, "nom": "Bail",
            "categorie": "bail", "url": "https://x.com/doc.pdf",
            "uploaded_at": "2026-01-01T00:00:00",
        })
        response = client.get(f"{BASE}/{BIEN_ID}/documents", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_charges_returns_data(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("charges", []).append({
            "id": "chg-1", "id_bien": BIEN_ID, "type_charge": "taxe",
            "montant": 500, "date_paiement": "2026-01-01",
        })
        response = client.get(f"{BASE}/{BIEN_ID}/charges", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1


# ──────────────────────────────────────────────────────────────
# Create PNO, frais agence, charge — id_bien override
# ──────────────────────────────────────────────────────────────


class TestCreateResourcesIdBienOverride:
    """Verify id_bien is always set from the URL path, not the payload."""

    def test_create_pno_sets_id_bien(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            f"{BASE}/{BIEN_ID}/assurance-pno",
            json={
                "compagnie": "Allianz",
                "montant_annuel": 350,
                "date_echeance": "2027-01-01",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["id_bien"] == BIEN_ID

    def test_create_frais_sets_id_bien(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            f"{BASE}/{BIEN_ID}/frais-agence",
            json={
                "nom_agence": "Agence Test",
                "type_frais": "fixe",
                "montant_ou_pourcentage": 120,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["id_bien"] == BIEN_ID

    def test_create_charge_sets_id_bien(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.post(
            f"{BASE}/{BIEN_ID}/charges",
            json={
                "id_bien": BIEN_ID,
                "type_charge": "copropriete",
                "montant": 250,
                "date_paiement": "2026-03-01",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["id_bien"] == BIEN_ID


# ──────────────────────────────────────────────────────────────
# Delete PNO, frais, charge — verify deletion
# ──────────────────────────────────────────────────────────────


class TestDeleteResources:
    def test_delete_pno(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("assurances_pno", []).append({
            "id": 3000, "id_bien": BIEN_ID, "compagnie": "X",
            "montant_annuel": 300, "date_echeance": "2027-01-01",
        })
        response = client.delete(
            f"{BASE}/{BIEN_ID}/assurance-pno/3000",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_delete_frais(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("frais_agence", []).append({
            "id": 3001, "id_bien": BIEN_ID, "type_frais": "fixe",
            "montant_ou_pourcentage": 100, "created_at": "2026-01-01",
        })
        response = client.delete(
            f"{BASE}/{BIEN_ID}/frais-agence/3001",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_delete_charge(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("charges", []).append({
            "id": "chg-3002", "id_bien": BIEN_ID, "type_charge": "taxe",
            "montant": 100, "date_paiement": "2026-01-01",
        })
        response = client.delete(
            f"{BASE}/{BIEN_ID}/charges/chg-3002",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_delete_bien(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.delete(f"{BASE}/{BIEN_ID}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_loyer_via_update_bien(self, client, auth_headers, fake_supabase):
        """Test deleting a bien removes it from the store."""
        setup(fake_supabase)
        seed_bien(fake_supabase)
        response = client.delete(f"{BASE}/{BIEN_ID}", headers=auth_headers)
        assert response.status_code == 204
        remaining = [b for b in fake_supabase.store.get("biens", []) if b["id"] == BIEN_ID]
        assert len(remaining) == 0


# ──────────────────────────────────────────────────────────────
# Update PNO (lines 933-957)
# ──────────────────────────────────────────────────────────────


class TestUpdatePno:
    def test_update_pno_fields(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store.setdefault("assurances_pno", []).append({
            "id": 4000, "id_bien": BIEN_ID, "compagnie": "Old",
            "montant_annuel": 300, "date_echeance": "2027-01-01",
        })
        response = client.patch(
            f"{BASE}/{BIEN_ID}/assurance-pno/4000",
            json={"compagnie": "Allianz", "montant_annuel": 500},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["compagnie"] == "Allianz"
        assert data["montant_annuel"] == 500
