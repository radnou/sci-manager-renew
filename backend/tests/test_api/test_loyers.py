from unittest.mock import patch, MagicMock


def _make_error_result(error_msg="db error"):
    """Create a fake result with an error attribute."""
    result = MagicMock()
    result.error = error_msg
    result.data = []
    return result


def test_get_loyers_requires_auth(client):
    response = client.get("/api/v1/loyers/")
    assert response.status_code == 401


def test_create_and_filter_loyers(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "10 rue Loyer",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1200.0,
        "charges": 100.0,
        "tmi": 30.0,
    }
    bien_created = client.post("/api/v1/biens/", json=bien_payload, headers=auth_headers)
    assert bien_created.status_code == 201
    bien_id = bien_created.json()["id"]

    payload_1 = {
        "id_bien": bien_id,
        "id_locataire": "loc-1",
        "date_loyer": "2026-01-01",
        "montant": 1200.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    payload_2 = {
        "id_bien": bien_id,
        "id_locataire": "loc-1",
        "date_loyer": "2026-03-01",
        "montant": 1200.0,
        "statut": "paye",
        "quitus_genere": True,
    }

    create_1 = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload_1, headers=auth_headers)
    create_2 = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload_2, headers=auth_headers)
    assert create_1.status_code == 201
    assert create_2.status_code == 201

    filtered = client.get(
        "/api/v1/loyers/?date_from=2026-02-01&date_to=2026-04-01",
        headers=auth_headers,
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["date_loyer"] == "2026-03-01"


def test_update_and_delete_loyer(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "11 rue Loyer",
        "ville": "Lyon",
        "code_postal": "69001",
        "type_locatif": "meuble",
        "loyer_cc": 950.0,
        "charges": 80.0,
        "tmi": 20.0,
    }
    bien_created = client.post("/api/v1/biens/", json=bien_payload, headers=auth_headers)
    assert bien_created.status_code == 201
    bien_id = bien_created.json()["id"]

    payload = {
        "id_bien": bien_id,
        "id_locataire": "loc-2",
        "date_loyer": "2026-02-01",
        "montant": 950.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    created = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload, headers=auth_headers)
    loyer_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/loyers/{loyer_id}",
        json={"statut": "paye", "quitus_genere": True},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["statut"] == "paye"

    deleted = client.delete(f"/api/v1/loyers/{loyer_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_list_loyers_rejects_invalid_date_range(client, auth_headers):
    response = client.get(
        "/api/v1/loyers/?date_from=2026-04-01&date_to=2026-02-01",
        headers=auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "date_from must be earlier than or equal to date_to"


def test_update_loyer_rejects_empty_payload(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "12 rue Loyer",
        "ville": "Marseille",
        "code_postal": "13001",
        "type_locatif": "nu",
        "loyer_cc": 900.0,
        "charges": 50.0,
        "tmi": 20.0,
    }
    bien_created = client.post("/api/v1/biens/", json=bien_payload, headers=auth_headers)
    assert bien_created.status_code == 201
    bien_id = bien_created.json()["id"]

    created = client.post(
        "/api/v1/loyers/?id_sci=sci-1",
        json={
            "id_bien": bien_id,
            "id_locataire": "loc-3",
            "date_loyer": "2026-05-01",
            "montant": 900.0,
            "statut": "en_attente",
            "quitus_genere": False,
        },
        headers=auth_headers,
    )
    assert created.status_code == 201

    response = client.patch(
        f"/api/v1/loyers/{created.json()['id']}",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "No update fields provided"


# ── Stats endpoint ──────────────────────────────────────────────────────


def test_loyer_stats_returns_monthly_aggregation(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/stats returns monthly aggregation with collection_rate."""
    # Seed loyers with id_sci so in_ filter works
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 1200.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-15", "montant": 800.0, "statut": "en_retard"},
        {"id": "l3", "id_bien": "bien-9", "id_sci": "sci-2", "date_loyer": "2026-04-01", "montant": 500.0, "statut": "en_attente"},
    ]
    resp = client.get("/api/v1/loyers/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    months = data["months"]
    assert len(months) == 2

    march = next(m for m in months if m["month"] == "2026-03")
    assert march["total"] == 2000.0
    assert march["paid"] == 1200.0
    assert march["late"] == 800.0
    assert march["pending"] == 0
    assert march["collection_rate"] == 60.0

    april = next(m for m in months if m["month"] == "2026-04")
    assert april["total"] == 500.0
    assert april["paid"] == 0
    assert april["pending"] == 500.0
    assert april["collection_rate"] == 0


def test_loyer_stats_requires_auth(client):
    resp = client.get("/api/v1/loyers/stats")
    assert resp.status_code == 401


def test_loyer_stats_empty_when_no_scis(client, auth_headers, fake_supabase):
    """User with no SCI associations gets empty months."""
    fake_supabase.store["associes"] = []
    resp = client.get("/api/v1/loyers/stats", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"months": []}


def test_loyer_stats_skips_rows_without_date(client, auth_headers, fake_supabase):
    """Loyer rows with empty date_loyer are skipped in stats."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-05-01", "montant": 200.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/stats", headers=auth_headers)
    assert resp.status_code == 200
    months = resp.json()["months"]
    assert len(months) == 1
    assert months[0]["month"] == "2026-05"
    assert months[0]["total"] == 200.0


def test_loyer_stats_with_months_limit(client, auth_headers, fake_supabase):
    """Stats respects the months query param to limit results."""
    fake_supabase.store["loyers"] = [
        {"id": f"l{i}", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": f"2026-{i:02d}-01", "montant": 100.0, "statut": "paye"}
        for i in range(1, 7)
    ]
    resp = client.get("/api/v1/loyers/stats?months=3", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["months"]) == 3


# ── List loyers with sci_id filter ──────────────────────────────────────


def test_list_loyers_filtered_by_sci_id(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/?id_sci=sci-1 returns only loyers for that SCI."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 1200.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-9", "id_sci": "sci-2", "date_loyer": "2026-04-01", "montant": 980.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/?id_sci=sci-1", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "l1"


def test_list_loyers_filtered_by_sci_id_with_date_range(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/?id_sci=sci-1&date_from=...&date_to=... applies date filters."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 200.0, "statut": "paye"},
        {"id": "l3", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-06-01", "montant": 300.0, "statut": "paye"},
    ]
    resp = client.get(
        "/api/v1/loyers/?id_sci=sci-1&date_from=2026-02-01&date_to=2026-04-01",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "l2"


def test_list_loyers_unauthorized_sci(client, auth_headers, fake_supabase):
    """Listing loyers for a SCI the user is not associated with returns 403."""
    resp = client.get("/api/v1/loyers/?id_sci=sci-unknown", headers=auth_headers)
    assert resp.status_code == 403


def test_list_loyers_all_scis_no_filter(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/ without id_sci returns loyers across all user SCIs."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-9", "id_sci": "sci-2", "date_loyer": "2026-04-01", "montant": 200.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_loyers_empty_when_no_scis(client, auth_headers, fake_supabase):
    """User with no SCIs gets empty list."""
    fake_supabase.store["associes"] = []
    resp = client.get("/api/v1/loyers/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── Create loyer ────────────────────────────────────────────────────────


def test_create_loyer_without_id_sci_resolves_from_bien(client, auth_headers, fake_supabase):
    """POST /api/v1/loyers/ without id_sci resolves SCI from the bien."""
    payload = {
        "id_bien": "bien-1",
        "id_locataire": "loc-1",
        "date_loyer": "2026-06-01",
        "montant": 999.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    resp = client.post("/api/v1/loyers/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id_sci"] == "sci-1"
    assert data["montant"] == 999.0


def test_create_loyer_mismatched_id_sci(client, auth_headers, fake_supabase):
    """POST with id_sci that doesn't match the bien's SCI returns 400."""
    payload = {
        "id_bien": "bien-1",  # belongs to sci-1
        "id_locataire": "loc-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    resp = client.post("/api/v1/loyers/?id_sci=sci-2", json=payload, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"
    assert "does not match" in resp.json()["error"]


def test_create_loyer_invalid_bien_id(client, auth_headers, fake_supabase):
    """POST with a non-existent bien_id returns 400 validation error."""
    payload = {
        "id_bien": "bien-nonexistent",
        "id_locataire": "loc-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    resp = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"
    assert "Unknown bien" in resp.json()["error"]


def test_create_loyer_unauthorized_sci(client, auth_headers, fake_supabase):
    """POST for a SCI the user has no access to returns 403."""
    # Add a bien belonging to an unknown SCI
    fake_supabase.store["biens"].append(
        {"id": "bien-unauth", "id_sci": "sci-foreign", "adresse": "1 rue X", "ville": "Paris", "code_postal": "75001"}
    )
    payload = {
        "id_bien": "bien-unauth",
        "id_locataire": "loc-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    resp = client.post("/api/v1/loyers/?id_sci=sci-foreign", json=payload, headers=auth_headers)
    assert resp.status_code == 403


def test_create_loyer_bien_without_sci(client, auth_headers, fake_supabase):
    """POST with a bien that has no id_sci and no id_sci param returns 400."""
    fake_supabase.store["biens"].append(
        {"id": "bien-nosci", "id_sci": None, "adresse": "1 rue Y", "ville": "Paris", "code_postal": "75001"}
    )
    payload = {
        "id_bien": "bien-nosci",
        "id_locataire": "loc-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    resp = client.post("/api/v1/loyers/", json=payload, headers=auth_headers)
    assert resp.status_code == 400
    assert "Unable to resolve SCI" in resp.json()["error"]


def test_create_loyer_requires_auth(client):
    payload = {
        "id_bien": "bien-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
    }
    resp = client.post("/api/v1/loyers/", json=payload)
    assert resp.status_code == 401


# ── Update loyer ────────────────────────────────────────────────────────


def test_update_loyer_montant_only(client, auth_headers, fake_supabase):
    """PATCH with only montant updates that field."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-upd", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 1200.0, "statut": "paye", "quitus_genere": False},
    ]
    resp = client.patch("/api/v1/loyers/loyer-upd", json={"montant": 1500.0}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["montant"] == 1500.0


def test_update_loyer_statut_only(client, auth_headers, fake_supabase):
    """PATCH with only statut updates that field."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-upd2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 1200.0, "statut": "en_attente", "quitus_genere": False},
    ]
    resp = client.patch("/api/v1/loyers/loyer-upd2", json={"statut": "en_retard"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["statut"] == "en_retard"


def test_update_loyer_not_found(client, auth_headers, fake_supabase):
    """PATCH on non-existent loyer returns 404."""
    resp = client.patch("/api/v1/loyers/loyer-ghost", json={"montant": 100.0}, headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == "resource_not_found"


def test_update_loyer_resolves_sci_from_bien(client, auth_headers, fake_supabase):
    """PATCH on a loyer without id_sci resolves SCI from the bien for access check."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-noscifield", "id_bien": "bien-1", "date_loyer": "2026-03-01", "montant": 500.0, "statut": "en_attente", "quitus_genere": False},
    ]
    resp = client.patch("/api/v1/loyers/loyer-noscifield", json={"montant": 600.0}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["montant"] == 600.0


def test_update_loyer_requires_auth(client):
    resp = client.patch("/api/v1/loyers/loyer-1", json={"montant": 100.0})
    assert resp.status_code == 401


def test_update_loyer_unauthorized_sci(client, auth_headers, fake_supabase):
    """PATCH on a loyer belonging to an inaccessible SCI returns 403."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-foreign", "id_bien": "bien-1", "id_sci": "sci-foreign", "date_loyer": "2026-03-01", "montant": 500.0, "statut": "en_attente"},
    ]
    resp = client.patch("/api/v1/loyers/loyer-foreign", json={"montant": 600.0}, headers=auth_headers)
    assert resp.status_code == 403


# ── Delete loyer ────────────────────────────────────────────────────────


def test_delete_loyer_success(client, auth_headers, fake_supabase):
    """DELETE returns 204 and removes the loyer."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-del", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 1200.0, "statut": "paye"},
    ]
    resp = client.delete("/api/v1/loyers/loyer-del", headers=auth_headers)
    assert resp.status_code == 204
    # Verify it's gone
    assert len(fake_supabase.store["loyers"]) == 0


def test_delete_loyer_not_found(client, auth_headers, fake_supabase):
    """DELETE on non-existent loyer returns 404."""
    resp = client.delete("/api/v1/loyers/loyer-ghost", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == "resource_not_found"


def test_delete_loyer_requires_auth(client):
    resp = client.delete("/api/v1/loyers/loyer-1")
    assert resp.status_code == 401


def test_delete_loyer_unauthorized_sci(client, auth_headers, fake_supabase):
    """DELETE on a loyer belonging to an inaccessible SCI returns 403."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-foreign-del", "id_bien": "bien-1", "id_sci": "sci-foreign", "date_loyer": "2026-03-01", "montant": 500.0, "statut": "en_attente"},
    ]
    resp = client.delete("/api/v1/loyers/loyer-foreign-del", headers=auth_headers)
    assert resp.status_code == 403


def test_delete_loyer_resolves_sci_from_bien(client, auth_headers, fake_supabase):
    """DELETE on a loyer without id_sci resolves SCI from the bien."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-noscifield-del", "id_bien": "bien-1", "date_loyer": "2026-03-01", "montant": 500.0, "statut": "en_attente"},
    ]
    resp = client.delete("/api/v1/loyers/loyer-noscifield-del", headers=auth_headers)
    assert resp.status_code == 204


# ── Edge cases & error paths ───────────────────────────────────────────


def test_list_loyers_date_from_only(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/?date_from=... without date_to works."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-06-01", "montant": 200.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/?date_from=2026-03-01", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "l2"


def test_list_loyers_date_to_only(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/?date_to=... without date_from works."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-06-01", "montant": 200.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/?date_to=2026-03-01", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "l1"


def test_list_loyers_sci_id_date_from_only(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/?id_sci=sci-1&date_from=... without date_to works."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-06-01", "montant": 200.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/?id_sci=sci-1&date_from=2026-03-01", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_loyers_sci_id_date_to_only(client, auth_headers, fake_supabase):
    """GET /api/v1/loyers/?id_sci=sci-1&date_to=... without date_from works."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-06-01", "montant": 200.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/?id_sci=sci-1&date_to=2026-03-01", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == "l1"


def test_stats_with_zero_montant_row(client, auth_headers, fake_supabase):
    """Stats handles rows where montant is 0 or None gracefully."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": None, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-15", "montant": 0, "statut": "en_attente"},
    ]
    resp = client.get("/api/v1/loyers/stats", headers=auth_headers)
    assert resp.status_code == 200
    months = resp.json()["months"]
    assert len(months) == 1
    assert months[0]["total"] == 0
    assert months[0]["collection_rate"] == 0


def test_stats_collection_rate_100_percent(client, auth_headers, fake_supabase):
    """Stats returns 100% collection_rate when all loyers are paid."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 1000.0, "statut": "paye"},
        {"id": "l2", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-15", "montant": 500.0, "statut": "paye"},
    ]
    resp = client.get("/api/v1/loyers/stats", headers=auth_headers)
    assert resp.status_code == 200
    months = resp.json()["months"]
    assert months[0]["collection_rate"] == 100.0


def test_create_loyer_with_matching_id_sci(client, auth_headers, fake_supabase):
    """POST /api/v1/loyers/?id_sci=sci-1 succeeds when id_sci matches bien's SCI."""
    payload = {
        "id_bien": "bien-1",
        "id_locataire": "loc-1",
        "date_loyer": "2026-07-01",
        "montant": 750.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    resp = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["id_sci"] == "sci-1"


# ── Error paths (monkeypatched) ────────────────────────────────────────


def test_list_loyers_db_error_on_associes(client, auth_headers, monkeypatch):
    """DB error when fetching user SCIs triggers DatabaseError in list."""
    from app.api.v1 import loyers as loyers_mod

    def _broken_get_service_client(request=None):
        class BrokenClient:
            def table(self, name):
                if name == "associes":
                    return type("Q", (), {
                        "select": lambda s, *a: s,
                        "eq": lambda s, *a: s,
                        "execute": lambda s: _make_error_result("connection lost"),
                    })()
                raise RuntimeError("unexpected table")
        return BrokenClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _broken_get_service_client)
    resp = client.get("/api/v1/loyers/", headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


def test_list_loyers_sci_id_db_error_on_query(client, auth_headers, monkeypatch):
    """DB error when querying loyers for a specific SCI triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    original_get_service_client = loyers_mod.get_supabase_user_client
    call_count = {"n": 0}

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    call_count["n"] += 1
                    if call_count["n"] >= 1:
                        return type("Q", (), {
                            "select": lambda s, *a: s,
                            "eq": lambda s, k, v: s,
                            "gte": lambda s, k, v: s,
                            "lte": lambda s, k, v: s,
                            "execute": lambda s: _make_error_result("query failed"),
                        })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.get("/api/v1/loyers/?id_sci=sci-1", headers=auth_headers)
    assert resp.status_code == 503


def test_list_loyers_generic_exception(client, auth_headers, monkeypatch):
    """Non-SCIManagerException in list_loyers is caught and wrapped as DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    def _exploding_validate(*args, **kwargs):
        raise RuntimeError("unexpected boom")

    monkeypatch.setattr(loyers_mod, "_validate_date_range", _exploding_validate)
    resp = client.get("/api/v1/loyers/", headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"
    assert "Unable to list loyers" in resp.json()["error"]


def test_create_loyer_generic_exception(client, auth_headers, monkeypatch):
    """Non-SCIManagerException in create_loyer is caught and wrapped."""
    from app.api.v1 import loyers as loyers_mod

    def _exploding_get_service_client(request=None):
        raise RuntimeError("unexpected create boom")

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _exploding_get_service_client)
    payload = {
        "id_bien": "bien-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
    }
    resp = client.post("/api/v1/loyers/", json=payload, headers=auth_headers)
    assert resp.status_code == 503
    assert "Unable to create loyer" in resp.json()["error"]


def test_update_loyer_generic_exception(client, auth_headers, monkeypatch, fake_supabase):
    """Non-SCIManagerException in update_loyer is caught and wrapped."""
    from app.api.v1 import loyers as loyers_mod

    fake_supabase.store["loyers"] = [
        {"id": "loyer-ex", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]

    original_get_service_client = loyers_mod.get_supabase_user_client

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                q = real_client.table(name)
                if name == "loyers":
                    def exploding_update(payload):
                        raise RuntimeError("unexpected update boom")
                    q.update = exploding_update
                return q
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.patch("/api/v1/loyers/loyer-ex", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 503
    assert "Unable to update loyer" in resp.json()["error"]


def test_delete_loyer_generic_exception(client, auth_headers, monkeypatch, fake_supabase):
    """Non-SCIManagerException in delete_loyer is caught and wrapped."""
    from app.api.v1 import loyers as loyers_mod

    fake_supabase.store["loyers"] = [
        {"id": "loyer-dex", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]

    original_get_service_client = loyers_mod.get_supabase_user_client

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                q = real_client.table(name)
                if name == "loyers":
                    def exploding_delete():
                        raise RuntimeError("unexpected delete boom")
                    q.delete = exploding_delete
                return q
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.delete("/api/v1/loyers/loyer-dex", headers=auth_headers)
    assert resp.status_code == 503
    assert "Unable to delete loyer" in resp.json()["error"]


def test_update_loyer_resolves_sci_missing_id_bien(client, auth_headers, fake_supabase):
    """Update a loyer that has neither id_sci nor id_bien triggers DatabaseError."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-orphan", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]
    resp = client.patch("/api/v1/loyers/loyer-orphan", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


def test_delete_loyer_resolves_sci_missing_id_bien(client, auth_headers, fake_supabase):
    """Delete a loyer that has neither id_sci nor id_bien triggers DatabaseError."""
    fake_supabase.store["loyers"] = [
        {"id": "loyer-orphan-del", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]
    resp = client.delete("/api/v1/loyers/loyer-orphan-del", headers=auth_headers)
    assert resp.status_code == 503


def test_update_loyer_bien_missing_id_sci(client, auth_headers, fake_supabase):
    """Update a loyer whose bien has no id_sci triggers DatabaseError."""
    fake_supabase.store["biens"].append(
        {"id": "bien-nosci2", "id_sci": None, "adresse": "X", "ville": "Y", "code_postal": "00000"}
    )
    fake_supabase.store["loyers"] = [
        {"id": "loyer-bnosci", "id_bien": "bien-nosci2", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]
    resp = client.patch("/api/v1/loyers/loyer-bnosci", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


def test_stats_db_error(client, auth_headers, monkeypatch):
    """DB error in stats query triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    original_get_service_client = loyers_mod.get_supabase_user_client

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    return type("Q", (), {
                        "select": lambda s, *a: s,
                        "in_": lambda s, k, v: s,
                        "order": lambda s, *a, **kw: s,
                        "execute": lambda s: _make_error_result("stats db error"),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.get("/api/v1/loyers/stats", headers=auth_headers)
    assert resp.status_code == 503


def test_fetch_bien_db_error(client, auth_headers, monkeypatch):
    """DB error when fetching bien during create triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    original_get_service_client = loyers_mod.get_supabase_user_client

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "biens":
                    return type("Q", (), {
                        "select": lambda s, *a: s,
                        "eq": lambda s, k, v: s,
                        "execute": lambda s: _make_error_result("biens db error"),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    payload = {
        "id_bien": "bien-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
    }
    resp = client.post("/api/v1/loyers/", json=payload, headers=auth_headers)
    assert resp.status_code == 503


def test_create_loyer_insert_db_error(client, auth_headers, monkeypatch):
    """DB error on insert during create triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    class InsertErrorClient:
        def table(self, name):
            return type("Q", (), {
                "insert": lambda s, payload: type("IQ", (), {
                    "execute": lambda s2: _make_error_result("insert failed"),
                })(),
            })()

    monkeypatch.setattr(loyers_mod, "_get_write_client", lambda: InsertErrorClient())
    payload = {
        "id_bien": "bien-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
    }
    resp = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload, headers=auth_headers)
    assert resp.status_code == 503


def test_create_loyer_insert_empty_result(client, auth_headers, monkeypatch):
    """Insert returning empty data during create triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    class InsertEmptyClient:
        def table(self, name):
            return type("Q", (), {
                "insert": lambda s, payload: type("IQ", (), {
                    "execute": lambda s2: MagicMock(error=None, data=[]),
                })(),
            })()

    monkeypatch.setattr(loyers_mod, "_get_write_client", lambda: InsertEmptyClient())
    payload = {
        "id_bien": "bien-1",
        "date_loyer": "2026-06-01",
        "montant": 500.0,
        "statut": "en_attente",
    }
    resp = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload, headers=auth_headers)
    assert resp.status_code == 503
    assert "Unable to create loyer" in resp.json()["error"]


def test_update_loyer_select_db_error(client, auth_headers, monkeypatch):
    """DB error when selecting existing loyer during update triggers error."""
    from app.api.v1 import loyers as loyers_mod

    original_get_service_client = loyers_mod.get_supabase_user_client

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    return type("Q", (), {
                        "select": lambda s, *a: s,
                        "eq": lambda s, k, v: s,
                        "execute": lambda s: _make_error_result("select failed"),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.patch("/api/v1/loyers/loyer-1", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 503


def test_update_loyer_update_db_error(client, auth_headers, monkeypatch, fake_supabase):
    """DB error on the update query itself triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    fake_supabase.store["loyers"] = [
        {"id": "loyer-ude", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]

    original_get_service_client = loyers_mod.get_supabase_user_client
    call_count = {"n": 0}

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    call_count["n"] += 1
                    if call_count["n"] == 1:
                        return real_client.table(name)
                    return type("Q", (), {
                        "update": lambda s, payload: type("UQ", (), {
                            "eq": lambda s2, k, v: s2,
                            "execute": lambda s2: _make_error_result("update failed"),
                        })(),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.patch("/api/v1/loyers/loyer-ude", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 503


def test_update_loyer_update_empty_result(client, auth_headers, monkeypatch, fake_supabase):
    """Update returning empty data triggers ResourceNotFoundError."""
    from app.api.v1 import loyers as loyers_mod

    fake_supabase.store["loyers"] = [
        {"id": "loyer-uempty", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]

    original_get_service_client = loyers_mod.get_supabase_user_client
    call_count = {"n": 0}

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    call_count["n"] += 1
                    if call_count["n"] == 1:
                        return real_client.table(name)
                    return type("Q", (), {
                        "update": lambda s, payload: type("UQ", (), {
                            "eq": lambda s2, k, v: s2,
                            "execute": lambda s2: MagicMock(error=None, data=[]),
                        })(),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.patch("/api/v1/loyers/loyer-uempty", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 404


def test_delete_loyer_select_db_error(client, auth_headers, monkeypatch):
    """DB error when selecting existing loyer during delete triggers error."""
    from app.api.v1 import loyers as loyers_mod

    def _patched_get_service_client(request=None):
        from tests.conftest import FakeSupabaseClient
        real_client = FakeSupabaseClient()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    return type("Q", (), {
                        "select": lambda s, *a: s,
                        "eq": lambda s, k, v: s,
                        "execute": lambda s: _make_error_result("select failed"),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.delete("/api/v1/loyers/loyer-1", headers=auth_headers)
    assert resp.status_code == 503


def test_delete_loyer_delete_db_error(client, auth_headers, monkeypatch, fake_supabase):
    """DB error on the delete query itself triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    fake_supabase.store["loyers"] = [
        {"id": "loyer-dde", "id_bien": "bien-1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]

    original_get_service_client = loyers_mod.get_supabase_user_client
    call_count = {"n": 0}

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    call_count["n"] += 1
                    if call_count["n"] == 1:
                        return real_client.table(name)
                    return type("Q", (), {
                        "delete": lambda s: type("DQ", (), {
                            "eq": lambda s2, k, v: s2,
                            "execute": lambda s2: _make_error_result("delete failed"),
                        })(),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.delete("/api/v1/loyers/loyer-dde", headers=auth_headers)
    assert resp.status_code == 503


def test_require_sci_access_empty_id_sci(client, auth_headers, fake_supabase):
    """_require_sci_access with empty id_sci raises DatabaseError (line 38)."""
    fake_supabase.store["biens"].append(
        {"id": "bien-emptysci", "id_sci": "", "adresse": "X", "ville": "Y", "code_postal": "00000"}
    )
    fake_supabase.store["loyers"] = [
        {"id": "loyer-emptysci", "id_bien": "bien-emptysci", "id_sci": "", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
    ]
    resp = client.patch("/api/v1/loyers/loyer-emptysci", json={"montant": 200.0}, headers=auth_headers)
    assert resp.status_code == 503


def test_select_by_sci_scope_db_error(client, auth_headers, monkeypatch, fake_supabase):
    """DB error in _select_by_sci_scope (line 56) triggers DatabaseError."""
    from app.api.v1 import loyers as loyers_mod

    original_get_service_client = loyers_mod.get_supabase_user_client

    def _patched_get_service_client(request=None):
        real_client = original_get_service_client()

        class WrappedClient:
            def table(self, name):
                if name == "loyers":
                    return type("Q", (), {
                        "select": lambda s, *a: s,
                        "in_": lambda s, k, v: s,
                        "gte": lambda s, k, v: s,
                        "lte": lambda s, k, v: s,
                        "execute": lambda s: _make_error_result("scope query error"),
                    })()
                return real_client.table(name)
        return WrappedClient()

    monkeypatch.setattr(loyers_mod, "get_supabase_user_client", _patched_get_service_client)
    resp = client.get("/api/v1/loyers/", headers=auth_headers)
    assert resp.status_code == 503


# ── Direct unit tests for internal helpers ─────────────────────────────


def test_require_sci_access_with_empty_id_sci():
    """_require_sci_access raises DatabaseError when id_sci is empty."""
    from app.api.v1.loyers import _require_sci_access
    from app.core.exceptions import DatabaseError
    import pytest
    with pytest.raises(DatabaseError, match="Missing id_sci"):
        _require_sci_access(["sci-1"], "")


def test_select_by_sci_scope_fallback_without_in_(fake_supabase):
    """_select_by_sci_scope uses eq-per-sci fallback when in_ not available."""
    from app.api.v1.loyers import _select_by_sci_scope

    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "date_loyer": "2026-03-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_sci": "sci-2", "date_loyer": "2026-04-01", "montant": 200.0, "statut": "paye"},
        {"id": "l3", "id_sci": "sci-3", "date_loyer": "2026-05-01", "montant": 300.0, "statut": "paye"},
    ]

    class NoInClient:
        """Client whose query object lacks in_ method to trigger fallback."""
        def __init__(self, store):
            self._store = store

        def table(self, name):
            from tests.conftest import FakeQuery
            q = FakeQuery(self._store, name)

            class NoInQuery:
                """Wraps FakeQuery but does not expose in_."""
                def __init__(self, inner):
                    self._inner = inner
                def select(self, *args, **kwargs):
                    self._inner.select(*args, **kwargs)
                    return self
                def eq(self, key, value):
                    self._inner.eq(key, value)
                    return self
                def gte(self, key, value):
                    self._inner.gte(key, value)
                    return self
                def lte(self, key, value):
                    self._inner.lte(key, value)
                    return self
                def execute(self):
                    return self._inner.execute()
            return NoInQuery(q)

    no_in_client = NoInClient(fake_supabase.store)
    rows = _select_by_sci_scope(no_in_client, ["sci-1", "sci-2"], None, None)
    assert len(rows) == 2
    ids = {r["id"] for r in rows}
    assert ids == {"l1", "l2"}


def test_select_by_sci_scope_fallback_with_dates(fake_supabase):
    """Fallback path applies date_from and date_to filters."""
    from app.api.v1.loyers import _select_by_sci_scope
    from datetime import date

    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 100.0, "statut": "paye"},
        {"id": "l2", "id_sci": "sci-1", "date_loyer": "2026-06-01", "montant": 200.0, "statut": "paye"},
    ]

    class NoInClient:
        def __init__(self, store):
            self._store = store
        def table(self, name):
            from tests.conftest import FakeQuery
            q = FakeQuery(self._store, name)
            class NoInQuery:
                def __init__(self, inner):
                    self._inner = inner
                def select(self, *args, **kwargs):
                    self._inner.select(*args, **kwargs)
                    return self
                def eq(self, key, value):
                    self._inner.eq(key, value)
                    return self
                def gte(self, key, value):
                    self._inner.gte(key, value)
                    return self
                def lte(self, key, value):
                    self._inner.lte(key, value)
                    return self
                def execute(self):
                    return self._inner.execute()
            return NoInQuery(q)

    no_in_client = NoInClient(fake_supabase.store)
    rows = _select_by_sci_scope(no_in_client, ["sci-1"], date(2026, 3, 1), date(2026, 12, 31))
    assert len(rows) == 1
    assert rows[0]["id"] == "l2"


def test_select_by_sci_scope_fallback_db_error(fake_supabase):
    """Fallback path raises DatabaseError on query error."""
    from app.api.v1.loyers import _select_by_sci_scope
    from app.core.exceptions import DatabaseError
    import pytest

    class ErrorClient:
        def table(self, name):
            class ErrQuery:
                def select(self, *a): return self
                def eq(self, k, v): return self
                def gte(self, k, v): return self
                def lte(self, k, v): return self
                def execute(self):
                    return _make_error_result("fallback error")
            return ErrQuery()

    with pytest.raises(DatabaseError):
        _select_by_sci_scope(ErrorClient(), ["sci-1"], None, None)
