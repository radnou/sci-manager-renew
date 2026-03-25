import jwt

from app.core.config import settings


def _auth_headers_for(user_id: str) -> dict[str, str]:
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated", "aud": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_generate_and_download_quitus(client, auth_headers):
    payload = {
        "id_loyer": "loyer-1",
        "id_bien": "bien-1",
        "nom_locataire": "Jean Dupont",
        "periode": "Mars 2026",
        "montant": 1200.0,
        "nom_sci": "SCI Mosa Belleville",
        "adresse_bien": "1 rue de la Paix",
        "ville_bien": "Paris",
    }

    generated = client.post("/api/v1/quitus/generate", json=payload, headers=auth_headers)
    assert generated.status_code == 200
    data = generated.json()
    assert data["filename"].startswith("quitus-")
    assert "sci-1" in data["filename"]
    assert data["size_bytes"] > 0

    downloaded = client.get(data["pdf_url"], headers=auth_headers)
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/pdf"
    assert downloaded.content.startswith(b"%PDF")


def test_render_quitus_returns_inline_pdf(client, auth_headers):
    payload = {
        "id_loyer": "loyer-2",
        "id_bien": "bien-9",
        "nom_locataire": "Alice Martin",
        "periode": "Avril 2026",
        "montant": 980.0,
        "nom_sci": "SCI Horizon Lyon",
        "adresse_bien": "42 avenue QA",
        "ville_bien": "Lyon",
    }

    response = client.post("/api/v1/quitus/render", json=payload, headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert 'inline; filename="quittance-avril-2026.pdf"' in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"%PDF")


def test_render_quitus_disabled(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "feature_pdf_render_direct", False)

    payload = {
        "id_loyer": "loyer-2",
        "id_bien": "bien-9",
        "nom_locataire": "Alice Martin",
        "periode": "Avril 2026",
        "montant": 980.0,
    }

    response = client.post("/api/v1/quitus/render", json=payload, headers=auth_headers)

    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "feature_disabled"
    assert data["details"]["flag"] == "feature_pdf_render_direct"


def test_download_quitus_missing_file_returns_structured_404(client, auth_headers, monkeypatch):
    from app.api.v1 import quitus

    async def fake_download_file(_path: str):
        raise RuntimeError("File not found")

    monkeypatch.setattr(quitus.storage_service, "download_file", fake_download_file)

    response = client.get(
        "/api/v1/quitus/files/quitus-1234567890abcdef1234567890abcdef.pdf",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "resource_not_found"
    assert data["error"] == "Quittance introuvable."


def test_download_quitus_blocks_non_member_before_storage_access(client, monkeypatch, fake_supabase):
    from app.api.v1 import quitus

    # Give user-456 an active subscription so they pass the paywall
    fake_supabase.store["subscriptions"].append({
        "user_id": "user-456",
        "plan_key": "starter",
        "status": "active",
        "is_active": True,
        "max_scis": 1,
        "max_biens": 5,
        "features": {"quitus_enabled": True},
    })

    called = {"value": False}

    async def fake_download_file(_path: str):
        called["value"] = True
        return b"%PDF-1.4 fake"

    monkeypatch.setattr(quitus.storage_service, "download_file", fake_download_file)

    response = client.get(
        "/api/v1/quitus/files/quitus-sci-2-1234567890abcdef1234567890abcdef.pdf",
        headers=_auth_headers_for("user-456"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Accès non autorisé à cette quittance"
    assert called["value"] is False


def test_quitus_generate_allowed_for_free_plan(client, auth_headers):
    """Free users CAN generate quitus (quitus_enabled=True for all plans)."""
    payload = {
        "id_loyer": "loyer-free",
        "id_bien": "bien-free",
        "nom_locataire": "Marie Libre",
        "periode": "Janvier 2026",
        "montant": 800.0,
        "nom_sci": "SCI Test Free",
        "adresse_bien": "5 rue Gratuite",
        "ville_bien": "Lyon",
    }

    response = client.post("/api/v1/quitus/generate", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"].startswith("quitus-")
    assert data["size_bytes"] > 0
