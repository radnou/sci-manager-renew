"""Tests for the echeances (deadlines) engine and API endpoint."""

from __future__ import annotations

from datetime import date, timedelta

import pytest


# ── Service unit tests ─────────────────────────────────────────────────────


class TestEcheancesService:
    """Unit tests for EcheancesService logic."""

    def test_calc_urgence_depassee(self):
        from app.services.echeances_service import _calc_urgence
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        assert _calc_urgence(yesterday) == "depassee"

    def test_calc_urgence_critique(self):
        from app.services.echeances_service import _calc_urgence
        in_15_days = (date.today() + timedelta(days=15)).isoformat()
        assert _calc_urgence(in_15_days) == "critique"

    def test_calc_urgence_urgente(self):
        from app.services.echeances_service import _calc_urgence
        in_60_days = (date.today() + timedelta(days=60)).isoformat()
        assert _calc_urgence(in_60_days) == "urgente"

    def test_calc_urgence_normale(self):
        from app.services.echeances_service import _calc_urgence
        in_120_days = (date.today() + timedelta(days=120)).isoformat()
        assert _calc_urgence(in_120_days) == "normale"

    def test_calc_urgence_lointaine(self):
        from app.services.echeances_service import _calc_urgence
        in_200_days = (date.today() + timedelta(days=200)).isoformat()
        assert _calc_urgence(in_200_days) == "lointaine"

    def test_calc_urgence_invalid_date(self):
        from app.services.echeances_service import _calc_urgence
        assert _calc_urgence("not-a-date") == "normale"

    def test_get_echeances_returns_structure(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        result = svc.get_echeances(fake_supabase, "user-123")
        assert "echeances" in result
        assert "resume" in result
        assert isinstance(result["echeances"], list)
        for key in ("depassee", "critique", "urgente", "normale", "lointaine"):
            assert key in result["resume"]

    def test_get_echeances_filtered_by_sci(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        result_all = svc.get_echeances(fake_supabase, "user-123")
        result_sci1 = svc.get_echeances(fake_supabase, "user-123", sci_id="sci-1")
        # Filtered should have fewer or equal echeances
        assert len(result_sci1["echeances"]) <= len(result_all["echeances"])

    def test_get_echeances_no_scis(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        result = svc.get_echeances(fake_supabase, "user-nonexistent")
        assert result["echeances"] == []
        assert result["resume"]["depassee"] == 0

    def test_check_ag_annuelle(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        sci = {"id": "sci-1", "nom": "Test SCI"}
        echeances = svc._check_ag_annuelle(sci)
        assert len(echeances) >= 1
        assert all(e["type"] == "ag_annuelle" for e in echeances)
        assert all("Art. 1856" in e["reference_legale"] for e in echeances)

    def test_check_declarations_fiscales_ir(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        sci = {"id": "sci-1", "nom": "Test SCI", "regime_fiscal": "IR"}
        echeances = svc._check_declarations_fiscales(sci)
        types = [e["type"] for e in echeances]
        assert "declaration_2072" in types
        assert "declaration_2044" in types

    def test_check_declarations_fiscales_is(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        sci = {"id": "sci-2", "nom": "Test IS", "regime_fiscal": "IS"}
        echeances = svc._check_declarations_fiscales(sci)
        types = [e["type"] for e in echeances]
        assert "declaration_2072" in types
        assert "declaration_2044" not in types  # IS regime has no 2044

    def test_check_pno_expiration(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        bien = {"id": "bien-1", "id_sci": "sci-1", "adresse": "1 rue de la Paix"}
        echeances = svc._check_pno(fake_supabase, bien)
        assert len(echeances) == 1
        assert echeances[0]["type"] == "pno_expiration"
        assert echeances[0]["date_echeance"] == "2026-06-01"

    def test_check_diagnostics_with_dates(self):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        bien = {
            "id": "bien-1", "id_sci": "sci-1", "adresse": "Test",
            "dpe_date": "2020-01-01",
            "diagnostic_electricite_date": "2021-06-01",
            "diagnostic_gaz_date": None,
            "diagnostic_amiante_date": "2023-01-01",
            "diagnostic_plomb_date": "2025-01-01",
        }
        echeances = svc._check_diagnostics(bien)
        types = [e["type"] for e in echeances]
        assert "diagnostic_dpe" in types
        assert "diagnostic_electricite" in types
        assert "diagnostic_amiante" in types
        assert "diagnostic_plomb" in types
        # gaz is None so should not generate an echeance
        assert not any("gaz" in t for t in types)

    def test_check_fin_bail(self):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        bail = {"date_fin": "2027-12-31"}
        bien = {"id": "bien-1", "id_sci": "sci-1", "adresse": "Test"}
        echeances = svc._check_fin_bail(bail, bien)
        assert len(echeances) == 1
        assert echeances[0]["type"] == "fin_bail"
        assert echeances[0]["date_echeance"] == "2027-12-31"

    def test_check_fin_bail_no_date(self):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        bail = {"date_fin": None}
        bien = {"id": "bien-1", "id_sci": "sci-1", "adresse": "Test"}
        assert svc._check_fin_bail(bail, bien) == []

    def test_check_revision_irl(self):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        bail = {"date_debut": "2025-06-15"}
        bien = {"id": "bien-1", "id_sci": "sci-1", "adresse": "Test"}
        echeances = svc._check_revision_irl(bail, bien)
        assert len(echeances) == 1
        assert echeances[0]["type"] == "revision_irl"

    def test_echeances_sorted_by_date(self, fake_supabase):
        from app.services.echeances_service import EcheancesService
        svc = EcheancesService()
        result = svc.get_echeances(fake_supabase, "user-123")
        dates = [e["date_echeance"] for e in result["echeances"]]
        assert dates == sorted(dates)


# ── API endpoint tests ─────────────────────────────────────────────────────


class TestEcheancesAPI:
    """Tests for GET /api/v1/echeances."""

    def test_get_echeances_ok(self, client, auth_headers):
        resp = client.get("/api/v1/echeances", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "echeances" in data
        assert "resume" in data
        assert isinstance(data["echeances"], list)

    def test_get_echeances_with_sci_filter(self, client, auth_headers):
        resp = client.get("/api/v1/echeances?sci_id=sci-1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["echeances"], list)

    def test_get_echeances_with_urgence_filter(self, client, auth_headers):
        resp = client.get("/api/v1/echeances?urgence=critique,urgente", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        for e in data["echeances"]:
            assert e["urgence"] in ("critique", "urgente")

    def test_get_echeances_unauthenticated(self, client):
        resp = client.get("/api/v1/echeances")
        assert resp.status_code == 401

    def test_get_echeances_resume_counts(self, client, auth_headers):
        resp = client.get("/api/v1/echeances", headers=auth_headers)
        assert resp.status_code == 200
        resume = resp.json()["resume"]
        for level in ("depassee", "critique", "urgente", "normale", "lointaine"):
            assert level in resume
            assert isinstance(resume[level], int)
            assert resume[level] >= 0

    def test_echeance_item_structure(self, client, auth_headers):
        resp = client.get("/api/v1/echeances", headers=auth_headers)
        assert resp.status_code == 200
        echeances = resp.json()["echeances"]
        if echeances:
            e = echeances[0]
            required_fields = ["type", "entite", "titre", "description", "date_echeance", "urgence"]
            for field in required_fields:
                assert field in e, f"Missing field: {field}"


# ── Bail clôture tests ─────────────────────────────────────────────────────

# Use real UUIDs because the router path param sci_id is typed as UUID
_SCI_UUID = "11111111-1111-1111-1111-111111111111"
_SCI_UUID_2 = "22222222-2222-2222-2222-222222222222"
_BIEN_ID = "bien-cloture"
_BAIL_ID = "bail-cloture"

_GERANT = {
    "id": "assoc-clot-1", "id_sci": _SCI_UUID,
    "user_id": "user-123", "nom": "Test User", "email": "t@t.fr",
    "part": 100, "role": "gerant",
}
_ASSOC_2 = {
    "id": "assoc-clot-2", "id_sci": _SCI_UUID_2,
    "user_id": "user-123", "nom": "Test User", "email": "t@t.fr",
    "part": 100, "role": "associe",
}
_BIEN = {"id": _BIEN_ID, "id_sci": _SCI_UUID, "adresse": "1 rue Test"}
_BAIL = {
    "id": _BAIL_ID, "id_bien": _BIEN_ID,
    "date_debut": "2024-01-01", "date_fin": "2027-12-31",
    "loyer_hc": 1000.0, "charges_locatives": 200.0,
    "statut": "en_cours",
}


def _setup_cloture(fake_supabase):
    """Setup data for bail clôture tests."""
    fake_supabase.store["associes"].extend([_GERANT, _ASSOC_2])
    fake_supabase.store["biens"].append(dict(_BIEN))
    fake_supabase.store["baux"].append(dict(_BAIL))
    fake_supabase.store.setdefault("bail_locataires", [])
    fake_supabase.store.setdefault("subscriptions", [])
    fake_supabase.store["subscriptions"].append({
        "user_id": "user-123", "plan_key": "pro", "status": "active",
        "is_active": True, "onboarding_completed": True,
    })


class TestBailCloture:
    """Tests for POST /scis/{sci_id}/biens/{bien_id}/baux/{bail_id}/cloturer."""

    def test_cloturer_bail_ok(self, client, auth_headers, fake_supabase):
        _setup_cloture(fake_supabase)
        payload = {
            "date_fin_effective": "2026-03-21",
            "etat_lieux_sortie": "2026-03-21",
            "depot_restitue_montant": 730.00,
            "retenues_detail": "Dégradations SDB: 350€",
            "motif": "Congé locataire",
        }
        resp = client.post(
            f"/api/v1/scis/{_SCI_UUID}/biens/{_BIEN_ID}/baux/{_BAIL_ID}/cloturer",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["statut"] == "termine"
        assert data["date_fin"] == "2026-03-21"

    def test_cloturer_bail_already_terminated(self, client, auth_headers, fake_supabase):
        _setup_cloture(fake_supabase)
        # Mark bail as already terminated
        for b in fake_supabase.store["baux"]:
            if b["id"] == _BAIL_ID:
                b["statut"] = "termine"
        payload = {"date_fin_effective": "2026-03-21"}
        resp = client.post(
            f"/api/v1/scis/{_SCI_UUID}/biens/{_BIEN_ID}/baux/{_BAIL_ID}/cloturer",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_cloturer_bail_not_found(self, client, auth_headers, fake_supabase):
        _setup_cloture(fake_supabase)
        payload = {"date_fin_effective": "2026-03-21"}
        resp = client.post(
            f"/api/v1/scis/{_SCI_UUID}/biens/{_BIEN_ID}/baux/nonexistent-bail/cloturer",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_cloturer_bail_wrong_sci(self, client, auth_headers, fake_supabase):
        _setup_cloture(fake_supabase)
        payload = {"date_fin_effective": "2026-03-21"}
        resp = client.post(
            f"/api/v1/scis/{_SCI_UUID_2}/biens/{_BIEN_ID}/baux/{_BAIL_ID}/cloturer",
            json=payload,
            headers=auth_headers,
        )
        # bien belongs to _SCI_UUID, not _SCI_UUID_2
        assert resp.status_code in (403, 404)

    def test_cloturer_bail_unauthenticated(self, client):
        payload = {"date_fin_effective": "2026-03-21"}
        resp = client.post(
            f"/api/v1/scis/{_SCI_UUID}/biens/{_BIEN_ID}/baux/{_BAIL_ID}/cloturer",
            json=payload,
        )
        assert resp.status_code == 401

    def test_cloturer_bail_minimal_payload(self, client, auth_headers, fake_supabase):
        _setup_cloture(fake_supabase)
        payload = {"date_fin_effective": "2026-03-21"}
        resp = client.post(
            f"/api/v1/scis/{_SCI_UUID}/biens/{_BIEN_ID}/baux/{_BAIL_ID}/cloturer",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["statut"] == "termine"
