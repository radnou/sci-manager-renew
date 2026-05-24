"""
Tests pour l'API déclaration 2065.

Couvre :
- POST /scis/{sci_id}/declaration-2065/generate
- GET /scis/{sci_id}/declaration-2065/{exercice}
- GET /scis/{sci_id}/declaration-2065/{exercice}/pdf (placeholder)
"""

import pytest
from fastapi.testclient import TestClient

SCI_UUID = "11111111-1111-1111-1111-111111111111"
BASE = f"/api/v1/scis/{SCI_UUID}/declaration-2065"

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


@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    
    tables = {}
    def get_table(name):
        if name not in tables:
            tables[name] = MagicMock()
        return tables[name]
    mock_client.table.side_effect = get_table

    import app.core.supabase_client as s_client
    monkeypatch.setattr(s_client, "_test_client", mock_client)
    monkeypatch.setattr("app.core.supabase_client.get_supabase_service_client", lambda: mock_client)
    monkeypatch.setattr("app.core.supabase_client.get_supabase_user_client", lambda request=None: mock_client)
    
    from app.main import app
    from app.core.paywall import require_sci_membership, AssocieMembership
    from app.core.security import get_current_user
    
    async def fake_membership(sci_id, user_id="user-123"):
        return AssocieMembership(
            user_id="user-123",
            sci_id=str(sci_id),
            role="gerant",
            associe_id="associe-1",
        )
        
    app.dependency_overrides[require_sci_membership] = fake_membership
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    
    yield mock_client
    
    app.dependency_overrides.pop(require_sci_membership, None)
    app.dependency_overrides.pop(get_current_user, None)


def mock_successful_declaration_data(mock_supabase):
    mock_supabase.table("sci").select().eq().execute.return_value = type("Result", (), {
        "data": [{"nom": "SCI Test", "capital_social": 10000, "date_cloture_exercice": "2025-12-31"}]
    })()
    mock_supabase.table("biens").select().eq().execute.return_value = type("Result", (), {
        "data": [{"id": "bien-1", "prix_acquisition": 250000, "frais_notaire": 15000, "frais_agence_acquisition": 0}]
    })()
    mock_supabase.table("loyers").select().eq().eq().gte().lte().execute.return_value = type("Result", (), {
        "data": [{"montant": 800}, {"montant": 800}]
    })()
    mock_supabase.table("credits_immobiliers").select().eq().execute.return_value = type("Result", (), {
        "data": [
            {"id": "cred-1", "montant_emprunte": 100000, "taux_nominal": 2.5, "duree_mois": 240, "date_debut": "2020-01-01", "mensualite": 500, "capital_restant_du": 258400}
        ]
    })()
    mock_supabase.table("fiscalite").select().eq().eq().execute.return_value = type("Result", (), {
        "data": [{"resultat_fiscal": 1200}]
    })()
    mock_supabase.table("declarations_2065").upsert().execute.return_value = type("Result", (), {
        "data": [{}],
        "error": None
    })()


def mock_successful_declaration_data(mock_supabase):
    mock_supabase.table("sci").select().eq().execute.return_value = type("Result", (), {
        "data": [{"nom": "SCI Test", "capital_social": 10000, "date_cloture_exercice": "2025-12-31"}]
    })()
    mock_supabase.table("biens").select().eq().execute.return_value = type("Result", (), {
        "data": [{"id": "bien-1", "prix_acquisition": 250000, "frais_notaire": 15000, "frais_agence_acquisition": 0}]
    })()
    mock_supabase.table("loyers").select().eq().eq().gte().lte().execute.return_value = type("Result", (), {
        "data": [{"montant": 800}, {"montant": 800}]
    })()
    mock_supabase.table("fiscalite").select().eq().eq().execute.return_value = type("Result", (), {
        "data": [{"resultat_fiscal": 1200}]
    })()
    mock_supabase.table("declarations_2065").upsert().execute.return_value = type("Result", (), {
        "data": [{}],
        "error": None
    })()


