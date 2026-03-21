"""Tests for SCI & Bien lifecycle endpoints (dissolution, gérant change, capital, cession)."""

from __future__ import annotations

import pytest

# Use UUID-formatted IDs since the lifecycle router uses UUID path params via require_gerant_role
SCI_ID = "00000000-0000-0000-0000-000000000010"
BIEN_ID = "00000000-0000-0000-0000-000000000020"
BIEN_FREE_ID = "00000000-0000-0000-0000-000000000021"
ASSOC_GERANT_ID = "00000000-0000-0000-0000-000000000030"
ASSOC_OTHER_ID = "00000000-0000-0000-0000-000000000031"


@pytest.fixture(autouse=True)
def _setup_lifecycle_data(fake_supabase):
    """Inject lifecycle test data with UUID-formatted IDs into the fake store."""
    fake_supabase.store["sci"].append({
        "id": SCI_ID, "nom": "SCI Lifecycle Test", "siren": "111222333",
        "regime_fiscal": "IR", "capital_social": 10000, "nom_gerant": "Gérant Test",
        "nb_parts_total": 100, "valeur_nominale_part": 100,
    })
    fake_supabase.store["biens"].append({
        "id": BIEN_ID, "id_sci": SCI_ID, "adresse": "1 rue Lifecycle",
        "ville": "Paris", "code_postal": "75001", "type_bien": "appartement",
        "loyer_cc": 1200, "statut": "loue", "tmi": 30, "prix_acquisition": 200000,
    })
    fake_supabase.store["biens"].append({
        "id": BIEN_FREE_ID, "id_sci": SCI_ID, "adresse": "2 rue Vacant",
        "ville": "Paris", "code_postal": "75002", "type_bien": "studio",
        "loyer_cc": 800, "statut": "vacant", "tmi": 30,
    })
    fake_supabase.store["baux"].append({
        "id": "bail-lc-1", "id_bien": BIEN_ID, "date_debut": "2025-01-01",
        "date_fin": "2027-12-31", "loyer_hc": 1000, "charges_locatives": 200,
        "statut": "en_cours",
    })
    fake_supabase.store["associes"].append({
        "id": ASSOC_GERANT_ID, "id_sci": SCI_ID, "user_id": "user-123",
        "nom": "Gérant Test", "email": "gerant@test.fr", "part": 60, "role": "gerant",
        "nb_parts": 60,
    })
    fake_supabase.store["associes"].append({
        "id": ASSOC_OTHER_ID, "id_sci": SCI_ID, "user_id": "user-456",
        "nom": "Associé Test", "email": "associe@test.fr", "part": 40, "role": "associe",
        "nb_parts": 40,
    })


# ──────────────────────────────────────────────────────────────
# TASK 1: Dissolution SCI
# ──────────────────────────────────────────────────────────────


