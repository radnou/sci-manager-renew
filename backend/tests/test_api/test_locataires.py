import pytest
from unittest.mock import MagicMock, patch
from app.api.v1.locataires import (
    _get_user_sci_ids,
    _require_sci_access,
    _fetch_accessible_biens,
    _fetch_bien,
    _fetch_locataires_by_bien_ids,
    _validate_date_range,
    _enrich_locataire_rows,
)
from app.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    ValidationError as AppValidationError,
)
from datetime import date


# ── Unit tests for helper functions ──────────────────────────────────────


def test_get_user_sci_ids_db_error():
    """_get_user_sci_ids raises DatabaseError when result has error."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.error = "connection refused"
    mock_result.data = []
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    with pytest.raises(DatabaseError):
        _get_user_sci_ids(mock_client, "user-x")


def test_require_sci_access_missing_id_sci():
    """_require_sci_access raises DatabaseError when id_sci is empty."""
    with pytest.raises(DatabaseError, match="Missing id_sci"):
        _require_sci_access(["sci-1"], "")


def test_require_sci_access_unauthorized():
    """_require_sci_access raises AuthorizationError when id_sci not in user list."""
    with pytest.raises(AuthorizationError):
        _require_sci_access(["sci-1", "sci-2"], "sci-99")


def test_fetch_accessible_biens_empty_sci_ids():
    """_fetch_accessible_biens returns [] when sci_ids is empty."""
    mock_client = MagicMock()
    result = _fetch_accessible_biens(mock_client, [])
    assert result == []


def test_fetch_accessible_biens_db_error():
    """_fetch_accessible_biens raises DatabaseError on query failure."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.error = "timeout"
    mock_result.data = []
    mock_query = MagicMock()
    mock_query.in_.return_value.execute.return_value = mock_result
    mock_client.table.return_value.select.return_value = mock_query
    with pytest.raises(DatabaseError):
        _fetch_accessible_biens(mock_client, ["sci-1"])


def test_fetch_accessible_biens_fallback_no_in(monkeypatch):
    """_fetch_accessible_biens uses fallback loop when in_ is not available."""
    mock_client = MagicMock()
    # Create a query object WITHOUT in_ method
    mock_query = MagicMock(spec=[])  # empty spec = no methods
    mock_query.select = MagicMock(return_value=mock_query)
    mock_query.eq = MagicMock(return_value=mock_query)
    mock_result = MagicMock()
    mock_result.error = None
    mock_result.data = [{"id": "b1", "id_sci": "sci-1", "adresse": "1 X", "ville": "Y"}]
    mock_query.execute = MagicMock(return_value=mock_result)
    mock_client.table.return_value.select.return_value = mock_query
    # Remove in_ to trigger fallback path
    assert not hasattr(mock_query, "in_")
    result = _fetch_accessible_biens(mock_client, ["sci-1"])
    assert len(result) == 1
    assert result[0]["id"] == "b1"


def test_fetch_accessible_biens_fallback_db_error():
    """_fetch_accessible_biens fallback raises DatabaseError on query failure."""
    mock_client = MagicMock()
    mock_query = MagicMock(spec=[])
    mock_query.select = MagicMock(return_value=mock_query)
    mock_query.eq = MagicMock(return_value=mock_query)
    mock_result = MagicMock()
    mock_result.error = "connection lost"
    mock_result.data = []
    mock_query.execute = MagicMock(return_value=mock_result)
    mock_client.table.return_value.select.return_value = mock_query
    with pytest.raises(DatabaseError):
        _fetch_accessible_biens(mock_client, ["sci-1"])


def test_fetch_bien_db_error():
    """_fetch_bien raises DatabaseError on query failure."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.error = "server error"
    mock_result.data = []
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    with pytest.raises(DatabaseError):
        _fetch_bien(mock_client, "bien-x")


def test_fetch_bien_not_found():
    """_fetch_bien raises ValidationError when bien does not exist."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.error = None
    mock_result.data = []
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    with pytest.raises(AppValidationError, match="Unknown bien id"):
        _fetch_bien(mock_client, "bien-ghost")


def test_fetch_locataires_by_bien_ids_empty():
    """_fetch_locataires_by_bien_ids returns [] for empty list."""
    mock_client = MagicMock()
    result = _fetch_locataires_by_bien_ids(mock_client, [])
    assert result == []