class TestGenerateDeclaration2065:
    """Tests pour POST /generate."""

    def test_generate_2065_success(self, client, mock_supabase):
        """✅ Génération réussie d'une déclaration 2065."""
        mock_successful_declaration_data(mock_supabase)
        mock_supabase.table("credits_immobiliers").select().in_().execute.return_value = type("Result", (), {
            "data": [
                {"id": "cred-1", "montant_emprunte": 100000, "taux_nominal": 2.5, "duree_mois": 240, "date_debut": "2020-01-01", "mensualite": 500, "capital_restant_du": 258400}
            ]
        })()

        payload = {
            "exercice": 2025,
            "tresorerie": 5000,
            "reserves": 2000,
        }

        # Act
        response = client.post(f"{BASE}/generate", json=payload, headers={"x-test-auth": "user-123"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sci_id"] == SCI_UUID
        assert data["exercice"] == 2025
        assert data["ecart"] == 0.0
        assert "actif" in data
        assert "passif" in data

    def test_generate_2065_invalid_year(self, client):
        """❌ Année invalide (trop ancienne)."""
        payload = {"exercice": 1999}
        response = client.post(f"{BASE}/generate", json=payload, headers={"x-test-auth": "user-123"})
        assert response.status_code == 422

    def test_generate_2065_missing_exercice(self, client):
        """❌ Champ exercice manquant."""
        payload = {"tresorerie": 5000}
        response = client.post(f"{BASE}/generate", json=payload, headers={"x-test-auth": "user-123"})
        assert response.status_code == 422


class TestGetDeclaration2065:
    """Tests pour GET /{exercice}."""

    def test_get_2065_success(self, client, mock_supabase):
        """✅ Récupération d'une déclaration existante."""
        mock_supabase.table("declarations_2065").select().eq().eq().execute.return_value = type("Result", (), {
            "data": [{
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
        })()

        response = client.get(f"{BASE}/2025", headers={"x-test-auth": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["exercice"] == 2025
        assert data["ecart"] == 0

    def test_get_2065_not_found(self, client, mock_supabase):
        """❌ Déclaration non trouvée."""
        mock_supabase.table("declarations_2065").select().eq().eq().execute.return_value = type("Result", (), {
            "data": []
        })()
        mock_supabase.table("sci").select().eq().execute.return_value = type("Result", (), {
            "data": []
        })()

        response = client.get(f"{BASE}/2020", headers={"x-test-auth": "user-123"})

        assert response.status_code == 404

    def test_get_2065_invalid_year(self, client):
        """❌ Format d'année invalide."""
        response = client.get(f"{BASE}/not-a-year", headers={"x-test-auth": "user-123"})
        assert response.status_code == 422


class TestGetDeclaration2065PDF:
    """Tests pour GET /{exercice}/pdf."""

    def test_get_pdf_success(self, client, mock_supabase):
        """✅ PDF généré avec succès."""
        mock_successful_declaration_data(mock_supabase)
        mock_supabase.table("credits_immobiliers").select().in_().execute.return_value = type("Result", (), {
            "data": [
                {"id": "cred-1", "montant_emprunte": 100000, "taux_nominal": 2.5, "duree_mois": 240, "date_debut": "2020-01-01", "mensualite": 500, "capital_restant_du": 255400}
            ]
        })()

        response = client.get(f"{BASE}/2025/pdf", headers={"x-test-auth": "user-123"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "declaration_2065_2025" in response.headers["content-disposition"]

    def test_get_pdf_not_found(self, client, mock_supabase):
        """❌ Déclaration non trouvée pour PDF."""
        mock_supabase.table("sci").select().eq().execute.return_value = type("Result", (), {
            "data": []
        })()

        response = client.get(f"{BASE}/2020/pdf", headers={"x-test-auth": "user-123"})
        assert response.status_code == 404
