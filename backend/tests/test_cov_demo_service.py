"""Tests for app/services/demo_service.py — seed + cleanup of demo data."""
from __future__ import annotations

import asyncio
import pytest

from tests.conftest import FakeSupabaseClient
from app.services import demo_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_client() -> FakeSupabaseClient:
    """Return a fresh FakeSupabaseClient with required tables initialized."""
    c = FakeSupabaseClient()
    # Ensure tables used by demo service exist
    for tbl in [
        "sci", "associes", "biens", "locataires", "baux", "bail_locataires",
        "loyers", "charges", "assurances_pno", "frais_agence", "credits_immobiliers",
        "fiscalite", "assemblees_generales", "mouvements_parts", "evenements_bien",
        "subscriptions",
    ]:
        c.store.setdefault(tbl, [])
    return c


# ---------------------------------------------------------------------------
# seed_demo_data tests
# ---------------------------------------------------------------------------

class TestSeedDemoData:

    def test_creates_sci(self):
        """seed_demo_data inserts a demo SCI record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-1"))

        sci_id = result["sci_id"]
        sci_rows = [r for r in c.store["sci"] if r["id"] == sci_id]
        assert len(sci_rows) == 1
        sci = sci_rows[0]
        assert sci["is_demo"] is True
        assert sci["nom"] == "SCI Résidence Belleville"
        assert sci["regime_fiscal"] == "IR"

    def test_creates_associes(self):
        """seed_demo_data creates 2 associés (gérant + co-associé)."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-1"))

        sci_id = result["sci_id"]
        assocs = [r for r in c.store["associes"] if r.get("id_sci") == sci_id]
        assert len(assocs) == 2
        roles = {a["role"] for a in assocs}
        assert "gerant" in roles
        assert "associe" in roles
        # Gérant is linked to user_id
        gerant = next(a for a in assocs if a["role"] == "gerant")
        assert gerant["user_id"] == "user-demo-1"
        assert gerant["is_demo"] is True

    def test_creates_bien(self):
        """seed_demo_data creates 1 demo bien linked to the SCI."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-2"))

        sci_id = result["sci_id"]
        bien_ids = result["bien_ids"]
        assert len(bien_ids) == 1

        biens = [r for r in c.store["biens"] if r["id_sci"] == sci_id]
        assert len(biens) == 1
        assert biens[0]["is_demo"] is True
        assert biens[0]["ville"] == "Lyon"
        assert biens[0]["id"] == bien_ids[0]

    def test_creates_locataire_and_bail(self):
        """seed_demo_data creates a locataire and a bail."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-3"))

        bien_id = result["bien_ids"][0]

        locataires = [r for r in c.store["locataires"] if r.get("id_bien") == bien_id]
        assert len(locataires) == 1
        assert locataires[0]["is_demo"] is True
        assert locataires[0]["nom"] == "Marie Lefèvre"

        baux = [r for r in c.store["baux"] if r.get("id_bien") == bien_id]
        assert len(baux) == 1
        assert baux[0]["is_demo"] is True
        assert baux[0]["statut"] == "en_cours"

    def test_creates_bail_locataires_link(self):
        """seed_demo_data inserts bail_locataires link row."""
        c = _fresh_client()
        asyncio.run(demo_service.seed_demo_data(c, "user-demo-4"))

        bl_rows = c.store.get("bail_locataires", [])
        assert len(bl_rows) >= 1

    def test_creates_six_loyers(self):
        """seed_demo_data inserts exactly 6 loyer rows for the bien."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-5"))

        bien_id = result["bien_ids"][0]
        loyers = [r for r in c.store["loyers"] if r.get("id_bien") == bien_id]
        assert len(loyers) == 6

        statuses = {r["statut"] for r in loyers}
        assert "paye" in statuses
        assert "en_retard" in statuses
        assert "en_attente" in statuses
        # All are demo
        assert all(r.get("is_demo") is True for r in loyers)

    def test_creates_charges(self):
        """seed_demo_data inserts charge rows for the bien."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-6"))

        bien_id = result["bien_ids"][0]
        charges = [r for r in c.store["charges"] if r.get("id_bien") == bien_id]
        assert len(charges) == 4
        assert all(r.get("is_demo") is True for r in charges)

    def test_creates_assurance_pno(self):
        """seed_demo_data inserts a PNO insurance record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-7"))

        bien_id = result["bien_ids"][0]
        pnos = [r for r in c.store["assurances_pno"] if r.get("id_bien") == bien_id]
        assert len(pnos) == 1
        assert pnos[0]["compagnie"] == "AXA"
        assert pnos[0]["is_demo"] is True

    def test_creates_frais_agence(self):
        """seed_demo_data inserts frais agence record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-8"))

        bien_id = result["bien_ids"][0]
        frais = [r for r in c.store["frais_agence"] if r.get("id_bien") == bien_id]
        assert len(frais) == 1
        assert frais[0]["nom_agence"] == "Nexity Gestion"

    def test_creates_credit_immobilier(self):
        """seed_demo_data inserts a credit immobilier record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-9"))

        bien_id = result["bien_ids"][0]
        credits = [r for r in c.store["credits_immobiliers"] if r.get("id_bien") == bien_id]
        assert len(credits) == 1
        assert credits[0]["banque"] == "Crédit Agricole"

    def test_creates_fiscalite(self):
        """seed_demo_data inserts a fiscalite record for last year."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-10"))

        sci_id = result["sci_id"]
        from datetime import datetime, timezone
        last_year = datetime.now(timezone.utc).year - 1
        fisc = [r for r in c.store["fiscalite"] if r.get("id_sci") == sci_id]
        assert len(fisc) == 1
        assert fisc[0]["annee"] == last_year
        assert fisc[0]["total_revenus"] == 10200

    def test_creates_assemblees_generales(self):
        """seed_demo_data inserts an AG record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-11"))

        sci_id = result["sci_id"]
        ags = [r for r in c.store["assemblees_generales"] if r.get("id_sci") == sci_id]
        assert len(ags) == 1
        assert ags[0]["type_ag"] == "ordinaire"

    def test_creates_mouvements_parts(self):
        """seed_demo_data inserts a mouvement de parts record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-12"))

        sci_id = result["sci_id"]
        mvts = [r for r in c.store["mouvements_parts"] if r.get("id_sci") == sci_id]
        assert len(mvts) == 1
        assert mvts[0]["type_mouvement"] == "cession"

    def test_creates_evenement_bien(self):
        """seed_demo_data inserts an evenement_bien record."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-13"))

        bien_id = result["bien_ids"][0]
        evts = [r for r in c.store["evenements_bien"] if r.get("id_bien") == bien_id]
        assert len(evts) == 1
        assert evts[0]["type"] == "travaux"

    def test_marks_subscription_demo_seeded_when_exists(self):
        """When subscription already exists, demo_seeded is set to True."""
        c = _fresh_client()
        c.store["subscriptions"] = [
            {"id": "sub-x", "user_id": "user-demo-14", "status": "demo", "demo_seeded": False}
        ]
        asyncio.run(demo_service.seed_demo_data(c, "user-demo-14"))

        sub = c.store["subscriptions"][0]
        assert sub["demo_seeded"] is True

    def test_creates_subscription_when_missing(self):
        """When no subscription exists, a demo subscription is created."""
        c = _fresh_client()
        c.store["subscriptions"] = []

        asyncio.run(demo_service.seed_demo_data(c, "user-demo-15"))

        subs = [r for r in c.store["subscriptions"] if r.get("user_id") == "user-demo-15"]
        assert len(subs) == 1
        assert subs[0]["demo_seeded"] is True
        assert subs[0]["status"] == "demo"

    def test_returns_dict_with_sci_id_and_bien_ids(self):
        """Return value has sci_id and bien_ids keys."""
        c = _fresh_client()
        result = asyncio.run(demo_service.seed_demo_data(c, "user-demo-16"))

        assert "sci_id" in result
        assert "bien_ids" in result
        assert isinstance(result["sci_id"], str)
        assert isinstance(result["bien_ids"], list)
        assert len(result["bien_ids"]) == 1

    def test_multiple_users_independent(self):
        """Seeding two different users creates independent data sets."""
        c = _fresh_client()
        r1 = asyncio.run(demo_service.seed_demo_data(c, "user-A"))
        r2 = asyncio.run(demo_service.seed_demo_data(c, "user-B"))

        assert r1["sci_id"] != r2["sci_id"]
        assert r1["bien_ids"][0] != r2["bien_ids"][0]


# ---------------------------------------------------------------------------
# cleanup_demo_data tests
# ---------------------------------------------------------------------------

class TestCleanupDemoData:

    def test_returns_zero_when_no_demo_data(self):
        """cleanup_demo_data returns 0 when there are no demo associes."""
        c = _fresh_client()
        # No demo associes
        c.store["associes"] = [
            {"id": "a1", "id_sci": "sci-real", "user_id": "user-Z", "is_demo": False}
        ]
        result = asyncio.run(demo_service.cleanup_demo_data(c, "user-Z"))
        assert result == 0

    def test_cleanup_removes_sci_and_associes(self):
        """After seed + cleanup, the demo SCI is removed and gerant associe is cleaned up."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-1"))
        sci_id = result_seed["sci_id"]

        # Verify data was seeded
        assert any(r["id"] == sci_id for r in c.store["sci"])
        # Gérant associé linked to this user
        assert any(
            r.get("id_sci") == sci_id and r.get("is_demo") and r.get("user_id") == "user-cleanup-1"
            for r in c.store["associes"]
        )

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-1"))

        # SCI should be gone
        assert not any(r["id"] == sci_id for r in c.store["sci"])
        # Gérant associé for this user should be gone
        assert not any(
            r.get("id_sci") == sci_id and r.get("user_id") == "user-cleanup-1"
            for r in c.store["associes"]
        )

    def test_cleanup_removes_demo_biens(self):
        """Cleanup removes demo biens."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-2"))
        bien_id = result_seed["bien_ids"][0]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-2"))

        assert not any(r["id"] == bien_id for r in c.store["biens"])

    def test_cleanup_removes_demo_loyers(self):
        """Cleanup removes demo loyer rows."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-3"))
        bien_id = result_seed["bien_ids"][0]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-3"))

        remaining = [r for r in c.store["loyers"] if r.get("id_bien") == bien_id]
        assert remaining == []

    def test_cleanup_removes_demo_charges(self):
        """Cleanup removes demo charge rows."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-4"))
        bien_id = result_seed["bien_ids"][0]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-4"))

        remaining = [r for r in c.store["charges"] if r.get("id_bien") == bien_id]
        assert remaining == []

    def test_cleanup_removes_assurance_pno(self):
        """Cleanup removes demo assurance PNO rows."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-5"))
        bien_id = result_seed["bien_ids"][0]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-5"))

        remaining = [r for r in c.store["assurances_pno"] if r.get("id_bien") == bien_id]
        assert remaining == []

    def test_cleanup_removes_frais_agence(self):
        """Cleanup removes frais agence rows."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-6"))
        bien_id = result_seed["bien_ids"][0]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-6"))

        remaining = [r for r in c.store["frais_agence"] if r.get("id_bien") == bien_id]
        assert remaining == []

    def test_cleanup_removes_fiscalite(self):
        """Cleanup removes fiscalité records for demo SCI."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-7"))
        sci_id = result_seed["sci_id"]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-7"))

        remaining = [r for r in c.store["fiscalite"] if r.get("id_sci") == sci_id]
        assert remaining == []

    def test_cleanup_removes_assemblees_generales(self):
        """Cleanup removes AG records for demo SCI."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-8"))
        sci_id = result_seed["sci_id"]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-8"))

        remaining = [r for r in c.store["assemblees_generales"] if r.get("id_sci") == sci_id]
        assert remaining == []

    def test_cleanup_removes_mouvements_parts(self):
        """Cleanup removes mouvements de parts for demo SCI."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-9"))
        sci_id = result_seed["sci_id"]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-9"))

        remaining = [r for r in c.store["mouvements_parts"] if r.get("id_sci") == sci_id]
        assert remaining == []

    def test_cleanup_removes_baux_and_locataires(self):
        """Cleanup removes baux and locataires for demo biens."""
        c = _fresh_client()
        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-10"))
        bien_id = result_seed["bien_ids"][0]

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-10"))

        remaining_baux = [r for r in c.store["baux"] if r.get("id_bien") == bien_id]
        remaining_locs = [r for r in c.store["locataires"] if r.get("id_bien") == bien_id]
        assert remaining_baux == []
        assert remaining_locs == []

    def test_cleanup_resets_demo_seeded_flag(self):
        """Cleanup resets demo_seeded and onboarding_completed on the subscription."""
        c = _fresh_client()
        c.store["subscriptions"] = [
            {"id": "sub-u11", "user_id": "user-cleanup-11", "status": "demo", "demo_seeded": True, "onboarding_completed": True}
        ]
        # Add a demo associe so cleanup finds the user
        c.store["associes"].append({
            "id": "assoc-fake", "id_sci": "sci-fake", "user_id": "user-cleanup-11", "is_demo": True
        })
        # Add the sci too so delete works
        c.store["sci"].append({"id": "sci-fake", "is_demo": True})

        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-11"))

        subs = [r for r in c.store["subscriptions"] if r.get("user_id") == "user-cleanup-11"]
        assert len(subs) == 1
        assert subs[0]["demo_seeded"] is False
        assert subs[0]["onboarding_completed"] is False

    def test_cleanup_returns_positive_deleted_count(self):
        """cleanup_demo_data returns the number of deleted rows (> 0 after seed)."""
        c = _fresh_client()
        asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-12"))

        deleted = asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-12"))
        assert deleted > 0

    def test_cleanup_does_not_touch_real_data(self):
        """Non-demo data from other users is untouched by cleanup."""
        c = _fresh_client()
        # Real (non-demo) SCI from another user
        c.store["sci"].append({"id": "sci-real", "is_demo": False})
        c.store["associes"].append({
            "id": "a-real", "id_sci": "sci-real", "user_id": "user-other", "is_demo": False
        })
        c.store["biens"].append({
            "id": "bien-real", "id_sci": "sci-real", "is_demo": False
        })

        # Seed + cleanup for demo user
        asyncio.run(demo_service.seed_demo_data(c, "user-cleanup-13"))
        asyncio.run(demo_service.cleanup_demo_data(c, "user-cleanup-13"))

        # Real data still present
        assert any(r["id"] == "sci-real" for r in c.store["sci"])
        assert any(r["id"] == "bien-real" for r in c.store["biens"])

    def test_seed_then_cleanup_full_roundtrip(self):
        """Full roundtrip: seed then cleanup leaves store clean."""
        c = _fresh_client()
        initial_sci_count = len(c.store["sci"])

        result_seed = asyncio.run(demo_service.seed_demo_data(c, "user-roundtrip"))
        sci_id = result_seed["sci_id"]

        # SCI was added
        assert len(c.store["sci"]) == initial_sci_count + 1

        asyncio.run(demo_service.cleanup_demo_data(c, "user-roundtrip"))

        # SCI was removed
        assert len(c.store["sci"]) == initial_sci_count
        assert not any(r["id"] == sci_id for r in c.store["sci"])
