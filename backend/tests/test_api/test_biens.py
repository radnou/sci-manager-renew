def test_get_biens_requires_auth(client):
    response = client.get("/api/v1/biens/")
    assert response.status_code == 401


def test_get_biens_returns_user_biens(client, auth_headers):
    response = client.get("/api/v1/biens/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_bien(client, auth_headers):
    payload = {
        "id_sci": "sci-1",
        "adresse": "10 rue Test",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1500.0,
        "charges": 200.0,
        "tmi": 30.0,
        "prix_acquisition": 300000.0,
    }
    response = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["adresse"] == "10 rue Test"
    assert data["rentabilite_brute"] == 6.0
    assert data["rentabilite_nette"] == 5.2


def test_update_and_delete_bien(client, auth_headers):
    payload = {
        "id_sci": "sci-1",
        "adresse": "11 rue Test",
        "ville": "Lyon",
        "code_postal": "69001",
        "type_locatif": "meuble",
        "loyer_cc": 1000.0,
        "charges": 100.0,
        "tmi": 20.0,
        "prix_acquisition": 200000.0,
    }
    created = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    bien_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/biens/{bien_id}",
        json={"ville": "Marseille", "charges": 150.0},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["ville"] == "Marseille"

    deleted = client.delete(f"/api/v1/biens/{bien_id}", headers=auth_headers)
    assert deleted.status_code == 204


# ── Additional coverage tests ─────────────────────────────────────────────


def test_list_biens_filtered_by_sci(client, auth_headers):
    """List biens with id_sci filter returns only biens for that SCI."""
    response = client.get("/api/v1/biens/?id_sci=sci-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(b["id_sci"] == "sci-1" for b in data)
    assert len(data) >= 1


def test_list_biens_unauthorized_sci(client, auth_headers):
    """Requesting biens for an SCI the user doesn't belong to returns 403."""
    response = client.get("/api/v1/biens/?id_sci=sci-unknown", headers=auth_headers)
    assert response.status_code == 403


def test_create_bien_unauthorized_sci(client, auth_headers):
    """Creating a bien on an SCI the user doesn't own returns 403."""
    payload = {
        "id_sci": "sci-unknown",
        "adresse": "10 rue Test",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1500.0,
        "charges": 200.0,
        "tmi": 30.0,
    }
    response = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    assert response.status_code == 403


def test_update_bien_not_found(client, auth_headers):
    """Updating a non-existent bien returns 404."""
    response = client.patch(
        "/api/v1/biens/nonexistent",
        json={"ville": "Marseille"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_bien_empty_payload(client, auth_headers):
    """Updating a bien with empty payload returns 503 (DatabaseError: no fields)."""
    response = client.patch(
        "/api/v1/biens/bien-1",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 503


def test_update_bien_unauthorized_sci(client, auth_headers, fake_supabase):
    """Updating a bien belonging to another user's SCI returns 403."""
    fake_supabase.store["biens"].append(
        {"id": "bien-alien", "id_sci": "sci-alien", "adresse": "1 rue Alien", "ville": "Mars", "code_postal": "00000", "type_bien": "studio", "surface_m2": 10, "nb_pieces": 1, "loyer_cc": 500, "statut": "loue", "tmi": 30}
    )
    response = client.patch(
        "/api/v1/biens/bien-alien",
        json={"ville": "Jupiter"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_update_bien_without_rentabilite_fields(client, auth_headers):
    """Updating a bien without loyer_cc/charges/prix_acquisition skips rentabilite recalc."""
    response = client.patch(
        "/api/v1/biens/bien-1",
        json={"ville": "Nice"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ville"] == "Nice"


def test_delete_bien_not_found(client, auth_headers):
    """Deleting a non-existent bien returns 404."""
    response = client.delete("/api/v1/biens/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_delete_bien_unauthorized_sci(client, auth_headers, fake_supabase):
    """Deleting a bien belonging to another user's SCI returns 403."""
    fake_supabase.store["biens"].append(
        {"id": "bien-alien2", "id_sci": "sci-alien", "adresse": "2 rue Alien", "ville": "Mars", "code_postal": "00000", "type_bien": "studio", "surface_m2": 10, "nb_pieces": 1, "loyer_cc": 500, "statut": "loue", "tmi": 30}
    )
    response = client.delete("/api/v1/biens/bien-alien2", headers=auth_headers)
    assert response.status_code == 403


def test_list_biens_no_associes(client, auth_headers, fake_supabase):
    """User with no associations returns empty list."""
    fake_supabase.store["associes"] = []
    response = client.get("/api/v1/biens/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_bien_with_missing_id_sci(client, auth_headers, fake_supabase):
    """Creating a bien with empty id_sci triggers _require_sci_access DatabaseError."""
    # Add an associe with empty id_sci to bypass the access check differently
    fake_supabase.store["associes"].append(
        {"id": "associe-empty", "id_sci": "", "user_id": "user-123", "nom": "Empty", "email": "e@e.local", "part": 100, "role": "gerant"}
    )
    payload = {
        "id_sci": "",
        "adresse": "10 rue Test",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1500.0,
    }
    response = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    # Empty id_sci triggers DatabaseError("Missing id_sci on scoped resource") -> 503
    assert response.status_code == 503


def test_list_biens_with_id_sci_error_on_query(client, auth_headers, fake_supabase):
    """Cover line 67: error when querying biens by id_sci."""
    from unittest.mock import patch, MagicMock
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_eq = q.eq

            def eq_with_error(key, value):
                result = orig_eq(key, value)
                if key == "id_sci":
                    orig_execute = result.execute
                    def execute_with_error():
                        return FakeResult(data=[], error="simulated DB error")
                    result.execute = execute_with_error
                return result
            q.eq = eq_with_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.get("/api/v1/biens/?id_sci=sci-1", headers=auth_headers)
    assert response.status_code == 503


def test_create_bien_insert_error(client, auth_headers, fake_supabase):
    """Cover line 89: insert returns error."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_insert = q.insert
            def insert_with_error(payload):
                result = orig_insert(payload)
                orig_execute = result.execute
                def execute_with_error():
                    return FakeResult(data=[], error="insert failed")
                result.execute = execute_with_error
                return result
            q.insert = insert_with_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        payload = {
            "id_sci": "sci-1",
            "adresse": "10 rue Test",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 1500.0,
        }
        response = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    assert response.status_code == 503


def test_create_bien_empty_result(client, auth_headers, fake_supabase):
    """Cover line 93: insert returns no data."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_insert = q.insert
            def insert_empty(payload):
                result = orig_insert(payload)
                orig_execute = result.execute
                def execute_empty():
                    return FakeResult(data=[])
                result.execute = execute_empty
                return result
            q.insert = insert_empty
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        payload = {
            "id_sci": "sci-1",
            "adresse": "10 rue Test",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 1500.0,
        }
        response = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    assert response.status_code == 503


def test_update_bien_error_on_update_query(client, auth_headers, fake_supabase):
    """Cover line 133: error when executing update query."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table
    call_count = {"biens_update": 0}

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_update = q.update
            def update_with_error(payload):
                result = orig_update(payload)
                # Wrap the final execute to return error
                class ErrorQuery:
                    def __init__(self, inner):
                        self._inner = inner
                    def eq(self, *a, **kw):
                        self._inner = self._inner.eq(*a, **kw)
                        return self
                    def execute(self):
                        return FakeResult(data=[], error="update failed")
                return ErrorQuery(result)
            q.update = update_with_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.patch(
            "/api/v1/biens/bien-1",
            json={"ville": "Marseille"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_bien_empty_result_after_update(client, auth_headers, fake_supabase):
    """Cover line 137: update returns no data -> ResourceNotFoundError."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
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
            "/api/v1/biens/bien-1",
            json={"ville": "Marseille"},
            headers=auth_headers,
        )
    assert response.status_code == 404


def test_delete_bien_error_on_delete_query(client, auth_headers, fake_supabase):
    """Cover line 166: error when executing delete query."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_delete = q.delete
            def delete_with_error():
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
            q.delete = delete_with_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.delete("/api/v1/biens/bien-1", headers=auth_headers)
    assert response.status_code == 503


def test_select_by_sci_scope_fallback_loop(client, auth_headers, fake_supabase):
    """Cover lines 41-47: _select_by_sci_scope fallback when query lacks in_ method.

    Patches hasattr to return False for 'in_' on FakeQuery instances used by _select_by_sci_scope.
    """
    import builtins
    original_hasattr = builtins.hasattr

    def patched_hasattr(obj, name):
        if name == "in_" and type(obj).__name__ == "FakeQuery":
            return False
        return original_hasattr(obj, name)

    from unittest.mock import patch
    with patch("builtins.hasattr", side_effect=patched_hasattr):
        response = client.get("/api/v1/biens/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_select_by_sci_scope_empty():
    """Cover line 31: _select_by_sci_scope with empty sci_ids returns []."""
    from app.api.v1.biens import _select_by_sci_scope
    assert _select_by_sci_scope(None, "biens", []) == []


def test_select_by_sci_scope_fallback_error(client, auth_headers, fake_supabase):
    """Cover line 45: error inside the fallback loop of _select_by_sci_scope."""
    import builtins
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_hasattr = builtins.hasattr
    original_table = fake_supabase.table
    call_count = {"biens_select": 0}

    def patched_hasattr(obj, name):
        if name == "in_" and type(obj).__name__ == "FakeQuery":
            return False
        return original_hasattr(obj, name)

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            call_count["biens_select"] += 1
            if call_count["biens_select"] > 0:
                orig_select = q.select
                def select_error(*a, **kw):
                    result = orig_select(*a, **kw)
                    orig_eq = result.eq
                    def eq_error(key, value):
                        r = orig_eq(key, value)
                        if key == "id_sci":
                            r.execute = lambda: FakeResult(data=[], error="fallback error")
                        return r
                    result.eq = eq_error
                    return result
                q.select = select_error
        return q

    with (
        patch("builtins.hasattr", side_effect=patched_hasattr),
        patch.object(fake_supabase, "table", side_effect=patched_table),
    ):
        response = client.get("/api/v1/biens/", headers=auth_headers)
    assert response.status_code == 503


def test_select_by_sci_scope_in_error():
    """Cover line 37: error in _select_by_sci_scope in_ path."""
    from app.api.v1.biens import _select_by_sci_scope
    from tests.conftest import FakeResult, FakeSupabaseClient, FakeQuery
    from app.core.exceptions import DatabaseError
    import pytest as _pytest

    fake_client = FakeSupabaseClient()

    original_in = FakeQuery.in_

    def in_with_error(self, key, values):
        result = original_in(self, key, values)
        orig_execute = result.execute
        def execute_error():
            return FakeResult(data=[], error="in_ query failed")
        result.execute = execute_error
        return result

    try:
        FakeQuery.in_ = in_with_error
        with _pytest.raises(DatabaseError):
            _select_by_sci_scope(fake_client, "biens", ["sci-1"])
    finally:
        FakeQuery.in_ = original_in


def test_require_sci_access_missing_id_sci():
    """Cover line 52: _require_sci_access with empty id_sci raises DatabaseError."""
    from app.api.v1.biens import _require_sci_access
    from app.core.exceptions import DatabaseError
    import pytest as _pytest

    with _pytest.raises(DatabaseError, match="Missing id_sci"):
        _require_sci_access(["sci-1"], "")


def test_require_sci_access_unauthorized():
    """Cover line 54: _require_sci_access with wrong id_sci raises AuthorizationError."""
    from app.api.v1.biens import _require_sci_access
    from app.core.exceptions import AuthorizationError
    import pytest as _pytest

    with _pytest.raises(AuthorizationError):
        _require_sci_access(["sci-1"], "sci-999")


def test_get_user_sci_ids_error(client, auth_headers, fake_supabase):
    """Cover line 24: error from associes query."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "associes":
            orig_execute = q.execute
            class ErrorSelectQuery:
                def __init__(self, inner):
                    self._inner = inner
                def select(self, *a, **kw):
                    self._inner = self._inner.select(*a, **kw)
                    return self
                def eq(self, *a, **kw):
                    self._inner = self._inner.eq(*a, **kw)
                    return self
                def execute(self):
                    return FakeResult(data=[], error="associes query failed")
            return ErrorSelectQuery(q)
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.get("/api/v1/biens/", headers=auth_headers)
    assert response.status_code == 503


def test_update_bien_error_fetching_existing(client, auth_headers, fake_supabase):
    """Cover line 114: error when fetching existing bien for update."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table
    select_call_count = {"count": 0}

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_select = q.select
            def select_with_error(*args, **kwargs):
                select_call_count["count"] += 1
                result = orig_select(*args, **kwargs)
                # Only error on the biens select (2nd call, after associes)
                class ErrorEqQuery:
                    def __init__(self, inner):
                        self._inner = inner
                    def eq(self, key, value):
                        if key == "id":
                            # This is the fetch for the existing bien
                            class ErrorExecute:
                                def execute(self_inner):
                                    return FakeResult(data=[], error="fetch error")
                            return ErrorExecute()
                        self._inner = self._inner.eq(key, value)
                        return self
                    def execute(self):
                        return self._inner.execute()
                return ErrorEqQuery(result)
            q.select = select_with_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.patch(
            "/api/v1/biens/bien-1",
            json={"ville": "Marseille"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_delete_bien_error_fetching_existing(client, auth_headers, fake_supabase):
    """Cover line 154: error when fetching existing bien for delete."""
    from unittest.mock import patch
    from tests.conftest import FakeResult

    original_table = fake_supabase.table

    def patched_table(name):
        q = original_table(name)
        if name == "biens":
            orig_select = q.select
            def select_with_error(*args, **kwargs):
                result = orig_select(*args, **kwargs)
                class ErrorEqQuery:
                    def __init__(self, inner):
                        self._inner = inner
                    def eq(self, key, value):
                        if key == "id":
                            class ErrorExecute:
                                def execute(self_inner):
                                    return FakeResult(data=[], error="fetch error")
                            return ErrorExecute()
                        self._inner = self._inner.eq(key, value)
                        return self
                    def execute(self):
                        return self._inner.execute()
                return ErrorEqQuery(result)
            q.select = select_with_error
        return q

    with patch.object(fake_supabase, "table", side_effect=patched_table):
        response = client.delete("/api/v1/biens/bien-1", headers=auth_headers)
    assert response.status_code == 503
