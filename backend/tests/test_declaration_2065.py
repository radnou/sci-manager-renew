"""
Tests pour l'API déclaration 2065.

Couvre :
- POST /scis/{sci_id}/declaration-2065/generate
- GET /scis/{sci_id}/declaration-2065/{exercice}
- GET /scis/{sci_id}/declaration-2065/{exercice}/pdf
"""

import pytest
from uuid import UUID

SCI_UUID = "11111111-1111-1111-1111-111111111111"
BASE = f"/api/v1/scis/{SCI_UUID}/declaration-2065"


class TestGenerateDeclaration2065:
    """Tests pour POST /generate."""

    def test_generate_2065_success(self, client, fake_supabase, auth_headers):
        """✅ Génération réussie d'une déclaration 2065."""
        # Arrange
        fake_supabase.store["sci"] = [
            {
                "id": SCI_UUID,
                "nom": "SCI Mosa Belleville",
                "siren": "123456789",
                "regime_fiscal": "IR",
                "adresse_siege": "12 rue de Belleville, 75020 Paris",
                "capital_social": 10000,
                "nom_gerant": "Test User",
                "date_cloture_exercice": "2025-12-31"
            }
        ]
        fake_supabase.store["associes"] = [
            {
                "id": "associe-1",
                "id_sci": SCI_UUID,
                "user_id": "user-123",
                "nom": "Test User",
                "email": "test.user@sci.local",
                "part": 100,
                "role": "gerant",
                "is_demo": False,
            }
        ]
        fake_supabase.store["biens"] = [
            {
                "id": "bien-1",
                "id_sci": SCI_UUID,
                "adresse": "1 rue de la Paix",
                "ville": "Paris",
                "code_postal": "75001",
                "prix_acquisition": 250000,
                "frais_notaire": 10000,
                "frais_agence_acquisition": 5000,
                "is_demo": False,
            }
        ]
        fake_supabase.store["loyers"] = [
            {
                "id": "loyer-1",
                "id_bien": "bien-1",
                "id_sci": SCI_UUID,
                "date_loyer": "2025-06-01",
                "montant": 800.0,
                "statut": "impayé",
            }
        ]
        fake_supabase.store["credits_immobiliers"] = [
            {
                "id": "cred-1",
                "id_bien": "bien-1",
                "montant_emprunte": 100000,
                "taux_nominal": 2.5,
                "duree_mois": 240,
                "date_debut": "2020-01-01",
                "mensualite": 500,
                "capital_restant_du": 60000,
            }
        ]
        fake_supabase.store["fiscalite"] = [
            {
                "id_sci": SCI_UUID,
                "annee": 2025,
                "resultat_fiscal": 1200.0,
            }
        ]

        payload = {
            "exercice": 2025,
            "tresorerie": 5000,
            "reserves": 2000,
        }

        # Act
        response = client.post(f"{BASE}/generate", json=payload, headers=auth_headers)

        # Assert
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["sci_id"] == SCI_UUID
        assert data["exercice"] == 2025
        assert "actif" in data
        assert "passif" in data

    def test_generate_2065_invalid_year(self, client, auth_headers):
        """❌ Année invalide (trop ancienne)."""
        payload = {"exercice": 1999}
        response = client.post(f"{BASE}/generate", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_generate_2065_missing_exercice(self, client, auth_headers):
        """❌ Champ exercice manquant."""
        payload = {"tresorerie": 5000}
        response = client.post(f"{BASE}/generate", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestGetDeclaration2065:
    """Tests pour GET /{exercice}."""

    def test_get_2065_success(self, client, fake_supabase, auth_headers):
        """✅ Récupération d'une déclaration existante."""
        fake_supabase.store["sci"] = [
            {
                "id": SCI_UUID,
                "nom": "SCI Mosa Belleville",
                "siren": "123456789",
                "regime_fiscal": "IR",
                "adresse_siege": "12 rue de Belleville, 75020 Paris",
                "capital_social": 10000,
                "nom_gerant": "Test User",
                "date_cloture_exercice": "2025-12-31"
            }
        ]
        fake_supabase.store["associes"] = [
            {
                "id": "associe-1",
                "id_sci": SCI_UUID,
                "user_id": "user-123",
                "nom": "Test User",
                "email": "test.user@sci.local",
                "part": 100,
                "role": "gerant",
                "is_demo": False,
            }
        ]
        fake_supabase.store["declarations_2065"] = [{
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
        }]

        response = client.get(f"{BASE}/2025", headers=auth_headers)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["exercice"] == 2025
        assert data["ecart"] == 0

    def test_get_2065_not_found(self, client, auth_headers):
        """❌ Déclaration non trouvée due à une SCI inexistante."""
        non_existent_base = "/api/v1/scis/22222222-2222-2222-2222-222222222222/declaration-2065"
        response = client.get(f"{non_existent_base}/2020", headers=auth_headers)
        assert response.status_code == 404

    def test_get_2065_invalid_year(self, client, auth_headers):
        """❌ Format d'année invalide."""
        response = client.get(f"{BASE}/not-a-year", headers=auth_headers)
        assert response.status_code == 422


class TestGetDeclaration2065PDF:
    """Tests pour GET /{exercice}/pdf."""

    def test_get_pdf_success(self, client, fake_supabase, auth_headers):
        """✅ PDF généré avec succès."""
        fake_supabase.store["sci"] = [
            {
                "id": SCI_UUID,
                "nom": "SCI Mosa Belleville",
                "siren": "123456789",
                "regime_fiscal": "IR",
                "adresse_siege": "12 rue de Belleville, 75020 Paris",
                "capital_social": 10000,
                "nom_gerant": "Test User",
                "date_cloture_exercice": "2025-12-31"
            }
        ]
        fake_supabase.store["associes"] = [
            {
                "id": "associe-1",
                "id_sci": SCI_UUID,
                "user_id": "user-123",
                "nom": "Test User",
                "email": "test.user@sci.local",
                "part": 100,
                "role": "gerant",
                "is_demo": False,
            }
        ]
        fake_supabase.store["declarations_2065"] = [{
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
        }]

        response = client.get(f"{BASE}/2025/pdf", headers=auth_headers)

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        assert "declaration_2065_2025" in response.headers["content-disposition"]

    def test_get_pdf_not_found(self, client, auth_headers):
        """❌ Déclaration non trouvée pour PDF due à une SCI inexistante."""
        non_existent_base = "/api/v1/scis/22222222-2222-2222-2222-222222222222/declaration-2065"
        response = client.get(f"{non_existent_base}/2020/pdf", headers=auth_headers)
        assert response.status_code == 404