def test_fetch_locataires_by_bien_ids_db_error():
    """_fetch_locataires_by_bien_ids raises DatabaseError on query failure."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.error = "query failed"
    mock_query = MagicMock()
    mock_query.in_.return_value.execute.return_value = mock_result
    mock_client.table.return_value.select.return_value = mock_query
    with pytest.raises(DatabaseError):
        _fetch_locataires_by_bien_ids(mock_client, ["bien-1"])


def test_fetch_locataires_by_bien_ids_fallback_no_in():
    """_fetch_locataires_by_bien_ids uses fallback loop when in_ is unavailable."""
    mock_client = MagicMock()
    mock_query = MagicMock(spec=[])
    mock_query.select = MagicMock(return_value=mock_query)
    mock_query.eq = MagicMock(return_value=mock_query)
    mock_result = MagicMock()
    mock_result.error = None
    mock_result.data = [{"id": "loc-1", "id_bien": "bien-1", "nom": "AB"}]
    mock_query.execute = MagicMock(return_value=mock_result)
    mock_client.table.return_value.select.return_value = mock_query
    assert not hasattr(mock_query, "in_")
    result = _fetch_locataires_by_bien_ids(mock_client, ["bien-1"])
    assert len(result) == 1


def test_fetch_locataires_by_bien_ids_fallback_db_error():
    """_fetch_locataires_by_bien_ids fallback raises DatabaseError."""
    mock_client = MagicMock()
    mock_query = MagicMock(spec=[])
    mock_query.select = MagicMock(return_value=mock_query)
    mock_query.eq = MagicMock(return_value=mock_query)
    mock_result = MagicMock()
    mock_result.error = "db down"
    mock_result.data = []
    mock_query.execute = MagicMock(return_value=mock_result)
    mock_client.table.return_value.select.return_value = mock_query
    with pytest.raises(DatabaseError):
        _fetch_locataires_by_bien_ids(mock_client, ["bien-1"])


def test_validate_date_range_valid():
    """_validate_date_range passes for valid dates."""
    _validate_date_range(date(2026, 1, 1), date(2026, 12, 31))
    _validate_date_range(date(2026, 1, 1), None)
    _validate_date_range(date(2026, 1, 1), date(2026, 1, 1))  # equal is OK


def test_validate_date_range_invalid():
    """_validate_date_range raises ValidationError when date_fin < date_debut."""
    with pytest.raises(AppValidationError, match="date_fin must be later"):
        _validate_date_range(date(2026, 6, 1), date(2026, 5, 1))


def test_enrich_locataire_rows_with_matching_bien():
    """_enrich_locataire_rows adds id_sci from bien_map."""
    locataires = [{"id": "l1", "id_bien": "b1", "nom": "Test"}]
    bien_map = {"b1": {"id": "b1", "id_sci": "s1"}}
    result = _enrich_locataire_rows(locataires, bien_map)
    assert result[0]["id_sci"] == "s1"


def test_enrich_locataire_rows_without_matching_bien():
    """_enrich_locataire_rows returns None id_sci when bien not in map."""
    locataires = [{"id": "l1", "id_bien": "b-unknown", "nom": "Test"}]
    bien_map = {}
    result = _enrich_locataire_rows(locataires, bien_map)
    assert result[0]["id_sci"] is None


def test_enrich_locataire_rows_bien_without_id_sci():
    """_enrich_locataire_rows returns None id_sci when bien has no id_sci."""
    locataires = [{"id": "l1", "id_bien": "b1", "nom": "Test"}]
    bien_map = {"b1": {"id": "b1"}}  # no id_sci key
    result = _enrich_locataire_rows(locataires, bien_map)
    assert result[0]["id_sci"] is None


# ── Integration-level error path tests ────────────────────────────────────
# These tests use proxy clients that do NOT mutate the shared FakeSupabaseClient.
# Each creates a fully independent wrapper that delegates to the real store
# but intercepts specific operations.


class _ProxyClient:
    """Wraps FakeSupabaseClient without mutating it."""

    def __init__(self, real_client, table_interceptor=None):
        self._real = real_client
        self._table_interceptor = table_interceptor

    def table(self, name):
        if self._table_interceptor:
            result = self._table_interceptor(name, self._real)
            if result is not None:
                return result
        return self._real.table(name)

    def __getattr__(self, name):
        return getattr(self._real, name)


def test_list_locataires_generic_exception(client, auth_headers, fake_supabase):
    """Generic exception in list_locataires returns 503 DatabaseError."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    def interceptor(name, real):
        if name == "locataires":
            raise RuntimeError("unexpected boom")
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.get("/api/v1/locataires/", headers=auth_headers)
    assert response.status_code == 503


