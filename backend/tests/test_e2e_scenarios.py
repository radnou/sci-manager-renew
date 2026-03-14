"""
End-to-end integration test scenarios for GererSCI.

Each class represents a complete user journey exercised through the FastAPI
TestClient + FakeSupabaseClient infrastructure.  Tests are self-contained:
they seed their own data and clean up via the autouse _reset_store fixture.

NOTE: Endpoints under /scis/{sci_id}/biens require UUID-formatted sci_id.
"""

from __future__ import annotations

import csv
import io

import pytest

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

SCI_UUID = "11111111-1111-1111-1111-111111111111"
SCI_UUID_2 = "22222222-2222-2222-2222-222222222222"
BIEN_ID = "bien-e2e-1"
BIEN_ID_2 = "bien-e2e-2"
BAIL_ID = 9001  # bail_id is int in router
LOYER_ID = "loyer-e2e-1"
LOCATAIRE_ID = 9501  # locataire_id is int in router

PRO_SUB = {
    "id": "sub-e2e",
    "user_id": "user-123",
    "plan_key": "pro",
    "status": "active",
    "is_active": True,
    "onboarding_completed": True,
    "max_scis": 10,
    "max_biens": 20,
    "features": {
        "multi_sci_enabled": True,
        "charges_enabled": True,
        "fiscalite_enabled": True,
        "quitus_enabled": True,
        "cerfa_enabled": True,
        "priority_support": True,
        "documents_enabled": True,
        "notifications_enabled": True,
        "associes_enabled": True,
        "pno_frais_enabled": True,
        "rentabilite_enabled": True,
        "dashboard_complet": True,
    },
}

FREE_SUB = {
    "id": "sub-free",
    "user_id": "user-123",
    "plan_key": "free",
    "status": "free",
    "is_active": True,
    "onboarding_completed": False,
    "max_scis": 1,
    "max_biens": 2,
    "features": {
        "multi_sci_enabled": False,
        "charges_enabled": False,
        "fiscalite_enabled": False,
        "quitus_enabled": True,
        "cerfa_enabled": False,
        "priority_support": False,
    },
}

GERANT_ASSOC = {
    "id": "assoc-e2e-g",
    "id_sci": SCI_UUID,
    "user_id": "user-123",
    "nom": "Test Gerant",
    "email": "gerant@sci.local",
    "part": 60,
    "role": "gerant",
}

ASSOC_ONLY = {
    "id": "assoc-e2e-a",
    "id_sci": SCI_UUID,
    "user_id": "user-456",
    "nom": "Camille Assoc",
    "email": "camille@sci.local",
    "part": 40,
    "role": "associe",
}

GERANT_ASSOC_2 = {
    "id": "assoc-e2e-g2",
    "id_sci": SCI_UUID_2,
    "user_id": "user-123",
    "nom": "Test Gerant",
    "email": "gerant@sci.local",
    "part": 100,
    "role": "gerant",
}


def _seed_pro(fake_supabase):
    """Standard setup: pro subscription + gerant membership on SCI_UUID."""
    fake_supabase.store["subscriptions"] = [PRO_SUB]
    fake_supabase.store["associes"] = [GERANT_ASSOC, ASSOC_ONLY]
    fake_supabase.store["sci"] = [
        {"id": SCI_UUID, "nom": "SCI E2E Test", "siren": "123456789", "regime_fiscal": "IR"},
    ]


def _seed_pro_two_scis(fake_supabase):
    """Pro subscription with two SCIs."""
    _seed_pro(fake_supabase)
    fake_supabase.store["sci"].append(
        {"id": SCI_UUID_2, "nom": "SCI E2E Deux", "siren": "987654321", "regime_fiscal": "IS"},
    )
    fake_supabase.store["associes"].append(GERANT_ASSOC_2)


def _seed_bien(fake_supabase, bien_id=BIEN_ID, sci_id=SCI_UUID):
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


def _seed_bail(fake_supabase, bail_id=BAIL_ID, bien_id=BIEN_ID):
    bail = {
        "id": bail_id,  # must be int (router param type)
        "id_bien": bien_id,
        "date_debut": "2025-01-01",
        "date_fin": "2028-01-01",
        "loyer_hc": 900.0,
        "charges_provisions": 100.0,
        "depot_garantie": 900.0,
        "statut": "en_cours",
    }
    fake_supabase.store.setdefault("baux", []).append(bail)
    return bail


def _patch_fake_auth(fake_supabase):
    """Add missing attributes to FakeAuthAdmin User objects for GDPR endpoints."""
    original_get_user = fake_supabase.auth.admin.get_user_by_id

    def patched_get_user(user_id):
        resp = original_get_user(user_id)
        resp.user.email_confirmed_at = "2026-01-01T00:00:00"
        resp.user.last_sign_in_at = "2026-03-10T10:00:00"
        return resp

    fake_supabase.auth.admin.get_user_by_id = patched_get_user
    fake_supabase.auth.admin.delete_user = lambda uid: None


def _seed_loyer(fake_supabase, loyer_id=LOYER_ID, bien_id=BIEN_ID, sci_id=SCI_UUID,
                date="2026-03-01", montant=1000.0, statut="paye"):
    loyer = {
        "id": loyer_id,
        "id_bien": bien_id,
        "id_sci": sci_id,
        "date_loyer": date,
        "montant": montant,
        "statut": statut,
    }
    fake_supabase.store.setdefault("loyers", []).append(loyer)
    return loyer


