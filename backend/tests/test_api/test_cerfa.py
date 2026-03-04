def test_generate_cerfa_2044(client, auth_headers):
    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 7000.0,
    }

    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["formulaire"] == "cerfa_2044"
    assert data["resultat_fiscal"] == 17000.0