def test_create_locataire_generic_exception(client, auth_headers, fake_supabase):
    """Non-SCIManagerException during create returns 503."""
    from app.api.v1 import locataires as loc_mod

    def interceptor(name, real):
        if name == "locataires":
            raise TypeError("unexpected type error")
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.post(
            "/api/v1/locataires/",
            json={"id_bien": "bien-1", "nom": "Boom", "date_debut": "2026-01-01"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_locataire_generic_exception(client, auth_headers, fake_supabase):
    """Non-SCIManagerException during update returns 503."""
    from app.api.v1 import locataires as loc_mod

    def interceptor(name, real):
        if name == "locataires":
            raise TypeError("unexpected in update")
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.patch(
            "/api/v1/locataires/loc-any",
            json={"email": "boom@e.fr"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_delete_locataire_generic_exception(client, auth_headers, fake_supabase):
    """Non-SCIManagerException during delete returns 503."""
    from app.api.v1 import locataires as loc_mod

    def interceptor(name, real):
        if name == "locataires":
            raise TypeError("unexpected in delete")
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.delete("/api/v1/locataires/loc-any", headers=auth_headers)
    assert response.status_code == 503


def test_create_locataire_insert_db_error(client, auth_headers, fake_supabase):
    """Database error during insert returns 503."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    class InsertErrorQuery:
        def __init__(self, real_query):
            self._real = real_query
            self._is_insert = False
        def __getattr__(self, n):
            return getattr(self._real, n)
        def insert(self, payload):
            self._is_insert = True
            return self
        def execute(self):
            if self._is_insert:
                return FakeResult(data=[], error="insert failed")
            return self._real.execute()

    def interceptor(name, real):
        if name == "locataires":
            return InsertErrorQuery(real.table(name))
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.post(
            "/api/v1/locataires/",
            json={"id_bien": "bien-1", "nom": "DB Error", "date_debut": "2026-01-01"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_create_locataire_insert_returns_empty(client, auth_headers, fake_supabase):
    """Insert returns empty data list raises DatabaseError (503)."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    class InsertEmptyQuery:
        def __init__(self, real_query):
            self._real = real_query
            self._is_insert = False
        def __getattr__(self, n):
            return getattr(self._real, n)
        def insert(self, payload):
            self._is_insert = True
            return self
        def execute(self):
            if self._is_insert:
                return FakeResult(data=[])
            return self._real.execute()

    def interceptor(name, real):
        if name == "locataires":
            return InsertEmptyQuery(real.table(name))
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.post(
            "/api/v1/locataires/",
            json={"id_bien": "bien-1", "nom": "Empty Result", "date_debut": "2026-01-01"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_locataire_db_error_on_select(client, auth_headers, fake_supabase):
    """Database error when selecting existing locataire returns 503."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    class SelectErrorQuery:
        def select(self, *a, **kw): return self
        def eq(self, k, v): return self
        def execute(self): return FakeResult(data=[], error="select failed")

    def interceptor(name, real):
        if name == "locataires":
            return SelectErrorQuery()
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.patch(
            "/api/v1/locataires/loc-xx",
            json={"email": "new@e.fr"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_locataire_update_db_error(client, auth_headers, fake_supabase):
    """Database error during update query returns 503."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    fake_supabase.store["locataires"] = [
        {"id": "loc-ue", "id_bien": "bien-1", "nom": "Update Error", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    call_count = {"n": 0}

    class UpdateErrorQuery:
        def __init__(self, real_query):
            self._real = real_query
        def __getattr__(self, n): return getattr(self._real, n)
        def update(self, payload): return self
        def eq(self, key, value): return self
        def execute(self): return FakeResult(data=[], error="update failed")

    def interceptor(name, real):
        if name == "locataires":
            call_count["n"] += 1
            if call_count["n"] >= 2:
                return UpdateErrorQuery(real.table(name))
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.patch(
            "/api/v1/locataires/loc-ue",
            json={"email": "fail@e.fr"},
            headers=auth_headers,
        )
    assert response.status_code == 503


def test_update_locataire_update_returns_empty(client, auth_headers, fake_supabase):
    """Update returns empty data raises ResourceNotFoundError (404)."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    fake_supabase.store["locataires"] = [
        {"id": "loc-ue2", "id_bien": "bien-1", "nom": "Will Disappear", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    call_count = {"n": 0}

    class UpdateEmptyQuery:
        def __init__(self, real_query):
            self._real = real_query
        def __getattr__(self, n): return getattr(self._real, n)
        def update(self, payload): return self
        def eq(self, key, value): return self
        def execute(self): return FakeResult(data=[])

    def interceptor(name, real):
        if name == "locataires":
            call_count["n"] += 1
            if call_count["n"] >= 2:
                return UpdateEmptyQuery(real.table(name))
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.patch(
            "/api/v1/locataires/loc-ue2",
            json={"email": "empty@e.fr"},
            headers=auth_headers,
        )
    assert response.status_code == 404


def test_delete_locataire_db_error_on_select(client, auth_headers, fake_supabase):
    """Database error selecting locataire for delete returns 503."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    class SelectErrorQuery:
        def select(self, *a, **kw): return self
        def eq(self, k, v): return self
        def execute(self): return FakeResult(data=[], error="select err")

    def interceptor(name, real):
        if name == "locataires":
            return SelectErrorQuery()
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.delete("/api/v1/locataires/loc-z", headers=auth_headers)
    assert response.status_code == 503


def test_delete_locataire_db_error_on_delete(client, auth_headers, fake_supabase):
    """Database error during delete query returns 503."""
    from app.api.v1 import locataires as loc_mod
    from tests.conftest import FakeResult

    fake_supabase.store["locataires"] = [
        {"id": "loc-de", "id_bien": "bien-1", "nom": "Del Error", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    call_count = {"n": 0}

    class DeleteErrorQuery:
        def delete(self): return self
        def eq(self, k, v): return self
        def execute(self): return FakeResult(data=[], error="delete failed")

    def interceptor(name, real):
        if name == "locataires":
            call_count["n"] += 1
            if call_count["n"] >= 2:
                return DeleteErrorQuery()
        return None

    proxy = _ProxyClient(fake_supabase, interceptor)
    with patch.object(loc_mod, "get_supabase_user_client", lambda request=None: proxy):
        response = client.delete("/api/v1/locataires/loc-de", headers=auth_headers)
    assert response.status_code == 503


# ── Original integration tests ───────────────────────────────────────────


def test_get_locataires_requires_auth(client):
    response = client.get("/api/v1/locataires/")
    assert response.status_code == 401


def test_create_and_filter_locataires(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "10 rue Locataire",
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

    create_response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": bien_id,
            "nom": "Jean Martin",
            "email": "jean.martin@example.com",
            "date_debut": "2026-01-15",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["nom"] == "Jean Martin"
    assert create_response.json()["id_sci"] == "sci-1"

    filtered = client.get(f"/api/v1/locataires/?id_bien={bien_id}", headers=auth_headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["nom"] == "Jean Martin"


def test_update_and_delete_locataire(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "11 rue Bail",
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

    created = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": bien_id,
            "nom": "Alice Bernard",
            "email": "alice@example.com",
            "date_debut": "2026-02-01",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    locataire_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/locataires/{locataire_id}",
        json={"email": "alice.bernard@example.com", "date_fin": "2026-12-31"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "alice.bernard@example.com"
    assert updated.json()["date_fin"] == "2026-12-31"

    deleted = client.delete(f"/api/v1/locataires/{locataire_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_create_locataire_rejects_invalid_dates(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "12 rue Bail",
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

    response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": bien_id,
            "nom": "Bail incohérent",
            "date_debut": "2026-05-01",
            "date_fin": "2026-04-01",
        },
        headers=auth_headers,
    )
    assert response.status_code in (400, 422)


# ── Auth required on all endpoints ───────────────────────────────────────

def test_create_locataire_requires_auth(client):
    response = client.post("/api/v1/locataires/", json={"id_bien": "b", "nom": "AA", "date_debut": "2026-01-01"})
    assert response.status_code == 401


def test_update_locataire_requires_auth(client):
    response = client.patch("/api/v1/locataires/loc-xyz", json={"nom": "New Name"})
    assert response.status_code == 401


def test_delete_locataire_requires_auth(client):
    response = client.delete("/api/v1/locataires/loc-xyz")
    assert response.status_code == 401


# ── List locataires ──────────────────────────────────────────────────────

def test_list_locataires_empty(client, auth_headers):
    """Empty locataires table returns empty list."""
    response = client.get("/api/v1/locataires/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_locataires_no_trailing_slash(client, auth_headers, fake_supabase):
    """GET /api/v1/locataires (no slash) works."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-1", "id_bien": "bien-1", "nom": "Dupont", "email": "d@e.fr", "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.get("/api/v1/locataires", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_list_locataires_with_sci_id_filter(client, auth_headers, fake_supabase):
    """Filter by sci_id returns only locataires whose bien belongs to that SCI."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-a", "id_bien": "bien-1", "nom": "Dupont A", "email": None, "date_debut": "2026-01-01", "date_fin": None},
        {"id": "loc-b", "id_bien": "bien-9", "nom": "Dupont B", "email": None, "date_debut": "2026-02-01", "date_fin": None},
    ]
    response = client.get("/api/v1/locataires/?id_sci=sci-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Only loc-a belongs to sci-1 (via bien-1)
    assert len(data) == 1
    assert data[0]["id"] == "loc-a"
    assert data[0]["id_sci"] == "sci-1"


def test_list_locataires_with_bien_id_filter(client, auth_headers, fake_supabase):
    """Filter by bien_id returns only locataires for that bien."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-x", "id_bien": "bien-1", "nom": "Xavier", "email": None, "date_debut": "2026-01-01", "date_fin": None},
        {"id": "loc-y", "id_bien": "bien-9", "nom": "Yves", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.get("/api/v1/locataires/?id_bien=bien-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "loc-x"


def test_list_locataires_bien_id_unauthorized(client, auth_headers, fake_supabase):
    """Filtering by a bien_id that user cannot access returns 403."""
    # bien-unknown is not in biens table at all
    response = client.get("/api/v1/locataires/?id_bien=bien-unknown", headers=auth_headers)
    assert response.status_code == 403


def test_list_locataires_sci_id_unauthorized(client, auth_headers, fake_supabase):
    """Filtering by a sci_id the user is not associated with returns 403."""
    response = client.get("/api/v1/locataires/?id_sci=sci-nope", headers=auth_headers)
    assert response.status_code == 403


def test_list_locataires_all_scis(client, auth_headers, fake_supabase):
    """Without filters, returns locataires across all user SCIs with enriched id_sci."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-1", "id_bien": "bien-1", "nom": "Alpha", "email": None, "date_debut": "2026-01-01", "date_fin": None},
        {"id": "loc-2", "id_bien": "bien-9", "nom": "Beta", "email": None, "date_debut": "2026-02-01", "date_fin": None},
    ]
    response = client.get("/api/v1/locataires/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    sci_map = {row["id"]: row["id_sci"] for row in data}
    assert sci_map["loc-1"] == "sci-1"
    assert sci_map["loc-2"] == "sci-2"


# ── Create locataire ─────────────────────────────────────────────────────

def test_create_locataire_all_fields(client, auth_headers):
    """Create locataire with all optional fields populated."""
    response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": "bien-1",
            "nom": "Marie Curie",
            "email": "marie@example.com",
            "date_debut": "2026-03-01",
            "date_fin": "2027-03-01",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nom"] == "Marie Curie"
    assert body["email"] == "marie@example.com"
    assert body["date_debut"] == "2026-03-01"
    assert body["date_fin"] == "2027-03-01"
    assert body["id_sci"] == "sci-1"
    assert "id" in body


def test_create_locataire_minimal_fields(client, auth_headers):
    """Create locataire with only required fields (no email, no date_fin)."""
    response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": "bien-9",
            "nom": "Paul Minimal",
            "date_debut": "2026-06-01",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nom"] == "Paul Minimal"
    assert body["email"] is None
    assert body["date_fin"] is None
    assert body["id_sci"] == "sci-2"


def test_create_locataire_no_trailing_slash(client, auth_headers):
    """POST /api/v1/locataires (no slash) works."""
    response = client.post(
        "/api/v1/locataires",
        json={"id_bien": "bien-1", "nom": "No Slash", "date_debut": "2026-01-01"},
        headers=auth_headers,
    )
    assert response.status_code == 201


def test_create_locataire_unknown_bien(client, auth_headers):
    """Creating locataire for a non-existent bien returns 422."""
    response = client.post(
        "/api/v1/locataires/",
        json={"id_bien": "bien-nonexistent", "nom": "Ghost", "date_debut": "2026-01-01"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_create_locataire_unauthorized_sci(client, auth_headers, fake_supabase):
    """Creating locataire for a bien belonging to an unauthorized SCI returns 403."""
    # Add a bien belonging to an SCI the user is NOT associated with
    fake_supabase.store["biens"].append(
        {"id": "bien-other", "id_sci": "sci-other", "adresse": "99 rue X", "ville": "Nantes", "code_postal": "44000"}
    )
    response = client.post(
        "/api/v1/locataires/",
        json={"id_bien": "bien-other", "nom": "Forbidden", "date_debut": "2026-01-01"},
        headers=auth_headers,
    )
    assert response.status_code == 403


# ── Update locataire ─────────────────────────────────────────────────────

def test_update_locataire_email_only(client, auth_headers, fake_supabase):
    """Partial update — change email only."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-u1", "id_bien": "bien-1", "nom": "Update Me", "email": "old@e.fr", "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u1",
        json={"email": "new@e.fr"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new@e.fr"
    assert response.json()["id_sci"] == "sci-1"


def test_update_locataire_nom_only(client, auth_headers, fake_supabase):
    """Partial update — change nom only."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-u2", "id_bien": "bien-1", "nom": "Old Name", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u2",
        json={"nom": "New Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["nom"] == "New Name"


def test_update_locataire_not_found(client, auth_headers):
    """Updating a non-existent locataire returns 404."""
    response = client.patch(
        "/api/v1/locataires/loc-ghost",
        json={"email": "ghost@e.fr"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_locataire_empty_payload(client, auth_headers, fake_supabase):
    """Updating with no fields returns 400 (validation error)."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-u3", "id_bien": "bien-1", "nom": "Empty", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u3",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_update_locataire_date_validation_fail(client, auth_headers, fake_supabase):
    """Updating date_fin to before existing date_debut returns 400."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-u4", "id_bien": "bien-1", "nom": "Date Test", "email": None, "date_debut": "2026-06-01", "date_fin": None},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u4",
        json={"date_fin": "2026-05-01"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_update_locataire_change_both_dates_valid(client, auth_headers, fake_supabase):
    """Updating both date_debut and date_fin with valid range succeeds."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-u5", "id_bien": "bien-1", "nom": "Both Dates", "email": None, "date_debut": "2026-01-01", "date_fin": "2026-12-31"},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u5",
        json={"date_debut": "2026-03-01", "date_fin": "2027-03-01"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["date_debut"] == "2026-03-01"
    assert body["date_fin"] == "2027-03-01"


def test_update_locataire_change_both_dates_invalid(client, auth_headers, fake_supabase):
    """Updating both dates where new date_fin < new date_debut returns 400."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-u6", "id_bien": "bien-1", "nom": "Both Invalid", "email": None, "date_debut": "2026-01-01", "date_fin": "2026-12-31"},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u6",
        json={"date_debut": "2026-10-01", "date_fin": "2026-09-01"},
        headers=auth_headers,
    )
    assert response.status_code == 400


# ── Delete locataire ─────────────────────────────────────────────────────

def test_delete_locataire_not_found(client, auth_headers):
    """Deleting a non-existent locataire returns 404."""
    response = client.delete("/api/v1/locataires/loc-ghost", headers=auth_headers)
    assert response.status_code == 404


def test_delete_locataire_success(client, auth_headers, fake_supabase):
    """Delete an existing locataire returns 204 and removes from store."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-d1", "id_bien": "bien-1", "nom": "To Delete", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.delete("/api/v1/locataires/loc-d1", headers=auth_headers)
    assert response.status_code == 204
    # Verify it was actually removed
    assert len(fake_supabase.store["locataires"]) == 0


def test_delete_locataire_unauthorized_sci(client, auth_headers, fake_supabase):
    """Deleting a locataire belonging to an unauthorized SCI returns 403."""
    fake_supabase.store["biens"].append(
        {"id": "bien-unauth", "id_sci": "sci-unauth", "adresse": "1 X", "ville": "Z", "code_postal": "00000"}
    )
    fake_supabase.store["locataires"] = [
        {"id": "loc-d2", "id_bien": "bien-unauth", "nom": "Forbidden", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.delete("/api/v1/locataires/loc-d2", headers=auth_headers)
    assert response.status_code == 403


# ── Enrichment logic ─────────────────────────────────────────────────────

def test_enrich_locataire_with_id_sci(client, auth_headers, fake_supabase):
    """Response includes id_sci from the bien's SCI."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-e1", "id_bien": "bien-9", "nom": "Enriched", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.get("/api/v1/locataires/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_sci"] == "sci-2"


def test_enrich_locataire_missing_bien_returns_null_sci(client, auth_headers, fake_supabase):
    """Locataire whose id_bien has no matching bien gets id_sci=None."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-orphan", "id_bien": "bien-phantom", "nom": "Orphan", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    # bien-phantom is not in biens, so it won't appear in bien_map
    # The locataire won't match any bien_ids from accessible biens, so it won't be returned
    response = client.get("/api/v1/locataires/", headers=auth_headers)
    assert response.status_code == 200
    # Orphan locataire is not returned because bien-phantom is not accessible
    assert len(response.json()) == 0


# ── Update locataire — unauthorized SCI ──────────────────────────────────

def test_update_locataire_unauthorized_sci(client, auth_headers, fake_supabase):
    """Updating a locataire belonging to an unauthorized SCI returns 403."""
    fake_supabase.store["biens"].append(
        {"id": "bien-unauth2", "id_sci": "sci-unauth2", "adresse": "2 X", "ville": "Z", "code_postal": "00000"}
    )
    fake_supabase.store["locataires"] = [
        {"id": "loc-u-unauth", "id_bien": "bien-unauth2", "nom": "Forbidden Update", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-u-unauth",
        json={"email": "hack@evil.com"},
        headers=auth_headers,
    )
    assert response.status_code == 403


# ── Create via POST without trailing slash ───────────────────────────────

def test_create_locataire_for_second_sci(client, auth_headers):
    """Create locataire on a bien from user's second SCI (sci-2)."""
    response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": "bien-9",
            "nom": "Second SCI Tenant",
            "email": "tenant2@sci.fr",
            "date_debut": "2026-04-01",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id_sci"] == "sci-2"
    assert body["nom"] == "Second SCI Tenant"


# ── List with combined filters ───────────────────────────────────────────

def test_list_locataires_sci_and_bien_filter(client, auth_headers, fake_supabase):
    """Combined sci_id + bien_id filter works correctly."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-c1", "id_bien": "bien-1", "nom": "Combo", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    response = client.get("/api/v1/locataires/?id_sci=sci-1&id_bien=bien-1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["nom"] == "Combo"


def test_list_locataires_sci_and_wrong_bien_filter(client, auth_headers, fake_supabase):
    """sci_id + bien_id filter with mismatched bien returns 403 (bien not in that SCI's accessible biens)."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-c2", "id_bien": "bien-9", "nom": "Mismatch", "email": None, "date_debut": "2026-01-01", "date_fin": None},
    ]
    # bien-9 belongs to sci-2, not sci-1
    response = client.get("/api/v1/locataires/?id_sci=sci-1&id_bien=bien-9", headers=auth_headers)
    assert response.status_code == 403


# ── Edge: update date_debut only, keeping existing date_fin ──────────────

def test_update_locataire_date_debut_only_valid(client, auth_headers, fake_supabase):
    """Updating date_debut to a date still before existing date_fin succeeds."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-dd", "id_bien": "bien-1", "nom": "DateDebut", "email": None, "date_debut": "2026-01-01", "date_fin": "2026-12-31"},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-dd",
        json={"date_debut": "2026-06-01"},
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_update_locataire_date_debut_only_invalid(client, auth_headers, fake_supabase):
    """Updating date_debut to after existing date_fin returns 400."""
    fake_supabase.store["locataires"] = [
        {"id": "loc-dd2", "id_bien": "bien-1", "nom": "DateDebut2", "email": None, "date_debut": "2026-01-01", "date_fin": "2026-06-01"},
    ]
    response = client.patch(
        "/api/v1/locataires/loc-dd2",
        json={"date_debut": "2026-07-01"},
        headers=auth_headers,
    )
    assert response.status_code == 400
