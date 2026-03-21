"""Tests for lifecycle features:
1. Conge bail (notice to quit)
2. Modeles PV d'AG pre-remplis
3. Convocation AG
4. Simulation droits d'enregistrement cession parts
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# UUIDs for test SCIs
SCI_UUID = "00000000-0000-0000-0000-000000000001"
SCI2_UUID = "00000000-0000-0000-0000-000000000002"

BIEN_ID = "bien-lc-1"
BAIL_ID = "bail-lc-1"

AG_ID = "00000000-0000-0000-0000-0000000000a1"


@pytest.fixture(autouse=True)
def _seed_lifecycle_data(fake_supabase):
    """Seed store with SCI, associes, bien, and bail data for lifecycle tests."""
    fake_supabase.store["sci"].extend([
        {
            "id": SCI_UUID,
            "nom": "SCI Test Lifecycle",
            "siren": "111222333",
            "adresse_siege": "10 rue de la Paix, 75001 Paris",
            "nom_gerant": "Jean Dupont",
            "regime_fiscal": "IR",
            "capital_social": 10000,
        },
        {
            "id": SCI2_UUID,
            "nom": "SCI Test Lifecycle 2",
            "siren": "444555666",
            "adresse_siege": None,
            "nom_gerant": None,
            "regime_fiscal": "IS",
            "capital_social": None,
        },
    ])
    fake_supabase.store["associes"].extend([
        {"id": "assoc-lc-1", "id_sci": SCI_UUID, "user_id": "user-123", "nom": "Jean Dupont", "email": "jean@test.fr", "part": 60, "role": "gerant"},
        {"id": "assoc-lc-2", "id_sci": SCI_UUID, "user_id": "user-456", "nom": "Marie Martin", "email": "marie@test.fr", "part": 40, "role": "associe"},
        {"id": "assoc-lc-3", "id_sci": SCI2_UUID, "user_id": "user-123", "nom": "Jean Dupont", "email": "jean@test.fr", "part": 100, "role": "associe"},
    ])
    fake_supabase.store["biens"].extend([
        {"id": BIEN_ID, "id_sci": SCI_UUID, "adresse": "5 rue Test", "ville": "Paris", "code_postal": "75001", "type_locatif": "nu", "type_bien": "appartement"},
    ])
    fake_supabase.store["baux"].extend([
        {"id": BAIL_ID, "id_bien": BIEN_ID, "date_debut": "2025-01-01", "date_fin": "2027-12-31", "loyer_hc": 800.0, "charges_locatives": 100.0, "statut": "en_cours"},
    ])


# ──────────────────────────────────────────────────────────────
# TASK 1: Conge bail
# ──────────────────────────────────────────────────────────────


class TestCongeBail:
    BASE = f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/{BAIL_ID}/conge"

    def test_conge_locataire_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        response = client.post(
            self.BASE,
            json={
                "type_conge": "locataire",
                "date_notification": "2026-03-21",
                "motif": "Départ volontaire",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["type_conge"] == "locataire"
        assert body["motif_conge"] == "Départ volontaire"
        # date_conge should be ~3 months after notification for nu
        assert body["date_conge"] == "2026-06-20"

    def test_conge_bailleur_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        response = client.post(
            self.BASE,
            json={
                "type_conge": "bailleur",
                "date_notification": "2026-03-21",
                "motif": "Vente",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["type_conge"] == "bailleur"
        assert body["motif_conge"] == "Vente"
        # date_conge should be ~6 months after notification
        assert body["date_conge"] == "2026-09-20"

    def test_conge_with_explicit_date_effet(self, client: TestClient, auth_headers: dict):
        response = client.post(
            self.BASE,
            json={
                "type_conge": "locataire",
                "date_notification": "2026-03-21",
                "motif": "Départ volontaire",
                "date_effet": "2026-08-01",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["date_conge"] == "2026-08-01"

    def test_conge_invalid_type(self, client: TestClient, auth_headers: dict):
        response = client.post(
            self.BASE,
            json={
                "type_conge": "invalid",
                "date_notification": "2026-03-21",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_conge_invalid_motif_bailleur(self, client: TestClient, auth_headers: dict):
        response = client.post(
            self.BASE,
            json={
                "type_conge": "bailleur",
                "date_notification": "2026-03-21",
                "motif": "Je veux pas de locataire",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_conge_bail_already_has_conge(self, client: TestClient, auth_headers: dict, fake_supabase):
        # Set existing conge on the bail
        for bail in fake_supabase.store["baux"]:
            if bail["id"] == BAIL_ID:
                bail["date_conge"] = "2026-06-01"
                bail["type_conge"] = "locataire"
                break

        response = client.post(
            self.BASE,
            json={
                "type_conge": "locataire",
                "date_notification": "2026-03-21",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_conge_bail_termine(self, client: TestClient, auth_headers: dict, fake_supabase):
        for bail in fake_supabase.store["baux"]:
            if bail["id"] == BAIL_ID:
                bail["statut"] = "termine"
                break

        response = client.post(
            self.BASE,
            json={
                "type_conge": "locataire",
                "date_notification": "2026-03-21",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_conge_bail_not_found(self, client: TestClient, auth_headers: dict):
        url = f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/baux/nonexistent-bail/conge"
        response = client.post(
            url,
            json={
                "type_conge": "locataire",
                "date_notification": "2026-03-21",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_conge_requires_gerant(self, client: TestClient, auth_headers: dict):
        url = f"/api/v1/scis/{SCI2_UUID}/biens/{BIEN_ID}/baux/{BAIL_ID}/conge"
        response = client.post(
            url,
            json={
                "type_conge": "locataire",
                "date_notification": "2026-03-21",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────
# TASK 2: Modeles PV d'AG pre-remplis
# ──────────────────────────────────────────────────────────────


class TestModeleAG:
    BASE = f"/api/v1/scis/{SCI_UUID}/assemblees-generales/modele"

    def test_modele_ago_approbation_comptes(self, client: TestClient, auth_headers: dict, fake_supabase):
        # Seed fiscalite data
        fake_supabase.store.setdefault("fiscalite", []).append(
            {"id": "fisc-1", "id_sci": SCI_UUID, "annee": 2025, "resultat_fiscal": 15000.0}
        )
        response = client.get(f"{self.BASE}/ago_approbation_comptes", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["type_ag"] == "ordinaire"
        assert "2025" in body["ordre_du_jour"]
        assert "Jean Dupont" in body["resolutions_modele"]
        assert "15" in body["resolutions_modele"]  # resultat formatted
        assert body["quorum_requis"] == "Selon statuts (défaut: majorité des parts)"
        assert body["date_ag_suggeree"]  # non-empty date string

    def test_modele_age_modification_statuts(self, client: TestClient, auth_headers: dict):
        response = client.get(f"{self.BASE}/age_modification_statuts", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["type_ag"] == "extraordinaire"
        assert "Modification des statuts" in body["ordre_du_jour"]
        assert "Unanimité" in body["quorum_requis"]

    def test_modele_age_cession_parts(self, client: TestClient, auth_headers: dict):
        response = client.get(f"{self.BASE}/age_cession_parts", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["type_ag"] == "extraordinaire"
        assert "cession" in body["ordre_du_jour"].lower()

    def test_modele_invalid_type(self, client: TestClient, auth_headers: dict):
        response = client.get(f"{self.BASE}/invalid_type", headers=auth_headers)
        assert response.status_code == 400

    def test_modele_requires_auth(self, client: TestClient):
        response = client.get(f"{self.BASE}/ago_approbation_comptes")
        assert response.status_code in (401, 403)

    def test_modele_no_fiscalite_data(self, client: TestClient, auth_headers: dict):
        """When no fiscalite data exists, should still return a valid template."""
        response = client.get(f"{self.BASE}/ago_approbation_comptes", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["type_ag"] == "ordinaire"


# ──────────────────────────────────────────────────────────────
# TASK 3: Convocation AG
# ──────────────────────────────────────────────────────────────


class TestConvocationAG:
    def test_convocation_success(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store.setdefault("assemblees_generales", []).append({
            "id": AG_ID,
            "id_sci": SCI_UUID,
            "date_ag": "2026-06-15",
            "type_ag": "ordinaire",
            "exercice_annee": 2025,
            "ordre_du_jour": "1. Approbation des comptes\n2. Affectation du résultat",
            "quorum_atteint": False,
        })

        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{AG_ID}/convocation",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()

        # Check convocation text contains key elements
        texte = body["texte_convocation"]
        assert "SCI Test Lifecycle" in texte
        assert "10 rue de la Paix" in texte
        assert "2026-06-15" in texte
        assert "Ordinaire" in texte
        assert "Approbation des comptes" in texte
        assert "Jean Dupont" in texte

        # Check date_limite_envoi is 15 days before AG
        assert body["date_limite_envoi"] == "2026-05-31"
        assert body["date_ag"] == "2026-06-15"

        # Check associes list
        assert len(body["associes_destinataires"]) == 2

    def test_convocation_extraordinaire(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store.setdefault("assemblees_generales", []).append({
            "id": AG_ID,
            "id_sci": SCI_UUID,
            "date_ag": "2026-09-01",
            "type_ag": "extraordinaire",
            "exercice_annee": 2025,
            "ordre_du_jour": "Modification des statuts",
            "quorum_atteint": False,
        })

        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/{AG_ID}/convocation",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert "Extraordinaire" in body["texte_convocation"]

    def test_convocation_ag_not_found(self, client: TestClient, auth_headers: dict):
        response = client.post(
            f"/api/v1/scis/{SCI_UUID}/assemblees-generales/00000000-0000-0000-0000-000000000099/convocation",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_convocation_requires_gerant(self, client: TestClient, auth_headers: dict, fake_supabase):
        fake_supabase.store.setdefault("assemblees_generales", []).append({
            "id": AG_ID,
            "id_sci": SCI2_UUID,
            "date_ag": "2026-06-15",
            "type_ag": "ordinaire",
            "exercice_annee": 2025,
            "ordre_du_jour": "Test",
            "quorum_atteint": False,
        })

        response = client.post(
            f"/api/v1/scis/{SCI2_UUID}/assemblees-generales/{AG_ID}/convocation",
            headers=auth_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────
# TASK 4: Simulation droits d'enregistrement
# ──────────────────────────────────────────────────────────────


class TestSimulationDroitsEnregistrement:
    BASE = f"/api/v1/scis/{SCI_UUID}/mouvements-parts/simulation-droits"

    def test_simulation_basic(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"{self.BASE}?nb_parts=400&prix_unitaire=150",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prix_total"] == 60000.0
        assert body["droits_enregistrement"] == 3000.0
        assert body["taux"] == 5.0
        assert body["base_taxable"] == 60000.0
        assert "Art. 726 CGI" in body["reference_legale"]
        assert len(body["formalites"]) == 5
        assert "Acte de cession" in body["formalites"][0]

    def test_simulation_small_amount(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"{self.BASE}?nb_parts=1&prix_unitaire=100",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prix_total"] == 100.0
        assert body["droits_enregistrement"] == 5.0

    def test_simulation_zero_price(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"{self.BASE}?nb_parts=10&prix_unitaire=0",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prix_total"] == 0.0
        assert body["droits_enregistrement"] == 0.0

    def test_simulation_invalid_nb_parts(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"{self.BASE}?nb_parts=0&prix_unitaire=100",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_simulation_negative_price(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"{self.BASE}?nb_parts=10&prix_unitaire=-50",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_simulation_missing_params(self, client: TestClient, auth_headers: dict):
        response = client.get(self.BASE, headers=auth_headers)
        assert response.status_code == 422

    def test_simulation_requires_auth(self, client: TestClient):
        response = client.get(f"{self.BASE}?nb_parts=10&prix_unitaire=100")
        assert response.status_code in (401, 403)

    def test_simulation_large_values(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"{self.BASE}?nb_parts=10000&prix_unitaire=500",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prix_total"] == 5000000.0
        assert body["droits_enregistrement"] == 250000.0
