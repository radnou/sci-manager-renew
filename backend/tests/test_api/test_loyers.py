from datetime import date

def test_list_loyers_empty(client):
    r = client.get("/v1/loyers")
    assert r.status_code == 200
    assert r.json() == []


def test_create_loyer(client):
    payload = {"id_bien": "00000000-0000-0000-0000-000000000000", "date_loyer": str(date.today()), "montant": 1000}
    r = client.post("/v1/loyers", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["montant"] == 1000
    assert "id" in data
