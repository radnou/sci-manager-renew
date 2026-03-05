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