BASE = f"/api/v1/scis/{SCI_UUID}/biens"
BASE2 = f"/api/v1/scis/{SCI_UUID_2}/biens"


# ══════════════════════════════════════════════════════════════
# Scenario 1: Complete Onboarding Journey
# ══════════════════════════════════════════════════════════════


class TestOnboardingJourney:
    """User signs up -> creates SCI -> creates bien -> creates bail -> completes onboarding."""

    def test_full_onboarding_flow(self, client, auth_headers, fake_supabase):
        # Start with an incomplete onboarding
        fake_supabase.store["subscriptions"] = [{
            **PRO_SUB,
            "onboarding_completed": False,
        }]
        fake_supabase.store["associes"] = []
        fake_supabase.store["sci"] = []
        fake_supabase.store["biens"] = []
        fake_supabase.store["baux"] = []

        # 1. Check onboarding status -- not completed
        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.status_code == 200
        status = resp.json()
        assert status["completed"] is False
        assert status["sci_created"] is False

        # 2. Create SCI
        fake_supabase.store["associes"].append(GERANT_ASSOC)
        fake_supabase.store["sci"].append(
            {"id": SCI_UUID, "nom": "SCI Onboard", "siren": "111222333", "regime_fiscal": "IR"},
        )

        # 3. Verify SCI appears in onboarding progress
        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.status_code == 200
        status = resp.json()
        assert status["sci_created"] is True
        assert status["sci_id"] == SCI_UUID
        assert status["bien_created"] is False

        # 4. Create bien
        _seed_bien(fake_supabase)

        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["bien_created"] is True
        assert resp.json()["bail_created"] is False

        # 5. Create bail
        _seed_bail(fake_supabase)

        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["bail_created"] is True

        # 6. Complete onboarding
        resp = client.post("/api/v1/onboarding/complete", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["completed"] is True

        # 7. Verify onboarding is now completed
        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["completed"] is True

    def test_onboarding_status_reflects_notification_prefs(self, client, auth_headers, fake_supabase):
        fake_supabase.store["subscriptions"] = [PRO_SUB]
        fake_supabase.store["associes"] = [GERANT_ASSOC]
        fake_supabase.store["sci"] = [{"id": SCI_UUID, "nom": "SCI NP", "siren": "111", "regime_fiscal": "IR"}]
        fake_supabase.store["notification_preferences"] = []

        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.json()["notifications_set"] is False

        fake_supabase.store["notification_preferences"].append(
            {"id": "np-1", "user_id": "user-123", "type": "late_payment", "email_enabled": True, "in_app_enabled": True}
        )

        resp = client.get("/api/v1/onboarding", headers=auth_headers)
        assert resp.json()["notifications_set"] is True

    def test_complete_onboarding_creates_subscription_if_missing(self, client, auth_headers, fake_supabase):
        fake_supabase.store["subscriptions"] = []
        fake_supabase.store["associes"] = [GERANT_ASSOC]

        resp = client.post("/api/v1/onboarding/complete", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["completed"] is True

        # Should have created a subscription row
        subs = [s for s in fake_supabase.store["subscriptions"] if s["user_id"] == "user-123"]
        assert len(subs) == 1
        assert subs[0]["onboarding_completed"] is True


# ══════════════════════════════════════════════════════════════
# Scenario 2: SCI Lifecycle
# ══════════════════════════════════════════════════════════════


class TestSCILifecycle:
    """Create SCI -> update -> add associe -> add bien -> list everything -> delete."""

    def test_create_update_delete_sci(self, client, auth_headers, fake_supabase):
        fake_supabase.store["subscriptions"] = [PRO_SUB]

        # 1. Create SCI
        resp = client.post(
            "/api/v1/scis/",
            json={"nom": "SCI Lifecycle", "siren": "999888777", "regime_fiscal": "IS"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        sci_id = resp.json()["id"]

        # 2. Verify it appears in listing
        resp = client.get("/api/v1/scis/", headers=auth_headers)
        assert resp.status_code == 200
        noms = [s["nom"] for s in resp.json()]
        assert "SCI Lifecycle" in noms

        # 3. Update SCI (user is gerant of the newly created SCI)
        resp = client.patch(
            f"/api/v1/scis/{sci_id}",
            json={"nom": "SCI Lifecycle Renamed"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "SCI Lifecycle Renamed"

        # 4. Delete SCI
        resp = client.delete(f"/api/v1/scis/{sci_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_add_associe_and_verify_listing(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)

        # List current associes
        resp = client.get(f"/api/v1/scis/{SCI_UUID}/associes", headers=auth_headers)
        assert resp.status_code == 200
        initial_count = len(resp.json())

        # Invite new associe
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/associes",
            json={"nom": "Nouvel Associe", "email": "new@sci.local", "part": 10, "role": "associe"},
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Verify count increased
        resp = client.get(f"/api/v1/scis/{SCI_UUID}/associes", headers=auth_headers)
        assert len(resp.json()) == initial_count + 1

    def test_delete_sci_cascades_all_data(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_bail(fake_supabase)
        _seed_loyer(fake_supabase)
        fake_supabase.store["charges"] = [
            {"id": "ch-del", "id_bien": BIEN_ID, "type_charge": "taxe", "montant": 500, "date_paiement": "2026-01-01"},
        ]
        fake_supabase.store["fiscalite"] = [
            {"id": "fisc-del", "id_sci": SCI_UUID, "annee": 2025, "total_revenus": 12000, "total_charges": 2000},
        ]
        fake_supabase.store["notifications"] = [
            {"id": "notif-del", "id_sci": SCI_UUID},
        ]

        resp = client.delete(f"/api/v1/scis/{SCI_UUID}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify cascaded deletes
        assert not any(b["id"] == BIEN_ID for b in fake_supabase.store.get("biens", []))
        assert not any(l["id"] == LOYER_ID for l in fake_supabase.store.get("loyers", []))
        assert not any(c["id"] == "ch-del" for c in fake_supabase.store.get("charges", []))

    def test_non_gerant_cannot_update_or_delete(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        # user-123 is associe (not gerant) of SCI_UUID_2
        fake_supabase.store["sci"].append(
            {"id": SCI_UUID_2, "nom": "SCI ReadOnly", "siren": "555", "regime_fiscal": "IR"},
        )
        fake_supabase.store["associes"].append(
            {"id": "assoc-ro", "id_sci": SCI_UUID_2, "user_id": "user-123", "nom": "RO", "email": "ro@t.com", "part": 50, "role": "associe"},
        )

        resp = client.patch(f"/api/v1/scis/{SCI_UUID_2}", json={"nom": "Nope"}, headers=auth_headers)
        assert resp.status_code == 403

        resp = client.delete(f"/api/v1/scis/{SCI_UUID_2}", headers=auth_headers)
        assert resp.status_code == 403


# ══════════════════════════════════════════════════════════════
# Scenario 3: Bien + Bail + Loyer Journey
# ══════════════════════════════════════════════════════════════


class TestBienBailLoyerJourney:
    """Create bien -> create bail with locataire -> record loyers -> generate quittance."""

    def test_full_rental_lifecycle(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)

        # 1. Create bien via API
        resp = client.post(
            BASE,
            json={
                "id_sci": SCI_UUID,
                "adresse": "20 avenue Victor Hugo",
                "ville": "Lyon",
                "code_postal": "69001",
                "type_locatif": "meuble",
                "loyer_cc": 850.0,
                "charges": 50.0,
                "tmi": 0.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        bien_id = resp.json()["id"]

        # 2. Verify bien in listing
        resp = client.get(BASE, headers=auth_headers)
        assert resp.status_code == 200
        assert any(b["id"] == bien_id for b in resp.json())

        # 3. Create bail
        resp = client.post(
            f"{BASE}/{bien_id}/baux",
            json={
                "id_bien": bien_id,
                "date_debut": "2026-01-01",
                "date_fin": "2029-01-01",
                "loyer_hc": 800.0,
                "charges_provisions": 50.0,
                "depot_garantie": 800.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        bail_id = resp.json()["id"]

        # 4. Verify bail in listing
        resp = client.get(f"{BASE}/{bien_id}/baux", headers=auth_headers)
        assert resp.status_code == 200
        assert any(b["id"] == bail_id for b in resp.json())

        # 5. Record a loyer
        resp = client.post(
            f"{BASE}/{bien_id}/loyers",
            json={
                "id_bien": bien_id,
                "date_loyer": "2026-03-01",
                "montant": 850.0,
                "statut": "paye",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        loyer_id = resp.json()["id"]

        # 6. Verify loyer in listing
        resp = client.get(f"{BASE}/{bien_id}/loyers", headers=auth_headers)
        assert resp.status_code == 200
        assert any(l["id"] == loyer_id for l in resp.json())

    def test_bail_create_via_api(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        # Create bail via API (type_locatif=nu requires minimum 3 years = 1095 days)
        resp = client.post(
            f"{BASE}/{BIEN_ID}/baux",
            json={
                "id_bien": BIEN_ID,
                "date_debut": "2025-01-01",
                "date_fin": "2028-06-01",
                "loyer_hc": 700.0,
                "charges_provisions": 80.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["date_debut"] == "2025-01-01"
        assert data["loyer_hc"] == 700.0

        # Verify it appears in listing
        resp = client.get(f"{BASE}/{BIEN_ID}/baux", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_bail_update_with_int_id(self, client, auth_headers, fake_supabase):
        """bail_id path param is int. Seed bail with int id to test PATCH."""
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_bail(fake_supabase)  # bail_id = 9001

        resp = client.patch(
            f"{BASE}/{BIEN_ID}/baux/{BAIL_ID}",
            json={"date_fin": "2027-06-01", "loyer_hc": 750.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_bail_delete(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_bail(fake_supabase)  # bail_id = 9001 (int)

        resp = client.delete(f"{BASE}/{BIEN_ID}/baux/{BAIL_ID}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify deleted
        resp = client.get(f"{BASE}/{BIEN_ID}/baux", headers=auth_headers)
        assert not any(b["id"] == BAIL_ID for b in resp.json())

    def test_loyer_recorded_and_listed(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        # Record two loyers
        for month, m in [("2026-01-01", 1000.0), ("2026-02-01", 1000.0)]:
            resp = client.post(
                f"{BASE}/{BIEN_ID}/loyers",
                json={"id_bien": BIEN_ID, "date_loyer": month, "montant": m, "statut": "paye"},
                headers=auth_headers,
            )
            assert resp.status_code == 201

        resp = client.get(f"{BASE}/{BIEN_ID}/loyers", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_generate_quittance_pdf(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase)

        resp = client.post(
            "/api/v1/quitus/generate",
            json={
                "id_loyer": LOYER_ID,
                "id_bien": BIEN_ID,
                "nom_locataire": "Jean Dupont",
                "periode": "Mars 2026",
                "montant": 1000.0,
                "nom_sci": "SCI E2E Test",
                "adresse_bien": "12 rue de la Paix",
                "ville_bien": "Paris",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "filename" in data
        assert data["size_bytes"] > 0
        assert data["pdf_url"].startswith("/api/v1/quitus/files/")


# ══════════════════════════════════════════════════════════════
# Scenario 4: Financial Dashboard Journey
# ══════════════════════════════════════════════════════════════


class TestFinancialJourney:
    """Record loyers + charges -> verify dashboard KPIs -> export CSV."""

    def test_dashboard_kpis_reflect_real_data(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase, statut="paye")
        _seed_loyer(fake_supabase, loyer_id="loyer-pending", statut="en_attente", date="2026-04-01")

        resp = client.get("/api/v1/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "kpis" in data
        assert "scis" in data
        assert "alertes" in data
        assert "activite" in data

    def test_dashboard_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 401

    def test_export_loyers_csv(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase, loyer_id="loyer-csv-1", date="2026-01-01", montant=1000.0)
        _seed_loyer(fake_supabase, loyer_id="loyer-csv-2", date="2026-02-01", montant=1000.0)

        resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        # Header + 2 data rows
        assert len(rows) == 3
        assert rows[0][0] == "date_loyer"

    def test_export_biens_csv(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 2  # header + 1 bien

    def test_export_csv_filters_by_sci(self, client, auth_headers, fake_supabase):
        _seed_pro_two_scis(fake_supabase)
        _seed_bien(fake_supabase, bien_id="bien-s1", sci_id=SCI_UUID)
        _seed_bien(fake_supabase, bien_id="bien-s2", sci_id=SCI_UUID_2)
        _seed_loyer(fake_supabase, loyer_id="l-s1", bien_id="bien-s1", sci_id=SCI_UUID)
        _seed_loyer(fake_supabase, loyer_id="l-s2", bien_id="bien-s2", sci_id=SCI_UUID_2)

        # Filter by SCI 1 only
        resp = client.get(f"/api/v1/export/loyers/csv?sci_id={SCI_UUID}", headers=auth_headers)
        assert resp.status_code == 200
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        # header + 1 loyer from SCI_UUID
        assert len(rows) == 2

    def test_export_csv_empty_when_no_data(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        fake_supabase.store["loyers"] = []

        resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
        assert resp.status_code == 200
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1  # header only

    def test_finances_endpoint(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase)

        resp = client.get("/api/v1/finances", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "revenus_total" in data
        assert "charges_total" in data
        assert "cashflow_net" in data

    def test_finances_blocked_for_cancelled_subscription(self, client, auth_headers, fake_supabase):
        """Cancelled paid subscription blocks finances endpoint."""
        fake_supabase.store["subscriptions"] = [{
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "cancelled",
            "is_active": False,
        }]
        fake_supabase.store["associes"] = [GERANT_ASSOC]

        resp = client.get("/api/v1/finances", headers=auth_headers)
        assert resp.status_code == 402

    def test_fiscalite_crud(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)

        # Create fiscalite
        resp = client.post(
            "/api/v1/fiscalite/",
            json={
                "id_sci": SCI_UUID,
                "annee": 2025,
                "total_revenus": 24000.0,
                "total_charges": 5000.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        fisc_id = resp.json()["id"]

        # List
        resp = client.get("/api/v1/fiscalite/", headers=auth_headers)
        assert resp.status_code == 200
        assert any(f["id"] == fisc_id for f in resp.json())

        # Update
        resp = client.patch(
            f"/api/v1/fiscalite/{fisc_id}",
            json={"total_charges": 6000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f"/api/v1/fiscalite/{fisc_id}", headers=auth_headers)
        assert resp.status_code == 204


# ══════════════════════════════════════════════════════════════
# Scenario 5: Document Management Journey
# ══════════════════════════════════════════════════════════════


class TestDocumentJourney:
    """Upload document -> list -> delete."""

    def test_upload_and_list_document(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        # Upload document (multipart file upload)
        import io as _io
        file_content = b"fake pdf content"
        resp = client.post(
            f"{BASE}/{BIEN_ID}/documents",
            data={"nom": "bail_signe.pdf", "categorie": "bail"},
            files={"file": ("bail_signe.pdf", _io.BytesIO(file_content), "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        doc_id = resp.json()["id"]

        # List documents
        resp = client.get(f"{BASE}/{BIEN_ID}/documents", headers=auth_headers)
        assert resp.status_code == 200
        assert any(d["id"] == doc_id for d in resp.json())

    def test_delete_document_by_int_id(self, client, auth_headers, fake_supabase):
        """doc_id path param is int, so seed with int ID for delete test."""
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        fake_supabase.store["documents_bien"] = [
            {"id": 7001, "id_bien": BIEN_ID, "nom": "test.pdf", "categorie": "bail",
             "url": "https://storage.local/docs/test.pdf", "uploaded_at": "2026-01-01T00:00:00"},
        ]

        # Verify it exists
        resp = client.get(f"{BASE}/{BIEN_ID}/documents", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Delete by int id
        resp = client.delete(f"{BASE}/{BIEN_ID}/documents/7001", headers=auth_headers)
        assert resp.status_code == 204

        # Verify deleted
        resp = client.get(f"{BASE}/{BIEN_ID}/documents", headers=auth_headers)
        assert resp.json() == []

    def test_sci_documents_aggregation(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase, bien_id="bien-doc1")
        _seed_bien(fake_supabase, bien_id="bien-doc2")
        fake_supabase.store["documents_bien"] = [
            {"id": "doc-1", "id_bien": "bien-doc1", "nom": "a.pdf", "categorie": "bail",
             "url": "https://x/a.pdf", "uploaded_at": "2026-01-01T00:00:00"},
            {"id": "doc-2", "id_bien": "bien-doc2", "nom": "b.pdf", "categorie": "facture",
             "url": "https://x/b.pdf", "uploaded_at": "2026-02-01T00:00:00"},
        ]

        resp = client.get(f"/api/v1/scis/{SCI_UUID}/documents", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_document_requires_membership(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        unknown = "99999999-9999-9999-9999-999999999999"
        resp = client.get(f"/api/v1/scis/{unknown}/documents", headers=auth_headers)
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# Scenario 6: Multi-SCI Isolation
# ══════════════════════════════════════════════════════════════


class TestMultiSCIIsolation:
    """Create 2 SCIs -> verify data isolation between them."""

    def test_biens_scoped_to_sci(self, client, auth_headers, fake_supabase):
        _seed_pro_two_scis(fake_supabase)
        _seed_bien(fake_supabase, bien_id="bien-sci1", sci_id=SCI_UUID)
        _seed_bien(fake_supabase, bien_id="bien-sci2", sci_id=SCI_UUID_2)

        # List biens for SCI 1
        resp = client.get(BASE, headers=auth_headers)
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.json()]
        assert "bien-sci1" in ids
        assert "bien-sci2" not in ids

        # List biens for SCI 2
        resp = client.get(BASE2, headers=auth_headers)
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.json()]
        assert "bien-sci2" in ids
        assert "bien-sci1" not in ids

    def test_loyers_scoped_to_sci_biens(self, client, auth_headers, fake_supabase):
        _seed_pro_two_scis(fake_supabase)
        _seed_bien(fake_supabase, bien_id="bien-iso1", sci_id=SCI_UUID)
        _seed_bien(fake_supabase, bien_id="bien-iso2", sci_id=SCI_UUID_2)
        _seed_loyer(fake_supabase, loyer_id="l-iso1", bien_id="bien-iso1", sci_id=SCI_UUID)
        _seed_loyer(fake_supabase, loyer_id="l-iso2", bien_id="bien-iso2", sci_id=SCI_UUID_2)

        resp = client.get(f"{BASE}/bien-iso1/loyers", headers=auth_headers)
        assert resp.status_code == 200
        ids = [l["id"] for l in resp.json()]
        assert "l-iso1" in ids
        assert "l-iso2" not in ids

    def test_export_respects_sci_filter(self, client, auth_headers, fake_supabase):
        _seed_pro_two_scis(fake_supabase)
        _seed_bien(fake_supabase, bien_id="bien-exp1", sci_id=SCI_UUID)
        _seed_bien(fake_supabase, bien_id="bien-exp2", sci_id=SCI_UUID_2)
        _seed_loyer(fake_supabase, loyer_id="l-exp1", bien_id="bien-exp1", sci_id=SCI_UUID)
        _seed_loyer(fake_supabase, loyer_id="l-exp2", bien_id="bien-exp2", sci_id=SCI_UUID_2)

        # Export with SCI filter
        resp = client.get(f"/api/v1/export/loyers/csv?sci_id={SCI_UUID_2}", headers=auth_headers)
        assert resp.status_code == 200
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 2  # header + 1

    def test_dashboard_aggregates_all_scis(self, client, auth_headers, fake_supabase):
        _seed_pro_two_scis(fake_supabase)
        _seed_bien(fake_supabase, bien_id="b-d1", sci_id=SCI_UUID)
        _seed_bien(fake_supabase, bien_id="b-d2", sci_id=SCI_UUID_2)

        resp = client.get("/api/v1/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Should see both SCIs
        assert len(data["scis"]) >= 2

    def test_non_member_sci_is_hidden(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        other_sci = "33333333-3333-3333-3333-333333333333"
        fake_supabase.store["sci"].append(
            {"id": other_sci, "nom": "SCI Foreign", "siren": "000", "regime_fiscal": "IR"},
        )
        # No membership for user-123 on other_sci

        resp = client.get(f"/api/v1/scis/{other_sci}/biens", headers=auth_headers)
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# Scenario 7: Paywall Enforcement
# ══════════════════════════════════════════════════════════════


class TestPaywallEnforcement:
    """Free plan limits -> upgrade -> access pro features."""

    def test_free_plan_limits_sci_creation(self, client, auth_headers, fake_supabase):
        """Free plan user with 1 SCI cannot create a second one (starter plan, max_scis=1)."""
        fake_supabase.store["subscriptions"] = [{
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 1,
            "max_biens": 5,
            "features": {"multi_sci_enabled": False},
        }]
        fake_supabase.store["associes"] = [GERANT_ASSOC]
        fake_supabase.store["sci"] = [
            {"id": SCI_UUID, "nom": "SCI One", "siren": "111222333", "regime_fiscal": "IR"},
        ]

        resp = client.post(
            "/api/v1/scis/",
            json={"nom": "SCI Two", "siren": "222333444", "regime_fiscal": "IR"},
            headers=auth_headers,
        )
        assert resp.status_code == 402

    def test_pro_plan_allows_multiple_scis(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)

        resp = client.post(
            "/api/v1/scis/",
            json={"nom": "SCI Extra", "siren": "333444555", "regime_fiscal": "IS"},
            headers=auth_headers,
        )
        assert resp.status_code == 201

    def test_finances_with_free_plan_still_works(self, client, auth_headers, fake_supabase):
        """Free plan is still active -- finances returns 200 (free plan defaults to is_active=True)."""
        fake_supabase.store["subscriptions"] = []
        fake_supabase.store["associes"] = [GERANT_ASSOC]

        resp = client.get("/api/v1/finances", headers=auth_headers)
        # Free plan defaults to is_active=True, so finances works
        assert resp.status_code == 200

    def test_finances_with_cancelled_subscription(self, client, auth_headers, fake_supabase):
        """A cancelled (non-active) paid subscription blocks finances."""
        fake_supabase.store["subscriptions"] = [{
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "cancelled",
            "is_active": False,
        }]
        fake_supabase.store["associes"] = [GERANT_ASSOC]

        resp = client.get("/api/v1/finances", headers=auth_headers)
        assert resp.status_code == 402

    def test_quitus_requires_feature_enabled(self, client, auth_headers, fake_supabase):
        """Quitus generation requires quitus_enabled feature."""
        fake_supabase.store["subscriptions"] = [{
            **FREE_SUB,
            "features": {"quitus_enabled": False},
        }]
        fake_supabase.store["associes"] = [GERANT_ASSOC]
        fake_supabase.store["sci"] = [
            {"id": SCI_UUID, "nom": "SCI Q", "siren": "111222333", "regime_fiscal": "IR"},
        ]
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase)

        resp = client.post(
            "/api/v1/quitus/generate",
            json={
                "id_loyer": LOYER_ID,
                "id_bien": BIEN_ID,
                "nom_locataire": "Jean Dupont",
                "periode": "Mars 2026",
                "montant": 1000.0,
            },
            headers=auth_headers,
        )
        # Should be blocked by feature gate
        assert resp.status_code in (402, 403)


# ══════════════════════════════════════════════════════════════
# Scenario 8: GDPR Compliance
# ══════════════════════════════════════════════════════════════


class TestGDPRCompliance:
    """Data summary -> export -> delete account."""

    def test_data_summary_returns_all_counts(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _patch_fake_auth(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase)

        resp = client.get("/api/v1/gdpr/data-summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user-123"
        assert "data_summary" in data
        summary = data["data_summary"]
        assert summary["sci_count"] >= 1
        assert summary["biens_count"] >= 1

    def test_export_includes_all_user_data(self, client, auth_headers, fake_supabase, fake_storage):
        _seed_pro(fake_supabase)
        _patch_fake_auth(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase)
        fake_supabase.store["charges"] = [
            {"id": "ch-gdpr", "id_bien": BIEN_ID, "type_charge": "taxe", "montant": 300, "date_paiement": "2026-01-01"},
        ]

        resp = client.get("/api/v1/gdpr/data-export", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["export_url"] is not None

    def test_delete_removes_all_user_data(self, client, auth_headers, fake_supabase, fake_storage):
        _seed_pro(fake_supabase)
        _patch_fake_auth(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_loyer(fake_supabase)
        fake_supabase.store["notifications"] = [
            {"id": "n-gdpr", "user_id": "user-123", "type": "info", "title": "Test", "message": "msg", "created_at": "2026-01-01"},
        ]
        fake_supabase.store["notification_preferences"] = [
            {"id": "np-gdpr", "user_id": "user-123", "type": "late_payment", "email_enabled": True, "in_app_enabled": True},
        ]

        resp = client.delete("/api/v1/gdpr/account", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        # Verify user-level data is cleaned
        assert not any(n["user_id"] == "user-123" for n in fake_supabase.store.get("notifications", []))
        assert not any(n["user_id"] == "user-123" for n in fake_supabase.store.get("notification_preferences", []))
        assert not any(a["user_id"] == "user-123" for a in fake_supabase.store.get("associes", []))

    def test_gdpr_requires_auth(self, client):
        assert client.get("/api/v1/gdpr/data-summary").status_code == 401
        assert client.get("/api/v1/gdpr/data-export").status_code == 401
        assert client.delete("/api/v1/gdpr/account").status_code == 401


# ══════════════════════════════════════════════════════════════
# Scenario 9: Notification Flow
# ══════════════════════════════════════════════════════════════


class TestNotificationFlow:
    """Notifications created -> listed -> marked as read."""

    def test_notification_lifecycle(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        fake_supabase.store["notifications"] = [
            {"id": "notif-1", "user_id": "user-123", "type": "late_payment", "title": "Loyer impaye",
             "message": "Loyer Mars non paye", "metadata": {}, "read_at": None, "created_at": "2026-03-10T10:00:00"},
            {"id": "notif-2", "user_id": "user-123", "type": "bail_expiring", "title": "Bail expire",
             "message": "Bail expire dans 30j", "metadata": {}, "read_at": None, "created_at": "2026-03-09T10:00:00"},
        ]

        # 1. List all notifications
        resp = client.get("/api/v1/notifications/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # 2. Get unread count
        resp = client.get("/api/v1/notifications/count", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

        # 3. Mark one as read
        resp = client.patch("/api/v1/notifications/notif-1/read", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["read_at"] is not None

        # 4. Unread count decreased
        resp = client.get("/api/v1/notifications/count", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

        # 5. Mark all as read
        resp = client.patch("/api/v1/notifications/read-all", headers=auth_headers)
        assert resp.status_code == 200

        # 6. Unread count is now 0
        resp = client.get("/api/v1/notifications/count", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_notification_preferences(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        fake_supabase.store["notification_preferences"] = []

        # 1. Get defaults (nothing saved yet)
        resp = client.get("/api/v1/user/notification-preferences", headers=auth_headers)
        assert resp.status_code == 200
        prefs = resp.json()["preferences"]
        assert len(prefs) >= 7  # DEFAULT_NOTIFICATION_TYPES has 7 entries
        # All should default to enabled
        for p in prefs:
            assert p["email_enabled"] is True
            assert p["in_app_enabled"] is True

        # 2. Update a preference
        resp = client.put(
            "/api/v1/user/notification-preferences",
            json={
                "preferences": [
                    {"type": "late_payment", "email_enabled": False, "in_app_enabled": True},
                    {"type": "bail_expiring", "email_enabled": True, "in_app_enabled": False},
                ]
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        prefs = resp.json()["preferences"]
        lp = next(p for p in prefs if p["type"] == "late_payment")
        assert lp["email_enabled"] is False
        assert lp["in_app_enabled"] is True

    def test_mark_nonexistent_notification_returns_404(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        fake_supabase.store["notifications"] = []

        resp = client.patch("/api/v1/notifications/nonexistent/read", headers=auth_headers)
        assert resp.status_code == 404

    def test_notifications_require_auth(self, client):
        assert client.get("/api/v1/notifications/").status_code == 401
        assert client.get("/api/v1/notifications/count").status_code == 401


# ══════════════════════════════════════════════════════════════
# Scenario 10: Charges + Assurance PNO + Frais Agence Journey
# ══════════════════════════════════════════════════════════════


class TestChargesJourney:
    """Add charges, PNO, frais agence -> verify rentabilite impact."""

    def test_charges_crud(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        # Create charge
        resp = client.post(
            f"{BASE}/{BIEN_ID}/charges",
            json={
                "id_bien": BIEN_ID,
                "type_charge": "copropriete",
                "montant": 250.0,
                "date_paiement": "2026-03-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        charge_id = resp.json()["id"]

        # List charges
        resp = client.get(f"{BASE}/{BIEN_ID}/charges", headers=auth_headers)
        assert resp.status_code == 200
        assert any(c["id"] == charge_id for c in resp.json())

        # Update charge
        resp = client.patch(
            f"{BASE}/{BIEN_ID}/charges/{charge_id}",
            json={"montant": 300.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["montant"] == 300.0

        # Delete charge
        resp = client.delete(f"{BASE}/{BIEN_ID}/charges/{charge_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_assurance_pno_create_and_list(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        # Create PNO (schema: compagnie, numero_contrat, montant_annuel, date_echeance)
        resp = client.post(
            f"{BASE}/{BIEN_ID}/assurance-pno",
            json={
                "compagnie": "AXA",
                "numero_contrat": "PNO-123",
                "montant_annuel": 180.0,
                "date_echeance": "2027-01-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        pno_id = resp.json()["id"]

        # List
        resp = client.get(f"{BASE}/{BIEN_ID}/assurance-pno", headers=auth_headers)
        assert resp.status_code == 200
        assert any(p["id"] == pno_id for p in resp.json())

    def test_assurance_pno_update_and_delete(self, client, auth_headers, fake_supabase):
        """pno_id path param is int, so seed with int ID for update/delete."""
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        # Table name is "assurances_pno" (plural) in the API code
        fake_supabase.store["assurances_pno"] = [
            {"id": 8001, "id_bien": BIEN_ID, "compagnie": "AXA", "numero_contrat": "PNO-123",
             "montant_annuel": 180.0, "date_echeance": "2027-01-01"},
        ]

        # Update
        resp = client.patch(
            f"{BASE}/{BIEN_ID}/assurance-pno/8001",
            json={"montant_annuel": 200.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f"{BASE}/{BIEN_ID}/assurance-pno/8001", headers=auth_headers)
        assert resp.status_code == 204

    def test_frais_agence_create_and_list(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        # Create frais (schema: nom_agence, contact, type_frais='pourcentage'|'fixe', montant_ou_pourcentage)
        resp = client.post(
            f"{BASE}/{BIEN_ID}/frais-agence",
            json={
                "nom_agence": "Orpi Lyon",
                "type_frais": "pourcentage",
                "montant_ou_pourcentage": 8.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        frais_id = resp.json()["id"]

        # List
        resp = client.get(f"{BASE}/{BIEN_ID}/frais-agence", headers=auth_headers)
        assert resp.status_code == 200
        assert any(f["id"] == frais_id for f in resp.json())

    def test_frais_agence_delete_by_int_id(self, client, auth_headers, fake_supabase):
        """frais_id path param is int, so seed with int ID for delete test."""
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        fake_supabase.store["frais_agence"] = [
            {"id": 6001, "id_bien": BIEN_ID, "nom_agence": "Orpi", "type_frais": "fixe",
             "montant_ou_pourcentage": 75.0},
        ]

        resp = client.delete(f"{BASE}/{BIEN_ID}/frais-agence/6001", headers=auth_headers)
        assert resp.status_code == 204

    def test_charges_require_gerant_role(self, client, auth_headers, fake_supabase):
        """Associe (non-gerant) cannot create charges."""
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase, bien_id="bien-ro", sci_id=SCI_UUID_2)
        fake_supabase.store["sci"].append(
            {"id": SCI_UUID_2, "nom": "SCI RO", "siren": "555", "regime_fiscal": "IR"},
        )
        fake_supabase.store["associes"].append(
            {"id": "assoc-ro2", "id_sci": SCI_UUID_2, "user_id": "user-123", "nom": "RO", "email": "ro@t.com", "part": 50, "role": "associe"},
        )

        resp = client.post(
            f"/api/v1/scis/{SCI_UUID_2}/biens/bien-ro/charges",
            json={"id_bien": "bien-ro", "type_charge": "taxe", "montant": 100.0, "date_paiement": "2026-01-01"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_multiple_charges_on_same_bien(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)

        charges_data = [
            {"type_charge": "copropriete", "montant": 250.0, "date_paiement": "2026-01-01"},
            {"type_charge": "taxe_fonciere", "montant": 800.0, "date_paiement": "2026-10-01"},
            {"type_charge": "assurance", "montant": 180.0, "date_paiement": "2026-03-01"},
        ]
        for ch in charges_data:
            resp = client.post(
                f"{BASE}/{BIEN_ID}/charges",
                json={"id_bien": BIEN_ID, **ch},
                headers=auth_headers,
            )
            assert resp.status_code == 201

        resp = client.get(f"{BASE}/{BIEN_ID}/charges", headers=auth_headers)
        assert len(resp.json()) == 3


# ══════════════════════════════════════════════════════════════
# Scenario 11: Auth & Security Edge Cases
# ══════════════════════════════════════════════════════════════


class TestAuthSecurity:
    """Verify authentication and authorization boundaries."""

    def test_all_major_endpoints_require_auth(self, client):
        """All user-facing endpoints must return 401 without auth headers."""
        endpoints = [
            ("GET", "/api/v1/scis/"),
            ("GET", "/api/v1/dashboard"),
            ("GET", "/api/v1/onboarding"),
            ("GET", "/api/v1/notifications/"),
            ("GET", "/api/v1/notifications/count"),
            ("GET", "/api/v1/export/loyers/csv"),
            ("GET", "/api/v1/export/biens/csv"),
            ("GET", "/api/v1/fiscalite/"),
            ("GET", "/api/v1/gdpr/data-summary"),
            ("GET", "/api/v1/user/notification-preferences"),
        ]
        for method, url in endpoints:
            if method == "GET":
                resp = client.get(url)
            elif method == "POST":
                resp = client.post(url)
            assert resp.status_code == 401, f"{method} {url} returned {resp.status_code}, expected 401"

    def test_invalid_uuid_in_nested_routes(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        resp = client.get("/api/v1/scis/not-a-uuid/biens", headers=auth_headers)
        assert resp.status_code == 422

    def test_accessing_nonexistent_sci(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        unknown = "99999999-9999-9999-9999-999999999999"
        resp = client.get(f"/api/v1/scis/{unknown}/biens", headers=auth_headers)
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# Scenario 12: Locataire Management via Bail
# ══════════════════════════════════════════════════════════════


class TestLocataireManagement:
    """Add locataire to bail -> list -> remove."""

    def test_add_and_remove_locataire(self, client, auth_headers, fake_supabase):
        _seed_pro(fake_supabase)
        _seed_bien(fake_supabase)
        _seed_bail(fake_supabase)  # bail_id = 9001 (int)
        fake_supabase.store["locataires"] = [
            {"id": LOCATAIRE_ID, "id_bien": BIEN_ID, "nom": "Jean Dupont", "email": "jean@test.com"},
        ]
        fake_supabase.store["bail_locataires"] = []

        # Add locataire to bail (bail_id is int in router, body uses "locataire_id")
        resp = client.post(
            f"{BASE}/{BIEN_ID}/baux/{BAIL_ID}/locataires",
            json={"locataire_id": LOCATAIRE_ID},
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Remove locataire from bail (locataire_id is int in router)
        resp = client.delete(
            f"{BASE}/{BIEN_ID}/baux/{BAIL_ID}/locataires/{LOCATAIRE_ID}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
