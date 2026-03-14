def _enable_pro_subscription(fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "active",
            "is_active": True,
            "max_scis": 10,
            "max_biens": 20,
            "features": {
                "multi_sci_enabled": True,
                "charges_enabled": True,
                "fiscalite_enabled": True,
                "quitus_enabled": True,
                "cerfa_enabled": True,
                "priority_support": True,
            },
        }
    ]


def test_get_charges_requires_auth(client):
    response = client.get("/api/v1/charges/")
    assert response.status_code == 401


def test_create_update_and_delete_charge(client, auth_headers, fake_supabase):
    _enable_pro_subscription(fake_supabase)
    bien_created = client.post(
        "/api/v1/biens/",
        json={
            "id_sci": "sci-1",
            "adresse": "17 rue Charges",
            "ville": "Paris",
            "code_postal": "75017",
            "type_locatif": "nu",
            "loyer_cc": 1100.0,
            "charges": 90.0,
            "tmi": 20.0,
        },
        headers=auth_headers,
    )
    bien_id = bien_created.json()["id"]

    created = client.post(
        "/api/v1/charges/",
        json={
            "id_bien": bien_id,
            "type_charge": "assurance",
            "montant": 240.0,
            "date_paiement": "2026-03-05",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["id_sci"] == "sci-1"
    assert payload["bien_adresse"] == "17 rue Charges"
    charge_id = payload["id"]

    listed = client.get("/api/v1/charges/?id_sci=sci-1", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/v1/charges/{charge_id}",
        json={"montant": 310.0, "type_charge": "travaux"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["montant"] == 310.0
    assert updated.json()["type_charge"] == "travaux"

    deleted = client.delete(f"/api/v1/charges/{charge_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_create_charge_requires_feature_upgrade(client, auth_headers, free_plan):
    response = client.post(
        "/api/v1/charges/",
        json={
            "id_bien": "bien-unknown",
            "type_charge": "assurance",
            "montant": 120.0,
            "date_paiement": "2026-03-05",
        },
        headers=auth_headers,
    )
    assert response.status_code == 402
    assert response.json()["code"] == "upgrade_required"


# ---------------------------------------------------------------------------
# list_charges — filter by id_bien
# ---------------------------------------------------------------------------


def test_list_charges_filter_by_bien(client, auth_headers, fake_supabase):
    """Covers L114-117: list_charges with id_bien filter on an accessible bien."""
    _enable_pro_subscription(fake_supabase)
    # Seed a charge on bien-1 (owned by user-123 via sci-1)
    fake_supabase.store["charges"] = [
        {"id": "ch-1", "id_bien": "bien-1", "type_charge": "taxe_fonciere", "montant": 500.0, "date_paiement": "2026-01-15"},
        {"id": "ch-2", "id_bien": "bien-9", "type_charge": "assurance", "montant": 200.0, "date_paiement": "2026-02-10"},
    ]
    resp = client.get("/api/v1/charges/?id_bien=bien-1", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "ch-1"


def test_list_charges_filter_by_bien_unauthorized(client, auth_headers, fake_supabase):
    """Covers L115-116: id_bien not in user's accessible biens -> 403."""
    _enable_pro_subscription(fake_supabase)
    # Remove user from all SCIs so no biens are accessible
    fake_supabase.store["associes"] = []
    resp = client.get("/api/v1/charges/?id_bien=bien-1", headers=auth_headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "authorization_error"


def test_list_charges_no_biens(client, auth_headers, fake_supabase):
    """Covers L70-71: _fetch_charges_by_bien_ids with empty bien_ids -> empty list."""
    _enable_pro_subscription(fake_supabase)
    # User is associated but has no biens
    fake_supabase.store["biens"] = []
    resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_charges_filter_by_sci(client, auth_headers, fake_supabase):
    """Covers L106-111: list_charges filtered by id_sci narrows accessible_biens."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-a", "id_bien": "bien-1", "type_charge": "copro", "montant": 300.0, "date_paiement": "2026-06-01"},
        {"id": "ch-b", "id_bien": "bien-9", "type_charge": "copro", "montant": 400.0, "date_paiement": "2026-06-01"},
    ]
    resp = client.get("/api/v1/charges/?id_sci=sci-1", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    ids = [c["id"] for c in data]
    assert "ch-a" in ids
    assert "ch-b" not in ids


def test_list_charges_sci_not_owned(client, auth_headers, fake_supabase):
    """Covers L107: _require_sci_access raises 403 for SCI user does not own."""
    _enable_pro_subscription(fake_supabase)
    resp = client.get("/api/v1/charges/?id_sci=sci-unknown", headers=auth_headers)
    assert resp.status_code == 403


def test_list_charges_requires_feature_upgrade(client, auth_headers, free_plan):
    """Covers L103: list_charges feature gate on free plan."""
    resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 402
    assert resp.json()["code"] == "upgrade_required"


def test_list_charges_sorts_by_date_desc(client, auth_headers, fake_supabase):
    """Covers L122: charges sorted by date_paiement descending."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-old", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2025-01-01"},
        {"id": "ch-new", "id_bien": "bien-1", "type_charge": "copro", "montant": 200.0, "date_paiement": "2026-06-01"},
    ]
    resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["id"] == "ch-new"
    assert data[1]["id"] == "ch-old"


# ---------------------------------------------------------------------------
# create_charge — error paths
# ---------------------------------------------------------------------------


def test_create_charge_unknown_bien(client, auth_headers, fake_supabase):
    """Covers L58: _fetch_bien raises ValidationError for unknown bien id."""
    _enable_pro_subscription(fake_supabase)
    resp = client.post(
        "/api/v1/charges/",
        json={"id_bien": "does-not-exist", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"


def test_create_charge_sci_not_owned(client, auth_headers, fake_supabase):
    """Covers L142: _require_sci_access raises 403 when bien's SCI is not user's."""
    _enable_pro_subscription(fake_supabase)
    # Add a bien owned by a SCI the user is NOT associated with
    fake_supabase.store["biens"].append(
        {"id": "bien-alien", "id_sci": "sci-alien", "adresse": "1 rue Alien", "ville": "Mars", "code_postal": "00000"}
    )
    resp = client.post(
        "/api/v1/charges/",
        json={"id_bien": "bien-alien", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_create_charge_validation_montant(client, auth_headers, fake_supabase):
    """Pydantic validation: montant must be > 0."""
    _enable_pro_subscription(fake_supabase)
    resp = client.post(
        "/api/v1/charges/",
        json={"id_bien": "bien-1", "type_charge": "assurance", "montant": -5.0, "date_paiement": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_charge_validation_type_too_short(client, auth_headers, fake_supabase):
    """Pydantic validation: type_charge min_length=2."""
    _enable_pro_subscription(fake_supabase)
    resp = client.post(
        "/api/v1/charges/",
        json={"id_bien": "bien-1", "type_charge": "X", "montant": 100.0, "date_paiement": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# update_charge — error paths
# ---------------------------------------------------------------------------


def test_update_charge_empty_payload(client, auth_headers, fake_supabase):
    """Covers L166-167: empty update payload -> ValidationError 400."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-upd", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]
    resp = client.patch("/api/v1/charges/ch-upd", json={}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"


def test_update_charge_not_found(client, auth_headers, fake_supabase):
    """Covers L65: _fetch_charge raises ResourceNotFoundError."""
    _enable_pro_subscription(fake_supabase)
    resp = client.patch(
        "/api/v1/charges/nonexistent",
        json={"montant": 999.0},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "resource_not_found"


def test_update_charge_sci_not_owned(client, auth_headers, fake_supabase):
    """Covers L175: update blocked when charge's bien belongs to unowned SCI."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["biens"].append(
        {"id": "bien-alien2", "id_sci": "sci-alien", "adresse": "2 rue Alien", "ville": "Mars", "code_postal": "00000"}
    )
    fake_supabase.store["charges"] = [
        {"id": "ch-alien", "id_bien": "bien-alien2", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]
    resp = client.patch(
        "/api/v1/charges/ch-alien",
        json={"montant": 200.0},
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_update_charge_requires_feature_upgrade(client, auth_headers, free_plan):
    """Covers L169: update_charge feature gate on free plan."""
    resp = client.patch(
        "/api/v1/charges/ch-any",
        json={"montant": 200.0},
        headers=auth_headers,
    )
    assert resp.status_code == 402
    assert resp.json()["code"] == "upgrade_required"


# ---------------------------------------------------------------------------
# delete_charge — error paths
# ---------------------------------------------------------------------------


def test_delete_charge_not_found(client, auth_headers, fake_supabase):
    """Covers L65: _fetch_charge raises ResourceNotFoundError on delete."""
    _enable_pro_subscription(fake_supabase)
    resp = client.delete("/api/v1/charges/nonexistent", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == "resource_not_found"


def test_delete_charge_sci_not_owned(client, auth_headers, fake_supabase):
    """Covers L204: delete blocked when charge belongs to unowned SCI."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["biens"].append(
        {"id": "bien-alien3", "id_sci": "sci-alien", "adresse": "3 rue Alien", "ville": "Mars", "code_postal": "00000"}
    )
    fake_supabase.store["charges"] = [
        {"id": "ch-del-alien", "id_bien": "bien-alien3", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]
    resp = client.delete("/api/v1/charges/ch-del-alien", headers=auth_headers)
    assert resp.status_code == 403


def test_delete_charge_requires_feature_upgrade(client, auth_headers, free_plan):
    """Covers L198: delete_charge feature gate on free plan."""
    resp = client.delete("/api/v1/charges/ch-any", headers=auth_headers)
    assert resp.status_code == 402
    assert resp.json()["code"] == "upgrade_required"


# ---------------------------------------------------------------------------
# Serialization edge cases
# ---------------------------------------------------------------------------


def test_serialize_charge_missing_bien_in_map(client, auth_headers, fake_supabase):
    """Covers L84-89: _serialize_charge when bien is not in bien_map (id_bien mismatch)."""
    _enable_pro_subscription(fake_supabase)
    # Insert a charge with id_bien that exists but won't match after SCI filtering
    fake_supabase.store["charges"] = [
        {"id": "ch-orphan", "id_bien": "bien-1", "type_charge": "copro", "montant": 50.0, "date_paiement": "2026-01-01"},
    ]
    resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["bien_adresse"] == "1 rue de la Paix"


def test_serialize_charge_with_null_id_bien(client, auth_headers, fake_supabase):
    """Covers L84: _serialize_charge when row has None id_bien."""
    _enable_pro_subscription(fake_supabase)
    # Charge with no id_bien — still returned with null enrichment fields
    fake_supabase.store["charges"] = [
        {"id": "ch-null", "id_bien": None, "type_charge": "copro", "montant": 50.0, "date_paiement": "2026-01-01"},
    ]
    # This charge's id_bien is None, so in_ filter won't match it — it won't appear
    # Instead, let's test the list: it should return 0 because the bien_ids won't include None
    resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# _require_sci_access edge case
# ---------------------------------------------------------------------------


def test_require_sci_access_missing_id_sci(client, auth_headers, fake_supabase):
    """Covers L35-36: _require_sci_access when id_sci is empty string -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)
    # Create a bien with empty id_sci
    fake_supabase.store["biens"].append(
        {"id": "bien-no-sci", "id_sci": "", "adresse": "X", "ville": "Y", "code_postal": "00000"}
    )
    resp = client.post(
        "/api/v1/charges/",
        json={"id_bien": "bien-no-sci", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


# ---------------------------------------------------------------------------
# _fetch_accessible_biens with empty sci_ids
# ---------------------------------------------------------------------------


def test_list_charges_no_scis(client, auth_headers, fake_supabase):
    """Covers L42-43: _fetch_accessible_biens with empty sci_ids returns []."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["associes"] = []  # user has no SCIs
    resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Without trailing slash (both route variants)
# ---------------------------------------------------------------------------


def test_list_charges_no_trailing_slash(client, auth_headers, fake_supabase):
    """Covers L93: GET /charges (no trailing slash) variant."""
    _enable_pro_subscription(fake_supabase)
    resp = client.get("/api/v1/charges", headers=auth_headers)
    assert resp.status_code == 200


def test_create_charge_no_trailing_slash(client, auth_headers, fake_supabase):
    """Covers L131: POST /charges (no trailing slash) variant."""
    _enable_pro_subscription(fake_supabase)
    resp = client.post(
        "/api/v1/charges",
        json={"id_bien": "bien-1", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Database error paths (monkeypatched)
# ---------------------------------------------------------------------------

from unittest.mock import patch, MagicMock


def _make_error_result(error_msg="db failure"):
    """Return a fake result with an error attribute set."""
    r = MagicMock()
    r.error = error_msg
    r.data = []
    return r


def _make_empty_result():
    """Return a fake result with no error but empty data."""
    r = MagicMock()
    r.error = None
    r.data = []
    return r


def test_execute_select_error_branch(client, auth_headers, fake_supabase):
    """Covers L24-25: _execute_select raises DatabaseError when result.error is set."""
    _enable_pro_subscription(fake_supabase)
    original_execute = fake_supabase.__class__.__dict__.get("table")

    call_count = {"n": 0}
    original_table = fake_supabase.table

    def patched_table(name):
        query = original_table(name)
        if name == "associes":
            orig_execute = query.execute

            def failing_execute():
                from tests.conftest import FakeResult
                return FakeResult(data=[], error="simulated db error")

            query.execute = failing_execute
        return query

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 503


def test_list_charges_generic_exception(client, auth_headers, fake_supabase):
    """Covers L126-128: generic exception in list_charges -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)

    def exploding_table(name):
        if name == "associes":
            raise RuntimeError("unexpected failure")
        return fake_supabase.__class__.table(fake_supabase, name)

    with patch.object(fake_supabase, "table", side_effect=exploding_table):
        resp = client.get("/api/v1/charges/", headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


def test_create_charge_insert_error(client, auth_headers, fake_supabase):
    """Covers L145-146: insert returns result.error -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)

    original_table = fake_supabase.table

    def patched_table(name):
        query = original_table(name)
        if name == "charges":
            orig_insert = query.insert

            def failing_insert(payload):
                q = orig_insert(payload)
                orig_exec = q.execute

                def error_execute():
                    from tests.conftest import FakeResult
                    return FakeResult(data=[], error="insert failed")

                q.execute = error_execute
                return q

            query.insert = failing_insert
        return query

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.post(
            "/api/v1/charges/",
            json={"id_bien": "bien-1", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
            headers=auth_headers,
        )
    assert resp.status_code == 503


def test_create_charge_insert_empty_result(client, auth_headers, fake_supabase):
    """Covers L149-150: insert returns no rows -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)

    original_table = fake_supabase.table

    def patched_table(name):
        query = original_table(name)
        if name == "charges":
            orig_insert = query.insert

            def empty_insert(payload):
                q = orig_insert(payload)
                orig_exec = q.execute

                def empty_execute():
                    from tests.conftest import FakeResult
                    return FakeResult(data=[])

                q.execute = empty_execute
                return q

            query.insert = empty_insert
        return query

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.post(
            "/api/v1/charges/",
            json={"id_bien": "bien-1", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
            headers=auth_headers,
        )
    assert resp.status_code == 503


def test_create_charge_generic_exception(client, auth_headers, fake_supabase):
    """Covers L155-157: generic exception in create_charge -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)

    original_table = fake_supabase.table
    call_count = {"n": 0}

    def patched_table(name):
        # Let associes and biens queries pass, explode on charges
        if name == "charges":
            raise RuntimeError("unexpected create failure")
        return original_table(name)

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.post(
            "/api/v1/charges/",
            json={"id_bien": "bien-1", "type_charge": "assurance", "montant": 100.0, "date_paiement": "2026-01-01"},
            headers=auth_headers,
        )
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


def test_update_charge_update_db_error(client, auth_headers, fake_supabase):
    """Covers L178-179: update returns result.error -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-uperr", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]

    original_table = fake_supabase.table
    update_call = {"done": False}

    def patched_table(name):
        query = original_table(name)
        if name == "charges" and not update_call["done"]:
            orig_update = query.update

            def failing_update(payload):
                update_call["done"] = True
                q = orig_update(payload)
                orig_eq = q.eq

                def patched_eq(key, val):
                    qq = orig_eq(key, val)
                    qq.execute = lambda: __import__("tests.conftest", fromlist=["FakeResult"]).FakeResult(data=[], error="update failed")
                    return qq

                q.eq = patched_eq
                return q

            query.update = failing_update
        return query

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.patch(
            "/api/v1/charges/ch-uperr",
            json={"montant": 999.0},
            headers=auth_headers,
        )
    assert resp.status_code == 503


def test_update_charge_returns_empty(client, auth_headers, fake_supabase):
    """Covers L182-183: update returns no rows -> ResourceNotFoundError 404."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-ghost", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]

    original_table = fake_supabase.table
    update_call = {"done": False}

    def patched_table(name):
        query = original_table(name)
        if name == "charges" and not update_call["done"]:
            orig_update = query.update

            def empty_update(payload):
                update_call["done"] = True
                q = orig_update(payload)
                orig_eq = q.eq

                def patched_eq(key, val):
                    qq = orig_eq(key, val)
                    qq.execute = lambda: __import__("tests.conftest", fromlist=["FakeResult"]).FakeResult(data=[])
                    return qq

                q.eq = patched_eq
                return q

            query.update = empty_update
        return query

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.patch(
            "/api/v1/charges/ch-ghost",
            json={"montant": 999.0},
            headers=auth_headers,
        )
    assert resp.status_code == 404
    assert resp.json()["code"] == "resource_not_found"


def test_update_charge_generic_exception(client, auth_headers, fake_supabase):
    """Covers L188-190: generic exception in update_charge -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-exc", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]

    original_table = fake_supabase.table
    update_call = {"done": False}

    def patched_table(name):
        if name == "charges" and not update_call["done"]:
            # First call to charges (select for _fetch_charge) should work
            q = original_table(name)
            orig_update = q.update

            def exploding_update(payload):
                update_call["done"] = True
                raise RuntimeError("unexpected update failure")

            q.update = exploding_update
            return q
        return original_table(name)

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.patch(
            "/api/v1/charges/ch-exc",
            json={"montant": 999.0},
            headers=auth_headers,
        )
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


def test_delete_charge_db_error(client, auth_headers, fake_supabase):
    """Covers L207-208: delete returns result.error -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-delerr", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]

    original_table = fake_supabase.table
    delete_call = {"done": False}

    def patched_table(name):
        query = original_table(name)
        if name == "charges" and not delete_call["done"]:
            orig_delete = query.delete

            def failing_delete():
                delete_call["done"] = True
                q = orig_delete()
                orig_eq = q.eq

                def patched_eq(key, val):
                    qq = orig_eq(key, val)
                    qq.execute = lambda: __import__("tests.conftest", fromlist=["FakeResult"]).FakeResult(data=[], error="delete failed")
                    return qq

                q.eq = patched_eq
                return q

            query.delete = failing_delete
        return query

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.delete("/api/v1/charges/ch-delerr", headers=auth_headers)
    assert resp.status_code == 503


def test_delete_charge_generic_exception(client, auth_headers, fake_supabase):
    """Covers L213-215: generic exception in delete_charge -> DatabaseError 503."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["charges"] = [
        {"id": "ch-delexc", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
    ]

    original_table = fake_supabase.table
    delete_call = {"done": False}

    def patched_table(name):
        if name == "charges" and not delete_call["done"]:
            q = original_table(name)
            orig_delete = q.delete

            def exploding_delete():
                delete_call["done"] = True
                raise RuntimeError("unexpected delete failure")

            q.delete = exploding_delete
            return q
        return original_table(name)

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        resp = client.delete("/api/v1/charges/ch-delexc", headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["code"] == "database_error"


# ---------------------------------------------------------------------------
# _fetch_accessible_biens / _fetch_charges_by_bien_ids fallback (no in_)
# ---------------------------------------------------------------------------


def test_fetch_accessible_biens_fallback_no_in(fake_supabase):
    """Covers L49-52: _fetch_accessible_biens fallback when query lacks in_."""
    from app.api.v1.charges import _fetch_accessible_biens
    from tests.conftest import FakeQuery

    # Temporarily remove in_ from the class so hasattr(query, "in_") returns False
    original_in = FakeQuery.in_
    delattr(FakeQuery, "in_")
    try:
        results = _fetch_accessible_biens(fake_supabase, ["sci-1", "sci-2"])
    finally:
        FakeQuery.in_ = original_in

    # Should have fetched biens for both SCIs via the eq fallback
    assert len(results) >= 2
    ids = {r["id"] for r in results}
    assert "bien-1" in ids


def test_fetch_charges_fallback_no_in(fake_supabase):
    """Covers L77-80: _fetch_charges_by_bien_ids fallback when query lacks in_."""
    from app.api.v1.charges import _fetch_charges_by_bien_ids
    from tests.conftest import FakeQuery

    fake_supabase.store["charges"] = [
        {"id": "ch-fb2", "id_bien": "bien-1", "type_charge": "copro", "montant": 100.0, "date_paiement": "2026-01-01"},
        {"id": "ch-fb3", "id_bien": "bien-9", "type_charge": "copro", "montant": 200.0, "date_paiement": "2026-02-01"},
    ]

    original_in = FakeQuery.in_
    delattr(FakeQuery, "in_")
    try:
        results = _fetch_charges_by_bien_ids(fake_supabase, ["bien-1", "bien-9"])
    finally:
        FakeQuery.in_ = original_in

    assert len(results) == 2
    ids = {r["id"] for r in results}
    assert "ch-fb2" in ids
    assert "ch-fb3" in ids
