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


def test_get_fiscalite_requires_auth(client):
    response = client.get("/api/v1/fiscalite/")
    assert response.status_code == 401


def test_create_update_and_delete_fiscalite(client, auth_headers, fake_supabase):
    _enable_pro_subscription(fake_supabase)

    created = client.post(
        "/api/v1/fiscalite/",
        json={
            "id_sci": "sci-1",
            "annee": 2025,
            "total_revenus": 36000,
            "total_charges": 7200,
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["resultat_fiscal"] == 28800
    assert payload["regime_fiscal"] == "IR"
    fiscalite_id = payload["id"]

    listed = client.get("/api/v1/fiscalite/?id_sci=sci-1", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/v1/fiscalite/{fiscalite_id}",
        json={"total_charges": 8200},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["resultat_fiscal"] == 27800

    deleted = client.delete(f"/api/v1/fiscalite/{fiscalite_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_list_fiscalite_requires_feature_upgrade(client, auth_headers, free_plan):
    response = client.get("/api/v1/fiscalite/?id_sci=sci-1", headers=auth_headers)
    assert response.status_code == 402
    assert response.json()["code"] == "upgrade_required"


# ── Additional coverage tests ─────────────────────────────────────────────


def test_list_fiscalite_all_scis(client, auth_headers, fake_supabase):
    """List fiscalite without id_sci filter returns all user SCIs."""
    _enable_pro_subscription(fake_supabase)
    # Seed fiscalite rows for both SCIs
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-1", "id_sci": "sci-1", "annee": 2025, "total_revenus": 10000, "total_charges": 2000, "resultat_fiscal": 8000},
        {"id": "fisc-2", "id_sci": "sci-2", "annee": 2024, "total_revenus": 5000, "total_charges": 1000, "resultat_fiscal": 4000},
    ]
    response = client.get("/api/v1/fiscalite/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Sorted by annee desc
    assert data[0]["annee"] == 2025
    assert data[1]["annee"] == 2024


def test_list_fiscalite_unauthorized_sci(client, auth_headers, fake_supabase):
    """Requesting fiscalite for an SCI the user doesn't belong to returns 403."""
    _enable_pro_subscription(fake_supabase)
    response = client.get("/api/v1/fiscalite/?id_sci=sci-unknown", headers=auth_headers)
    assert response.status_code == 403


def test_create_fiscalite_unauthorized_sci(client, auth_headers, fake_supabase):
    """Creating fiscalite on an SCI the user doesn't own returns 403."""
    _enable_pro_subscription(fake_supabase)
    response = client.post(
        "/api/v1/fiscalite/",
        json={"id_sci": "sci-unknown", "annee": 2025, "total_revenus": 100, "total_charges": 50},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_create_fiscalite_requires_feature_upgrade(client, auth_headers, free_plan):
    """Creating fiscalite on free plan returns 402."""
    response = client.post(
        "/api/v1/fiscalite/",
        json={"id_sci": "sci-1", "annee": 2025, "total_revenus": 100, "total_charges": 50},
        headers=auth_headers,
    )
    assert response.status_code == 402


def test_update_fiscalite_not_found(client, auth_headers, fake_supabase):
    """Updating a non-existent fiscalite returns 404."""
    _enable_pro_subscription(fake_supabase)
    response = client.patch(
        "/api/v1/fiscalite/nonexistent",
        json={"total_revenus": 999},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_fiscalite_unauthorized_sci(client, auth_headers, fake_supabase):
    """Updating fiscalite belonging to another user's SCI returns 403."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-alien", "id_sci": "sci-alien", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]
    response = client.patch(
        "/api/v1/fiscalite/fisc-alien",
        json={"total_revenus": 2000},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_update_fiscalite_requires_feature_upgrade(client, auth_headers, free_plan, fake_supabase):
    """Updating fiscalite on free plan returns 402."""
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-1", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]
    response = client.patch(
        "/api/v1/fiscalite/fisc-1",
        json={"total_revenus": 2000},
        headers=auth_headers,
    )
    assert response.status_code == 402


def test_update_fiscalite_recalculates_resultat(client, auth_headers, fake_supabase):
    """Updating only total_revenus recalculates resultat_fiscal using existing total_charges."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-calc", "id_sci": "sci-1", "annee": 2025, "total_revenus": 10000, "total_charges": 3000, "resultat_fiscal": 7000},
    ]
    response = client.patch(
        "/api/v1/fiscalite/fisc-calc",
        json={"total_revenus": 15000},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["resultat_fiscal"] == 12000.0


def test_delete_fiscalite_not_found(client, auth_headers, fake_supabase):
    """Deleting a non-existent fiscalite returns 404."""
    _enable_pro_subscription(fake_supabase)
    response = client.delete("/api/v1/fiscalite/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_delete_fiscalite_unauthorized_sci(client, auth_headers, fake_supabase):
    """Deleting fiscalite belonging to another user's SCI returns 403."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-alien", "id_sci": "sci-alien", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]
    response = client.delete("/api/v1/fiscalite/fisc-alien", headers=auth_headers)
    assert response.status_code == 403


def test_delete_fiscalite_requires_feature_upgrade(client, auth_headers, free_plan, fake_supabase):
    """Deleting fiscalite on free plan returns 402."""
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-1", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]
    response = client.delete("/api/v1/fiscalite/fisc-1", headers=auth_headers)
    assert response.status_code == 402


def test_create_fiscalite_sci_not_found(client, auth_headers, fake_supabase):
    """Creating fiscalite for a SCI that exists in associes but not in sci table returns 404."""
    _enable_pro_subscription(fake_supabase)
    # Add association to a SCI that doesn't exist in the sci table
    fake_supabase.store["associes"].append(
        {"id": "associe-ghost", "id_sci": "sci-ghost", "user_id": "user-123", "nom": "Ghost", "email": "g@g.local", "part": 100, "role": "gerant"}
    )
    fake_supabase.store["sci"] = []  # Remove all SCIs from the table
    response = client.post(
        "/api/v1/fiscalite/",
        json={"id_sci": "sci-ghost", "annee": 2025, "total_revenus": 100, "total_charges": 50},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_list_fiscalite_serializes_without_sci_match(client, auth_headers, fake_supabase):
    """Fiscalite rows whose SCI is missing from sci table still serialize (regime_fiscal/nom_sci = None)."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-orphan", "id_sci": "sci-1", "annee": 2025, "total_revenus": 5000, "total_charges": 1000, "resultat_fiscal": 4000},
    ]
    # Remove SCIs so the sci_map is empty
    fake_supabase.store["sci"] = []
    response = client.get("/api/v1/fiscalite/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["regime_fiscal"] is None
    assert data[0]["nom_sci"] is None


def test_list_fiscalite_generic_exception(client, auth_headers, fake_supabase):
    """Cover lines 116-118: generic exception in list_fiscalite."""
    from unittest.mock import patch
    _enable_pro_subscription(fake_supabase)
    with patch("app.api.v1.fiscalite._get_user_sci_ids", side_effect=RuntimeError("boom")):
        response = client.get("/api/v1/fiscalite/", headers=auth_headers)
    assert response.status_code == 503


def test_create_fiscalite_insert_error(client, auth_headers, fake_supabase):
    """Cover line 139: insert returns error."""
    from unittest.mock import patch
    from tests.conftest import FakeResult
    _enable_pro_subscription(fake_supabase)

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "fiscalite":
            orig_insert = q.insert
            def insert_error(payload):
                result = orig_insert(payload)
                result.execute = lambda: FakeResult(data=[], error="insert failed")
                return result
            q.insert = insert_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.post(
            "/api/v1/fiscalite/",
            json={"id_sci": "sci-1", "annee": 2025, "total_revenus": 100, "total_charges": 50},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_create_fiscalite_empty_result(client, auth_headers, fake_supabase):
    """Cover line 143: insert returns no data."""
    from unittest.mock import patch
    from tests.conftest import FakeResult
    _enable_pro_subscription(fake_supabase)

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "fiscalite":
            orig_insert = q.insert
            def insert_empty(payload):
                result = orig_insert(payload)
                result.execute = lambda: FakeResult(data=[])
                return result
            q.insert = insert_empty
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.post(
            "/api/v1/fiscalite/",
            json={"id_sci": "sci-1", "annee": 2025, "total_revenus": 100, "total_charges": 50},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_create_fiscalite_generic_exception(client, auth_headers, fake_supabase):
    """Cover lines 148-150: generic exception in create_fiscalite."""
    from unittest.mock import patch
    _enable_pro_subscription(fake_supabase)
    with patch("app.api.v1.fiscalite._get_user_sci_ids", side_effect=RuntimeError("boom")):
        response = client.post(
            "/api/v1/fiscalite/",
            json={"id_sci": "sci-1", "annee": 2025, "total_revenus": 100, "total_charges": 50},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_fiscalite_update_error(client, auth_headers, fake_supabase):
    """Cover line 181: update query returns error."""
    from unittest.mock import patch
    from tests.conftest import FakeResult
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-err", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "fiscalite":
            orig_update = q.update
            def update_error(payload):
                result = orig_update(payload)
                class ErrorQuery:
                    def __init__(self, inner):
                        self._inner = inner
                    def eq(self, *a, **kw):
                        self._inner = self._inner.eq(*a, **kw)
                        return self
                    def execute(self):
                        return FakeResult(data=[], error="update failed")
                return ErrorQuery(result)
            q.update = update_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.patch(
            "/api/v1/fiscalite/fisc-err",
            json={"total_revenus": 2000},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_fiscalite_empty_result(client, auth_headers, fake_supabase):
    """Cover line 185: update returns no data -> ResourceNotFoundError."""
    from unittest.mock import patch
    from tests.conftest import FakeResult
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-empty", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "fiscalite":
            orig_update = q.update
            def update_empty(payload):
                result = orig_update(payload)
                class EmptyQuery:
                    def __init__(self, inner):
                        self._inner = inner
                    def eq(self, *a, **kw):
                        self._inner = self._inner.eq(*a, **kw)
                        return self
                    def execute(self):
                        return FakeResult(data=[])
                return EmptyQuery(result)
            q.update = update_empty
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.patch(
            "/api/v1/fiscalite/fisc-empty",
            json={"total_revenus": 2000},
            headers=auth_headers,
        )
    assert response.status_code == 404


def test_update_fiscalite_generic_exception(client, auth_headers, fake_supabase):
    """Cover lines 192-194: generic exception in update_fiscalite."""
    from unittest.mock import patch
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-gen", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]
    with patch("app.api.v1.fiscalite._fetch_fiscalite", side_effect=RuntimeError("boom")):
        response = client.patch(
            "/api/v1/fiscalite/fisc-gen",
            json={"total_revenus": 2000},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_delete_fiscalite_error_on_delete_query(client, auth_headers, fake_supabase):
    """Cover line 210: delete query returns error."""
    from unittest.mock import patch
    from tests.conftest import FakeResult
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-del-err", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "fiscalite":
            orig_delete = q.delete
            def delete_error():
                result = orig_delete()
                class ErrorQuery:
                    def __init__(self, inner):
                        self._inner = inner
                    def eq(self, *a, **kw):
                        self._inner = self._inner.eq(*a, **kw)
                        return self
                    def execute(self):
                        return FakeResult(data=[], error="delete failed")
                return ErrorQuery(result)
            q.delete = delete_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.delete("/api/v1/fiscalite/fisc-del-err", headers=auth_headers)
    assert response.status_code == 503


def test_delete_fiscalite_generic_exception(client, auth_headers, fake_supabase):
    """Cover lines 215-217: generic exception in delete_fiscalite."""
    from unittest.mock import patch
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-gen-del", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]
    with patch("app.api.v1.fiscalite._fetch_fiscalite", side_effect=RuntimeError("boom")):
        response = client.delete("/api/v1/fiscalite/fisc-gen-del", headers=auth_headers)
    assert response.status_code == 503


def test_execute_select_error():
    """Cover line 29: _execute_select raises DatabaseError when result.error is truthy."""
    from app.api.v1.fiscalite import _execute_select
    from tests.conftest import FakeResult
    import pytest as _pytest
    from app.core.exceptions import DatabaseError

    fake_result = FakeResult(data=[], error="db error")

    class FakeQuery:
        def execute(self):
            return fake_result

    with _pytest.raises(DatabaseError):
        _execute_select(FakeQuery())


def test_require_sci_access_missing_id_sci():
    """Cover line 40: _require_sci_access with empty id_sci raises DatabaseError."""
    from app.api.v1.fiscalite import _require_sci_access
    import pytest as _pytest
    from app.core.exceptions import DatabaseError

    with _pytest.raises(DatabaseError, match="Missing id_sci"):
        _require_sci_access(["sci-1"], "")


def test_fetch_scis_empty_list():
    """Cover line 47: _fetch_scis with empty list returns []."""
    from app.api.v1.fiscalite import _fetch_scis
    assert _fetch_scis(None, []) == []


def test_fetch_fiscalite_rows_empty_list():
    """Cover line 68: _fetch_fiscalite_rows with empty list returns []."""
    from app.api.v1.fiscalite import _fetch_fiscalite_rows
    assert _fetch_fiscalite_rows(None, []) == []


def test_fetch_scis_fallback_loop(client, auth_headers, fake_supabase):
    """Cover lines 53-56: _fetch_scis fallback when query lacks in_ method.

    Patches hasattr to return False for 'in_' on FakeQuery instances.
    """
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-fb-sci", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]

    import builtins
    original_hasattr = builtins.hasattr

    def patched_hasattr(obj, name):
        if name == "in_" and type(obj).__name__ == "FakeQuery":
            return False
        return original_hasattr(obj, name)

    from unittest.mock import patch
    with patch("builtins.hasattr", side_effect=patched_hasattr):
        response = client.get("/api/v1/fiscalite/", headers=auth_headers)
    assert response.status_code == 200


def test_fetch_fiscalite_rows_fallback_loop(client, auth_headers, fake_supabase):
    """Cover lines 74-77: _fetch_fiscalite_rows fallback when query lacks in_ method."""
    _enable_pro_subscription(fake_supabase)
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-fb", "id_sci": "sci-1", "annee": 2025, "total_revenus": 1000, "total_charges": 200, "resultat_fiscal": 800},
    ]

    import builtins
    original_hasattr = builtins.hasattr

    def patched_hasattr(obj, name):
        if name == "in_" and type(obj).__name__ == "FakeQuery":
            return False
        return original_hasattr(obj, name)

    from unittest.mock import patch
    with patch("builtins.hasattr", side_effect=patched_hasattr):
        response = client.get("/api/v1/fiscalite/?id_sci=sci-1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
