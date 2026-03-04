def test_list_biens_empty(client):
    r = client.get("/v1/biens")
    assert r.status_code == 200
    assert r.json() == []


def test_create_bien(client):
    payload = {"id_sci": "00000000-0000-0000-0000-000000000000", "adresse": "123 rue"}
    r = client.post("/v1/biens", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["adresse"] == "123 rue"
    assert "id" in data
