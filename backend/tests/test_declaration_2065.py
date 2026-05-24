"""
Tests pour l'API déclaration 2065.

Couvre :
- POST /scis/{sci_id}/declaration-2065/generate
- GET /scis/{sci_id}/declaration-2065/{exercice}
- GET /scis/{sci_id}/declaration-2065/{exercice}/pdf
"""

import pytest
from fastapi.testclient import TestClient

SCI_UUID = "11111111-1111-1111-1111-111111111111"
BASE = f"/api/v1/scis/{SCI_UUID}/declaration-2065"


class TestGenerateDeclaration2065:
    """Tests pour POST /generate."""

    def test_generate_2065_success(self, client, fake_supabase, auth_headers):
        """✅ Génération réussie d'une déclaration 2065."""
        # Arrange
        fake_supabase.store.setdefault("credits_immobiliers", [])
        fake_supabase.store["sci"].append({
            "id": SCI_UUID,
            "nom": "SCI Test 2065",
            "capital_social": 10000,
            "date_cloture_exercice": "2025-12-31",
            "siren": "123456789",
            "regime_fiscal": "IS",
        })
        fake_supabase.store["associes"].append({
            "id": "associe-test",
            "id_sci": SCI_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
            "is_demo": False,
        })
        fake_supabase.store["biens"].append({
            "id": "bien-test",
            "id_sci": SCI_UUID,
            "adresse": "10 Rue du Test",
            "ville": "Paris",
            "code_postal": "75001",
            "prix_acquisition": 250000,
            "frais_notaire": 15000,
            "frais_agence_acquisition": 0,
            "type_bien": "appartement",
            "surface_m2": 50,
            "nb_pieces": 2,
            "loyer_cc": 1200,
            "statut": "loue",
            "tmi": 30,
            "is_demo": False,
        })
        fake_supabase.store["credits_immobiliers"].append({
            "id": "cred-1",
            "id_bien": "bien-test",
            "montant_emprunte": 100000,
            "taux_nominal": 2.5,
            "duree_mois": 240,
            "date_debut": "2020-01-01",
            "mensualite": 500,
            "capital_restant_du": 60000,
        })
        fake_supabase.store["fiscalite"].append({
            "id": "fisc-1",
            "id_sci": SCI_UUID,
            "annee": 2025,
            "resultat_fiscal": 1200,
        })

        payload = {
            "exercice": 2025,
            "tresorerie": 5000,
            "reserves": 198800,
        }

        # Act
        response = client.post(f"{BASE}/generate", json=payload, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sci_id"] == SCI_UUID
        assert data["exercice"] == 2025
        assert data["ecart"] == 0.0
        assert "actif" in data
        assert "passif" in data

    def test_generate_2065_invalid_year(self, client, fake_supabase, auth_headers):
        """❌ Année invalide (trop ancienne)."""
        # Seed the associate membership to pass the middleware auth check first
        fake_supabase.store["associes"].append({
            "id": "associe-test",
            "id_sci": SCI_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
            "is_demo": False,
        })
        payload = {"exercice": 1999}
        response = client.post(f"{BASE}/generate", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_generate_2065_missing_exercice(self, client, fake_supabase, auth_headers):
        """❌ Champ exercice manquant."""
        # Seed the associate membership to pass the middleware auth check first
        fake_supabase.store["associes"].append({
            "id": "associe-test",
            "id_sci": SCI_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
            "is_demo": False,
        })
        payload = {"tresorerie": 5000}
        response = client.post(f"{BASE}/generate", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestGetDeclaration2065:
    """Tests pour GET /{exercice}."""

    def test_get_2065_success(self, client, fake_supabase, auth_headers):
        """✅ Récupération d'une déclaration existante."""
        fake_supabase.store.setdefault("declarations_2065", [])
        fake_supabase.store["associes"].append({
            "id": "associe-test",
            "id_sci": SCI_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
            "is_demo": False,
        })
        fake_supabase.store["declarations_2065"].append({
            "id_sci": SCI_UUID,
            "exercice": 2025,
            "date_cloture": "2025-12-31",
            "actif_immobilisations": 250000,
            "actif_creances": 1600,
            "actif_tresorerie": 5000,
            "passif_capital": 10000,
            "passif_resultat": 1200,
            "passif_emprunts": 60000,
            "ecart": 0,
        })

        response = client.get(f"{BASE}/2025", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["exercice"] == 2025
        assert data["ecart"] == 0

    def test_get_2065_not_found(self, client, auth_headers):
        """❌ Déclaration non trouvée (ou SCI non trouvée/non accessible)."""
        # Ne pas ajouter de ligne dans associes pour SCI_UUID, ce qui causera une erreur 404 SCI non trouvée
        response = client.get(f"{BASE}/2020", headers=auth_headers)
        assert response.status_code == 404

    def test_get_2065_invalid_year(self, client, fake_supabase, auth_headers):
        """❌ Format d'année invalide."""
        # Seed the associate membership to pass the middleware auth check first
        fake_supabase.store["associes"].append({
            "id": "associe-test",
            "id_sci": SCI_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
            "is_demo": False,
        })
        response = client.get(f"{BASE}/not-a-year", headers=auth_headers)
        assert response.status_code == 422


class TestGetDeclaration2065PDF:
    """Tests pour GET /{exercice}/pdf."""

    def test_get_pdf_success(self, client, fake_supabase, auth_headers):
        """✅ PDF généré avec succès."""
        fake_supabase.store["sci"].append({
            "id": SCI_UUID,
            "nom": "SCI Test 2065",
            "capital_social": 10000,
            "date_cloture_exercice": "2025-12-31",
            "siren": "123456789",
            "regime_fiscal": "IS",
        })
        fake_supabase.store["associes"].append({
            "id": "associe-test",
            "id_sci": SCI_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
            "is_demo": False,
        })
        fake_supabase.store["biens"].append({
            "id": "bien-test",
            "id_sci": SCI_UUID,
            "adresse": "10 Rue du Test",
            "ville": "Paris",
            "code_postal": "75001",
            "prix_acquisition": 250000,
            "frais_notaire": 15000,
            "frais_agence_acquisition": 0,
            "type_bien": "appartement",
            "surface_m2": 50,
            "nb_pieces": 2,
            "loyer_cc": 1200,
            "statut": "loue",
            "tmi": 30,
            "is_demo": False,
        })

        response = client.get(f"{BASE}/2025/pdf", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "declaration_2065_2025" in response.headers["content-disposition"]

    def test_get_pdf_not_found(self, client, auth_headers):
        """❌ Déclaration non trouvée pour PDF (ou SCI non trouvée)."""
        # Ne pas associer pour avoir 404
        response = client.get(f"{BASE}/2020/pdf", headers=auth_headers)
        assert response.status_code == 404
