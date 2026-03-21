"""Tests for lifecycle features: avenant, recurring charges, sinistre, feuille presence, calendrier fiscal."""

from __future__ import annotations

import pytest

# ──────────────────────────────────────────────────────────────
# UUIDs for tests (endpoints require valid UUIDs)
# ──────────────────────────────────────────────────────────────

SCI_UUID = "11111111-1111-1111-1111-111111111111"
AG_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
BIEN_ID = "bien-test-1"
BAIL_ID = "bail-test-1"

ACTIVE_SUB = {
    "user_id": "user-123",
    "plan_key": "pro",
    "status": "active",
    "is_active": True,
    "onboarding_completed": True,
}

GERANT_ASSOCIE = {
    "id": "associe-uuid-g",
    "id_sci": SCI_UUID,
    "user_id": "user-123",
    "nom": "Test Gerant",
    "email": "gerant@test.fr",
    "part": 60,
    "role": "gerant",
}

ASSOC_B = {
    "id": "associe-uuid-b",
    "id_sci": SCI_UUID,
    "user_id": "user-456",
    "nom": "Camille Bernard",
    "email": "camille@test.fr",
    "part": 40,
    "role": "associe",
}


def _seed(fake_supabase):
    """Seed the store with UUID-keyed data for lifecycle tests."""
    fake_supabase.store["sci"] = [
        {"id": SCI_UUID, "nom": "SCI Test Lifecycle", "siren": "111222333", "regime_fiscal": "IR", "adresse_siege": "1 rue Test", "capital_social": 10000, "nom_gerant": "Test Gerant"},
    ]
    fake_supabase.store["associes"] = [GERANT_ASSOCIE, ASSOC_B]
    fake_supabase.store["subscriptions"] = [ACTIVE_SUB]
    fake_supabase.store["biens"] = [
        {"id": BIEN_ID, "id_sci": SCI_UUID, "adresse": "10 rue de la Paix", "ville": "Paris", "code_postal": "75001", "type_bien": "appartement", "type_locatif": "nu", "surface_m2": 50},
    ]
    fake_supabase.store["baux"] = [
        {"id": BAIL_ID, "id_bien": BIEN_ID, "date_debut": "2025-01-01", "date_fin": "2027-12-31", "loyer_hc": 1000.0, "charges_locatives": 200.0, "statut": "en_cours"},
    ]
    fake_supabase.store["assurances_pno"] = [
        {"id": "pno-test", "id_bien": BIEN_ID, "compagnie": "MAIF", "date_echeance": "2026-06-01", "montant_annuel": 280},
    ]
    fake_supabase.store["evenements_bien"] = []
    fake_supabase.store["notifications"] = []
    fake_supabase.store["calendrier_fiscal"] = []
    fake_supabase.store["assemblees_generales"] = [
        {"id": AG_UUID, "id_sci": SCI_UUID, "date_ag": "2026-06-15", "type_ag": "ordinaire", "exercice_annee": 2025, "quorum_atteint": False},
    ]


# ──────────────────────────────────────────────────────────────
# TASK 1: Avenant bail
# ──────────────────────────────────────────────────────────────


