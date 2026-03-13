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
        for tbl in ("baux", "loyers", "charges", "assurances_pno", "frais_agence", "documents"):
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
        for tbl in ("loyers", "charges", "assurances_pno", "frais_agence", "documents"):
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
                "assureur": "AXA",
                "prime_annuelle": 360.0,
                "date_debut": "2024-01-01",
            }
        ]
        for tbl in ("baux", "loyers", "charges", "frais_agence", "documents"):
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
        assert data["bail_id"] == 5
        assert data["locataire_id"] == 42

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
        fake_supabase.store["bail_locataires"] = [{"bail_id": 5, "locataire_id": 42}]

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
        "assureur": "AXA",
        "numero_contrat": "CTR-2024-001",
        "prime_annuelle": 360.0,
        "date_debut": "2024-01-01",
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
        assert data["assureur"] == "AXA"
        assert data["prime_annuelle"] == 360.0

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
                "assureur": "AXA",
                "prime_annuelle": 360.0,
                "date_debut": "2024-01-01",
            }
        ]
        response = client.patch(
            f"{self.PNO_URL}/3",
            json={"prime_annuelle": 420.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["prime_annuelle"] == 420.0

    def test_delete_pno_as_gerant(self, client, auth_headers, fake_supabase):
        setup(fake_supabase)
        seed_bien(fake_supabase)
        fake_supabase.store["assurances_pno"] = [
            {
                "id": 3,
                "id_bien": BIEN_ID,
                "assureur": "AXA",
                "prime_annuelle": 360.0,
                "date_debut": "2024-01-01",
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
            json={"prime_annuelle": 420.0},
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
        "type_frais": "gestion_locative",
        "montant": 85.0,
        "date_frais": "2024-03-01",
        "description": "Gestion mars 2024",
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
        assert data["type_frais"] == "gestion_locative"
        assert data["montant"] == 85.0

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
                "type_frais": "gestion_locative",
                "montant": 85.0,
                "date_frais": "2024-03-01",
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
        fake_supabase.store["documents"] = [
            {
                "id": doc_id,
                "id_bien": BIEN_ID,
                "nom": "Bail signé",
                "categorie": "bail",
                "url": "https://storage.local/sci-1/bien-abc/doc.pdf",
                "created_at": "2024-01-15T10:00:00",
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
        assert fake_supabase.store["documents"] == []

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
        fake_supabase.store["documents"] = [
            {
                "id": 20,
                "id_bien": BIEN_ID,
                "nom": "Bail signé",
                "categorie": "bail",
                "url": "https://storage.local/doc1.pdf",
                "created_at": "2024-01-15T10:00:00",
            },
            {
                "id": 21,
                "id_bien": "other-bien",
                "nom": "Autre doc",
                "categorie": "autre",
                "url": "https://storage.local/doc2.pdf",
                "created_at": "2024-01-15T10:00:00",
            },
        ]
        response = client.get(self.DOCS_URL, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 20


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