class TestDissolutionSCI:
    """POST /api/v1/scis/{sci_id}/dissoudre"""

    def test_dissolve_sci_with_active_baux_rejected(self, client, auth_headers):
        """Cannot dissolve SCI when baux are still active."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/dissoudre",
            json={
                "date_dissolution": "2026-03-21",
                "motif": "Décision unanime des associés",
                "liquidateur": "Marie Dupont",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "baux" in resp.json()["error"].lower()

    def test_dissolve_sci_success(self, client, auth_headers, fake_supabase):
        """Dissolve SCI after terminating all baux."""
        # Terminate all active baux for this SCI's biens
        for bail in fake_supabase.store["baux"]:
            if bail.get("id_bien") == BIEN_ID:
                bail["statut"] = "termine"

        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/dissoudre",
            json={
                "date_dissolution": "2026-03-21",
                "motif": "Décision unanime des associés",
                "liquidateur": "Marie Dupont",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["statut"] == "dissoute"
        assert data["date_dissolution"] == "2026-03-21"
        assert data["motif_dissolution"] == "Décision unanime des associés"
        assert data["liquidateur"] == "Marie Dupont"

        # Verify SCI statut updated in store
        sci = next(s for s in fake_supabase.store["sci"] if s["id"] == SCI_ID)
        assert sci["statut"] == "dissoute"

        # Verify notifications were created
        notifications = [
            n for n in fake_supabase.store.get("notifications", [])
            if n.get("type") == "dissolution"
        ]
        assert len(notifications) >= 1

    def test_dissolve_already_dissolved_rejected(self, client, auth_headers, fake_supabase):
        """Cannot dissolve an already dissolved SCI."""
        for sci in fake_supabase.store["sci"]:
            if sci["id"] == SCI_ID:
                sci["statut"] = "dissoute"
        for bail in fake_supabase.store["baux"]:
            if bail.get("id_bien") == BIEN_ID:
                bail["statut"] = "termine"

        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/dissoudre",
            json={
                "date_dissolution": "2026-03-22",
                "motif": "Re-dissolution",
                "liquidateur": "Test",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "déjà dissoute" in resp.json()["error"]


# ──────────────────────────────────────────────────────────────
# TASK 2: Changement de gérant
# ──────────────────────────────────────────────────────────────


class TestChangerGerant:
    """POST /api/v1/scis/{sci_id}/changer-gerant"""

    def test_changer_gerant_success(self, client, auth_headers, fake_supabase):
        """Successfully change gérant."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/changer-gerant",
            json={
                "nouveau_gerant_associe_id": ASSOC_OTHER_ID,
                "date_effet": "2026-04-01",
                "ag_id": "ag-001",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nouveau_gerant"] == "Associé Test"
        assert data["ancien_gerant"] == "Gérant Test"
        assert data["date_effet"] == "2026-04-01"

        # Verify roles updated in store
        old_gerant = next(a for a in fake_supabase.store["associes"] if a["id"] == ASSOC_GERANT_ID)
        assert old_gerant["role"] == "associe"

        new_gerant = next(a for a in fake_supabase.store["associes"] if a["id"] == ASSOC_OTHER_ID)
        assert new_gerant["role"] == "gerant"

        # Verify SCI nom_gerant updated
        sci = next(s for s in fake_supabase.store["sci"] if s["id"] == SCI_ID)
        assert sci["nom_gerant"] == "Associé Test"

    def test_changer_gerant_nonexistent_associe(self, client, auth_headers):
        """Reject if target associé does not exist."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/changer-gerant",
            json={
                "nouveau_gerant_associe_id": "00000000-0000-0000-0000-999999999999",
                "date_effet": "2026-04-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_changer_gerant_already_gerant(self, client, auth_headers):
        """Reject if target is already gérant."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/changer-gerant",
            json={
                "nouveau_gerant_associe_id": ASSOC_GERANT_ID,
                "date_effet": "2026-04-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "déjà gérant" in resp.json()["error"]


# ──────────────────────────────────────────────────────────────
# TASK 3: Modification du capital
# ──────────────────────────────────────────────────────────────


class TestModifierCapital:
    """POST /api/v1/scis/{sci_id}/modifier-capital"""

    def test_augmentation_capital_success(self, client, auth_headers, fake_supabase):
        """Successfully increase capital."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/modifier-capital",
            json={
                "nouveau_capital": 200000,
                "nouveau_nb_parts": 1333,
                "nouvelle_valeur_nominale": 150,
                "type": "augmentation",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nouveau_capital"] == 200000
        assert data["nouveau_nb_parts"] == 1333
        assert data["nouvelle_valeur_nominale"] == 150
        assert data["type"] == "augmentation"
        assert data["ancien_capital"] == 10000

        # Verify SCI updated in store
        sci = next(s for s in fake_supabase.store["sci"] if s["id"] == SCI_ID)
        assert sci["capital_social"] == 200000
        assert sci["nb_parts_total"] == 1333
        assert sci["valeur_nominale_part"] == 150

        # Verify mouvement_parts record created
        mouvements = fake_supabase.store.get("mouvements_parts", [])
        assert len(mouvements) >= 1
        last = mouvements[-1]
        assert last["type_mouvement"] == "augmentation"

    def test_reduction_capital_success(self, client, auth_headers):
        """Successfully decrease capital."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/modifier-capital",
            json={
                "nouveau_capital": 5000,
                "nouveau_nb_parts": 50,
                "nouvelle_valeur_nominale": 100,
                "type": "reduction",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "reduction"
        assert data["nouveau_capital"] == 5000

    def test_augmentation_with_lower_capital_rejected(self, client, auth_headers):
        """Augmentation must be higher than current capital."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/modifier-capital",
            json={
                "nouveau_capital": 5000,
                "nouveau_nb_parts": 50,
                "nouvelle_valeur_nominale": 100,
                "type": "augmentation",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ──────────────────────────────────────────────────────────────
# TASK 4: Acquisition bien (enhanced create)
# ──────────────────────────────────────────────────────────────


class TestAcquisitionBien:
    """POST /api/v1/scis/{sci_id}/biens with acquisition data"""

    def test_create_bien_with_acquisition_creates_event(self, client, auth_headers, fake_supabase):
        """Creating a bien with acquisition data should auto-create an acquisition event."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens",
            json={
                "id_sci": SCI_ID,
                "adresse": "10 rue des Tests",
                "ville": "Paris",
                "code_postal": "75010",
                "loyer_cc": 1500,
                "prix_acquisition": 250000,
                "acquisition_date": "2026-01-15",
                "frais_notaire": 18000,
                "frais_agence_acquisition": 12000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        bien_id = data["id"]

        # Verify evenement was created
        events = [
            e for e in fake_supabase.store.get("evenements_bien", [])
            if e.get("id_bien") == bien_id and e.get("type") == "acquisition"
        ]
        assert len(events) == 1
        event = events[0]
        assert event["montant"] == 280000  # 250000 + 18000 + 12000
        assert "250000" in event["description"]

    def test_create_bien_without_acquisition_no_event(self, client, auth_headers, fake_supabase):
        """Creating a bien without acquisition data should not create an event."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens",
            json={
                "id_sci": SCI_ID,
                "adresse": "20 rue Simple",
                "ville": "Lyon",
                "code_postal": "69001",
                "loyer_cc": 800,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        events = fake_supabase.store.get("evenements_bien", [])
        assert len(events) == 0


# ──────────────────────────────────────────────────────────────
# TASK 5: Cession / vente bien
# ──────────────────────────────────────────────────────────────


class TestCessionBien:
    """POST /api/v1/scis/{sci_id}/biens/{bien_id}/ceder"""

    def test_ceder_bien_with_active_bail_rejected(self, client, auth_headers):
        """Cannot sell a bien with active baux."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens/{BIEN_ID}/ceder",
            json={
                "prix_cession": 350000,
                "date_cession": "2026-06-01",
                "acquereur": "M. Durand",
                "frais_cession": 15000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "baux" in resp.json()["error"].lower()

    def test_ceder_bien_success(self, client, auth_headers, fake_supabase):
        """Successfully sell a bien after terminating baux."""
        for bail in fake_supabase.store["baux"]:
            if bail.get("id_bien") == BIEN_ID:
                bail["statut"] = "termine"

        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens/{BIEN_ID}/ceder",
            json={
                "prix_cession": 350000,
                "date_cession": "2026-06-01",
                "acquereur": "M. Durand",
                "frais_cession": 15000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["statut"] == "cede"
        assert data["prix_cession"] == 350000
        assert data["acquereur"] == "M. Durand"
        assert data["plus_value_brute"] == 150000  # 350000 - 200000

        # Verify bien updated in store
        bien = next(b for b in fake_supabase.store["biens"] if b["id"] == BIEN_ID)
        assert bien["statut"] == "cede"

        # Verify cession event created
        events = [
            e for e in fake_supabase.store.get("evenements_bien", [])
            if e.get("id_bien") == BIEN_ID and e.get("type") == "cession"
        ]
        assert len(events) == 1

    def test_ceder_bien_already_sold(self, client, auth_headers, fake_supabase):
        """Cannot sell an already sold bien."""
        for bail in fake_supabase.store["baux"]:
            if bail.get("id_bien") == BIEN_ID:
                bail["statut"] = "termine"
        for bien in fake_supabase.store["biens"]:
            if bien["id"] == BIEN_ID:
                bien["statut"] = "cede"

        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens/{BIEN_ID}/ceder",
            json={
                "prix_cession": 350000,
                "date_cession": "2026-06-01",
                "acquereur": "M. Durand",
                "frais_cession": 15000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "déjà été cédé" in resp.json()["error"]

    def test_ceder_bien_no_acquisition_price(self, client, auth_headers, fake_supabase):
        """Cession without prix_acquisition returns null plus_value."""
        # Use the bien without prix_acquisition
        for bail in fake_supabase.store["baux"]:
            if bail.get("id_bien") == BIEN_ID:
                bail["statut"] = "termine"
        # Remove prix_acquisition
        for bien in fake_supabase.store["biens"]:
            if bien["id"] == BIEN_ID:
                bien.pop("prix_acquisition", None)

        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens/{BIEN_ID}/ceder",
            json={
                "prix_cession": 350000,
                "date_cession": "2026-06-01",
                "acquereur": "M. Durand",
                "frais_cession": 0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["plus_value_brute"] is None

    def test_ceder_bien_not_found(self, client, auth_headers):
        """Cannot sell a non-existent bien."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/biens/00000000-0000-0000-0000-999999999999/ceder",
            json={
                "prix_cession": 350000,
                "date_cession": "2026-06-01",
                "acquereur": "M. Durand",
                "frais_cession": 0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# TASK 6: Auto-update parts after mouvement de parts
# ──────────────────────────────────────────────────────────────


class TestMouvementPartsRecalculation:
    """POST /api/v1/scis/{sci_id}/mouvements-parts — recalculate associe parts"""

    def test_mouvement_parts_updates_associe_nb_parts(self, client, auth_headers, fake_supabase):
        """Creating a mouvement de parts should update cedant/cessionnaire nb_parts."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/mouvements-parts",
            json={
                "date_mouvement": "2026-03-20",
                "type_mouvement": "cession",
                "cedant_nom": "Gérant Test",
                "cessionnaire_nom": "Associé Test",
                "nb_parts": 10,
                "prix_unitaire": 100,
                "prix_total": 1000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Verify cedant lost 10 parts
        cedant = next(a for a in fake_supabase.store["associes"] if a["id"] == ASSOC_GERANT_ID)
        assert cedant["nb_parts"] == 50
        assert cedant["part"] == 50.0

        # Verify cessionnaire gained 10 parts
        cessionnaire = next(a for a in fake_supabase.store["associes"] if a["id"] == ASSOC_OTHER_ID)
        assert cessionnaire["nb_parts"] == 50
        assert cessionnaire["part"] == 50.0

    def test_mouvement_parts_no_matching_associes(self, client, auth_headers):
        """Mouvement with non-matching names should still succeed (just no recalc)."""
        resp = client.post(
            f"/api/v1/scis/{SCI_ID}/mouvements-parts",
            json={
                "date_mouvement": "2026-03-20",
                "type_mouvement": "cession",
                "cedant_nom": "Inconnu Cedant",
                "cessionnaire_nom": "Inconnu Cessionnaire",
                "nb_parts": 10,
                "prix_unitaire": 100,
                "prix_total": 1000,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
