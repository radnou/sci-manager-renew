def test_generate_and_download_quitus(client, auth_headers):
    payload = {
        "id_loyer": "loyer-1",
        "id_bien": "bien-1",
        "nom_locataire": "Jean Dupont",
        "periode": "Mars 2026",
        "montant": 1200.0,
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