class TestAvenantBail:
    """POST /api/v1/scis/{sci_id}/biens/{bien_id}/baux/{bail_id}/avenant"""

    def test_avenant_revision_loyer(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/{BAIL_ID}/avenant",
            json={
                "type_avenant": "revision_loyer",
                "nouveau_loyer_hc": 1350,
                "date_effet": "2026-04-01",
                "motif": "Revision IRL T1 2026",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "avenant" in data
        assert "bail_updated" in data
        assert data["bail_updated"]["loyer_hc"] == 1350

        # Verify evenement was created
        events = fake_supabase.store.get("evenements_bien", [])
        assert len(events) == 1
        assert events[0]["type"] == "avenant"

    def test_avenant_modification_charges(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/{BAIL_ID}/avenant",
            json={
                "type_avenant": "modification_charges",
                "nouvelles_charges": 250,
                "date_effet": "2026-04-01",
                "motif": "Regularisation charges",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["bail_updated"]["charges_locatives"] == 250

    def test_avenant_invalid_type(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/{BAIL_ID}/avenant",
            json={
                "type_avenant": "invalid_type",
                "date_effet": "2026-04-01",
                "motif": "Test",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_avenant_bail_not_found(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/nonexistent/avenant",
            json={
                "type_avenant": "revision_loyer",
                "nouveau_loyer_hc": 1500,
                "date_effet": "2026-04-01",
                "motif": "Test",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_avenant_creates_notification(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/{BAIL_ID}/avenant",
            json={
                "type_avenant": "ajout_locataire",
                "date_effet": "2026-05-01",
                "motif": "Ajout colocataire",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Check that notification was created
        notifs = fake_supabase.store.get("notifications", [])
        assert len(notifs) >= 1


# ──────────────────────────────────────────────────────────────
# TASK 2: Charges recurrentes auto-generees
# ──────────────────────────────────────────────────────────────


class TestRecurringCharges:
    """check_recurring_charges in notification_cron.py"""

    @pytest.mark.asyncio
    async def test_recurring_charges_on_quarter_start(self, fake_supabase):
        from unittest.mock import patch
        from datetime import date
        from app.services.notification_cron import check_recurring_charges

        fake_supabase.store["biens"] = [
            {"id": "bien-rc-1", "id_sci": "sci-rc-1"},
        ]
        fake_supabase.store["charges"] = [
            {"id": "ch-1", "id_bien": "bien-rc-1", "id_sci": "sci-rc-1", "type_charge": "copropriete", "montant": 500, "date_paiement": "2025-10-01"},
        ]

        with patch("app.services.notification_cron.date") as mock_date:
            mock_date.today.return_value = date(2026, 1, 1)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            created = await check_recurring_charges(fake_supabase)

        assert created >= 1
        new_charges = [c for c in fake_supabase.store["charges"] if c.get("date_paiement") == "2026-01-01"]
        assert len(new_charges) >= 1
        assert new_charges[0]["montant"] == 500

    @pytest.mark.asyncio
    async def test_recurring_charges_not_on_quarter_start(self, fake_supabase):
        from unittest.mock import patch
        from datetime import date
        from app.services.notification_cron import check_recurring_charges

        with patch("app.services.notification_cron.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 15)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            created = await check_recurring_charges(fake_supabase)

        assert created == 0

    @pytest.mark.asyncio
    async def test_recurring_charges_dedup(self, fake_supabase):
        from unittest.mock import patch
        from datetime import date
        from app.services.notification_cron import check_recurring_charges

        fake_supabase.store["biens"] = [
            {"id": "bien-rc-2", "id_sci": "sci-rc-2"},
        ]
        fake_supabase.store["charges"] = [
            {"id": "ch-old", "id_bien": "bien-rc-2", "id_sci": "sci-rc-2", "type_charge": "copropriete", "montant": 500, "date_paiement": "2025-10-01"},
            {"id": "ch-dup", "id_bien": "bien-rc-2", "id_sci": "sci-rc-2", "type_charge": "copropriete", "montant": 500, "date_paiement": "2026-01-15"},
        ]

        with patch("app.services.notification_cron.date") as mock_date:
            mock_date.today.return_value = date(2026, 1, 1)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            created = await check_recurring_charges(fake_supabase)

        # Should NOT create copropriete for bien-rc-2 (already exists in Q1)
        copro_charges = [c for c in fake_supabase.store["charges"]
                         if c["id_bien"] == "bien-rc-2" and c["type_charge"] == "copropriete"
                         and c.get("date_paiement", "") >= "2026-01-01"
                         and c.get("date_paiement", "") <= "2026-03-31"]
        assert len(copro_charges) == 1
        assert created == 0


# ──────────────────────────────────────────────────────────────
# TASK 3: Declaration sinistre PNO
# ──────────────────────────────────────────────────────────────


class TestDeclarationSinistre:
    """POST /api/v1/scis/{sci_id}/biens/{bien_id}/sinistre"""

    def test_declare_sinistre_success(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/sinistre",
            json={
                "date_sinistre": "2026-03-15",
                "description": "Degat des eaux SDB",
                "montant_estime": 2500,
                "numero_dossier": "SIN-2026-001",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "evenement" in data
        assert "assurance_pno" in data
        assert data["evenement"]["type"] == "sinistre"
        assert data["assurance_pno"]["compagnie"] == "MAIF"

        events = fake_supabase.store.get("evenements_bien", [])
        assert len(events) == 1
        assert events[0]["type"] == "sinistre"
        assert "SIN-2026-001" in events[0]["titre"]

    def test_declare_sinistre_without_pno(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        fake_supabase.store["assurances_pno"] = []

        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/sinistre",
            json={
                "date_sinistre": "2026-03-15",
                "description": "Incendie mineur",
                "montant_estime": 1000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["assurance_pno"] is None

    def test_declare_sinistre_creates_notification(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/sinistre",
            json={
                "date_sinistre": "2026-03-15",
                "description": "Degat des eaux",
                "montant_estime": 3000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

        notifs = fake_supabase.store.get("notifications", [])
        assert len(notifs) >= 1

    def test_declare_sinistre_bien_not_found(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/biens/nonexistent/sinistre",
            json={
                "date_sinistre": "2026-03-15",
                "description": "Test",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# TASK 4: Feuille de presence AG
# ──────────────────────────────────────────────────────────────


class TestFeuillePresenceAG:
    """GET/POST /api/v1/scis/{sci_id}/assemblees-generales/{ag_id}/feuille-presence"""

    def test_get_feuille_presence(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.get(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{AG_UUID}/feuille-presence",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sci_nom"] == "SCI Test Lifecycle"
        assert data["date_ag"] == "2026-06-15"
        assert data["type_ag"] == "ordinaire"
        assert len(data["associes"]) == 2
        assert data["total_parts"] == 100
        assert data["quorum_atteint"] is None

        assoc_60 = next(a for a in data["associes"] if a["nb_parts"] == 60)
        assert assoc_60["pct"] == 60.0

    def test_get_feuille_presence_ag_not_found(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        unknown_ag = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        resp = client.get(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{unknown_ag}/feuille-presence",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_post_feuille_presence_quorum_atteint(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{AG_UUID}/feuille-presence",
            json={
                "presences": [
                    {"associe_id": "associe-uuid-g", "present": True},
                    {"associe_id": "associe-uuid-b", "present": True},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["quorum_atteint"] is True
        assert data["parts_presentes"] == 100
        assert data["total_parts"] == 100
        assert data["pourcentage_present"] == 100.0

        ag = next(a for a in fake_supabase.store["assemblees_generales"] if a["id"] == AG_UUID)
        assert ag["quorum_atteint"] is True

    def test_post_feuille_presence_quorum_non_atteint(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{AG_UUID}/feuille-presence",
            json={
                "presences": [
                    {"associe_id": "associe-uuid-g", "present": False},
                    {"associe_id": "associe-uuid-b", "present": True},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["quorum_atteint"] is False
        assert data["parts_presentes"] == 40
        assert data["pourcentage_present"] == 40.0

    def test_post_feuille_presence_majority_present(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{AG_UUID}/feuille-presence",
            json={
                "presences": [
                    {"associe_id": "associe-uuid-g", "present": True},
                    {"associe_id": "associe-uuid-b", "present": False},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["quorum_atteint"] is True
        assert data["pourcentage_present"] == 60.0


# ──────────────────────────────────────────────────────────────
# TASK 5: Calendrier fiscal avec statut
# ──────────────────────────────────────────────────────────────


class TestCalendrierFiscal:
    """GET/POST /api/v1/scis/{sci_id}/calendrier-fiscal/{annee}"""

    def test_get_calendrier_fiscal_ir(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.get(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["annee"] == 2026
        echeances = data["echeances"]
        keys = [e["key"] for e in echeances]

        # IR regime: should have 2072, 2044, taxe_fonciere, cfe, ag
        assert "2072" in keys
        assert "2044" in keys
        assert "taxe_fonciere" in keys
        assert "cfe" in keys
        assert "ag" in keys
        # Should NOT have liasse_is (IS-only)
        assert "liasse_is" not in keys

        # All should be a_faire initially (except possibly ag)
        for e in echeances:
            if e["key"] != "ag":
                assert e["statut"] == "a_faire"

    def test_get_calendrier_fiscal_is(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        # Change SCI to IS regime
        fake_supabase.store["sci"][0]["regime_fiscal"] = "IS"

        resp = client.get(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        keys = [e["key"] for e in data["echeances"]]

        assert "liasse_is" in keys
        assert "taxe_fonciere" in keys
        # Should NOT have 2072, 2044 (IR-only)
        assert "2072" not in keys
        assert "2044" not in keys

    def test_get_calendrier_fiscal_ag_auto_detected(self, client, auth_headers, fake_supabase):
        """AG held for exercice_annee=2025 should appear as 'fait' in the 2025 calendar."""
        _seed(fake_supabase)
        resp = client.get(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2025",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        ag_echeance = next((e for e in data["echeances"] if e["key"] == "ag"), None)
        assert ag_echeance is not None
        assert ag_echeance["statut"] == "fait"
        assert ag_echeance["date_realisation"] == "2026-06-15"

    def test_marquer_echeance_faite(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026/2072/marquer-fait",
            json={"date_realisation": "2026-05-02"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["key"] == "2072"
        assert data["statut"] == "fait"
        assert data["date_realisation"] == "2026-05-02"

        # Now check the calendar reflects it
        resp2 = client.get(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026",
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        echeances = resp2.json()["echeances"]
        e2072 = next(e for e in echeances if e["key"] == "2072")
        assert e2072["statut"] == "fait"
        assert e2072["date_realisation"] == "2026-05-02"

    def test_marquer_echeance_invalid_key(self, client, auth_headers, fake_supabase):
        _seed(fake_supabase)
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026/invalid_key/marquer-fait",
            json={"date_realisation": "2026-05-02"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_marquer_echeance_upsert(self, client, auth_headers, fake_supabase):
        """Marking the same echeance twice should update, not duplicate."""
        _seed(fake_supabase)
        client.post(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026/taxe_fonciere/marquer-fait",
            json={"date_realisation": "2026-10-10"},
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/v1/scis/{SCI_UUID}/calendrier-fiscal/2026/taxe_fonciere/marquer-fait",
            json={"date_realisation": "2026-10-12"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["date_realisation"] == "2026-10-12"

        records = [r for r in fake_supabase.store.get("calendrier_fiscal", [])
                   if r.get("echeance_key") == "taxe_fonciere" and r.get("annee") == 2026]
        assert len(records) == 1
