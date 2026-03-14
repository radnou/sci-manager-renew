from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
import jwt

from app.core.config import settings
from app.core.rate_limit import limiter
from app.main import app

# Override settings for tests
settings.cors_origins = ["http://testserver"]

# Disable rate limiting in tests to avoid 429 errors
limiter.enabled = False

# ── Seed data (deep-copied into every fresh FakeSupabaseClient) ──────────

_INITIAL_STORE: dict[str, list[dict]] = {
    "sci": [
        {"id": "sci-1", "nom": "SCI Mosa Belleville", "siren": "123456789", "regime_fiscal": "IR"},
        {"id": "sci-2", "nom": "SCI Horizon Lyon", "siren": "987654321", "regime_fiscal": "IS"},
    ],
    "biens": [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris", "code_postal": "75001", "type_bien": "appartement", "surface_m2": 50, "nb_pieces": 2, "loyer_cc": 1200, "statut": "loue", "tmi": 30},
        {"id": "bien-9", "id_sci": "sci-2", "adresse": "42 avenue QA", "ville": "Lyon", "code_postal": "69001", "type_bien": "appartement", "surface_m2": 35, "nb_pieces": 1, "loyer_cc": 980, "statut": "loue", "tmi": 30},
        {"id": "bien-free", "id_sci": "sci-1", "adresse": "5 rue Gratuite", "ville": "Lyon", "code_postal": "69002", "type_bien": "studio", "surface_m2": 20, "nb_pieces": 1, "loyer_cc": 800, "statut": "loue", "tmi": 30},
    ],
    "locataires": [],
    "loyers": [
        {"id": "loyer-1", "id_bien": "bien-1", "date_loyer": "2026-03-01", "montant": 1200.0, "statut": "paye"},
        {"id": "loyer-2", "id_bien": "bien-9", "date_loyer": "2026-04-01", "montant": 980.0, "statut": "paye"},
        {"id": "loyer-free", "id_bien": "bien-free", "date_loyer": "2026-01-01", "montant": 800.0, "statut": "paye"},
    ],
    "charges": [],
    "fiscalite": [],
    "admins": [
        {"user_id": "user-123"},
    ],
    "subscriptions": [
        {"id": "sub-1", "user_id": "user-123", "status": "active", "plan_key": "pro", "is_active": True, "onboarding_completed": True},
    ],
    "associes": [
        {"id": "associe-1", "id_sci": "sci-1", "user_id": "user-123", "nom": "Test User", "email": "test.user@sci.local", "part": 60, "role": "gerant"},
        {"id": "associe-1b", "id_sci": "sci-1", "user_id": "user-456", "nom": "Camille Bernard", "email": "camille.bernard@sci.local", "part": 40, "role": "associe"},
        {"id": "associe-2", "id_sci": "sci-2", "user_id": "user-123", "nom": "Test User", "email": "test.user@sci.local", "part": 100, "role": "associe"},
    ],
}


class FakeResult:
    def __init__(self, data: list[dict], error: str | None = None, count: int | None = None):
        self.data = data
        self.error = error
        self.count = len(data) if count is None else count


class _FakeNotProxy:
    """Proxy for `.not_.is_(...)` negation filter on FakeQuery."""

    def __init__(self, query: "FakeQuery"):
        self._query = query

    def is_(self, key: str, value: str) -> "FakeQuery":
        self._query._not_is_filters.append((key, value))
        return self._query


class FakeQuery:
    def __init__(self, store: dict[str, list[dict]], table_name: str):
        self._store = store
        self._table_name = table_name
        self._filters: list[tuple[str, str]] = []
        self._in_filters: list[tuple[str, set[str]]] = []
        self._gte_filters: list[tuple[str, str]] = []
        self._lte_filters: list[tuple[str, str]] = []
        self._lt_filters: list[tuple[str, str]] = []
        self._is_filters: list[tuple[str, str]] = []
        self._not_is_filters: list[tuple[str, str]] = []
        self._operation = "select"
        self._payload: list[dict] = []
        self._update_payload: dict = {}
        self._order_key: str | None = None
        self._order_desc: bool = False
        self._limit: int | None = None
        self.not_ = _FakeNotProxy(self)

    def select(self, *_args, **_kwargs) -> "FakeQuery":
        self._operation = "select"
        return self

    def insert(self, payload: dict | list[dict]) -> "FakeQuery":
        self._operation = "insert"
        if isinstance(payload, list):
            self._payload = [deepcopy(item) for item in payload]
        else:
            self._payload = [deepcopy(payload)]
        return self

    def upsert(self, payload: dict | list[dict], **_kwargs) -> "FakeQuery":
        self._operation = "insert"
        if isinstance(payload, list):
            self._payload = [deepcopy(item) for item in payload]
        else:
            self._payload = [deepcopy(payload)]
        return self

    def update(self, payload: dict) -> "FakeQuery":
        self._operation = "update"
        self._update_payload = deepcopy(payload)
        return self

    def delete(self) -> "FakeQuery":
        self._operation = "delete"
        return self

    def eq(self, key: str, value: object) -> "FakeQuery":
        self._filters.append((key, str(value)))
        return self

    def in_(self, key: str, values: list[object]) -> "FakeQuery":
        self._in_filters.append((key, {str(value) for value in values}))
        return self

    def gte(self, key: str, value: object) -> "FakeQuery":
        self._gte_filters.append((key, str(value)))
        return self

    def lte(self, key: str, value: object) -> "FakeQuery":
        self._lte_filters.append((key, str(value)))
        return self

    def lt(self, key: str, value: object) -> "FakeQuery":
        self._lt_filters.append((key, str(value)))
        return self

    def is_(self, key: str, value: str) -> "FakeQuery":
        self._is_filters.append((key, value))
        return self

    def order(self, key: str, *, desc: bool = False) -> "FakeQuery":
        self._order_key = key
        self._order_desc = desc
        return self

    def limit(self, count: int) -> "FakeQuery":
        self._limit = count
        return self

    def maybe_single(self) -> "FakeQuery":
        self._limit = 1
        return self

    def _matches(self, row: dict) -> bool:
        for key, value in self._filters:
            if str(row.get(key)) != value:
                return False
        for key, values in self._in_filters:
            if str(row.get(key)) not in values:
                return False
        for key, value in self._gte_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) < value:
                return False
        for key, value in self._lte_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) > value:
                return False
        for key, value in self._lt_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) >= value:
                return False
        for key, value in self._not_is_filters:
            if value == "null":
                if row.get(key) is None:
                    return False
            else:
                if row.get(key) is not None:
                    return False
        for key, value in self._is_filters:
            if value == "null":
                if row.get(key) is not None:
                    return False
            else:
                if row.get(key) is None:
                    return False
        return True

    def execute(self) -> FakeResult:
        rows = self._store.setdefault(self._table_name, [])

        if self._operation == "select":
            data = [deepcopy(row) for row in rows if self._matches(row)]
            if self._order_key:
                data.sort(
                    key=lambda r: r.get(self._order_key, ""),
                    reverse=self._order_desc,
                )
            if self._limit is not None:
                data = data[: self._limit]
            return FakeResult(data=data)

        if self._operation == "insert":
            inserted: list[dict] = []
            for payload in self._payload:
                payload.setdefault("id", str(uuid4()))
                rows.append(deepcopy(payload))
                inserted.append(deepcopy(payload))
            return FakeResult(data=inserted)

        if self._operation == "update":
            updated: list[dict] = []
            for row in rows:
                if self._matches(row):
                    row.update(deepcopy(self._update_payload))
                    updated.append(deepcopy(row))
            return FakeResult(data=updated)

        if self._operation == "delete":
            kept: list[dict] = []
            deleted: list[dict] = []
            for row in rows:
                if self._matches(row):
                    deleted.append(deepcopy(row))
                else:
                    kept.append(row)
            self._store[self._table_name] = kept
            return FakeResult(data=deleted)

        return FakeResult(data=[], error="unsupported operation")


class FakeAuthAdmin:
    def list_users(self, page=1, per_page=50):
        return [
            type("User", (), {
                "id": "user-123",
                "email": "test@sci.local",
                "created_at": "2026-01-01T00:00:00",
            })()
        ]

    def get_user_by_id(self, user_id):
        return type("UserResponse", (), {
            "user": type("User", (), {
                "id": user_id,
                "email": "test@sci.local",
                "created_at": "2026-01-01T00:00:00",
            })()
        })()


class FakeAuth:
    def __init__(self):
        self.admin = FakeAuthAdmin()


class _FakeBucket:
    """Minimal fake for ``client.storage.from_(<bucket>)``."""

    def __init__(self):
        self.removed: list[list[str]] = []
        self.uploaded: list[tuple[str, bytes]] = []

    def upload(self, path: str, content: bytes, **_kwargs):
        self.uploaded.append((path, content))

    def get_public_url(self, path: str) -> str:
        return f"https://storage.local/storage/v1/object/public/documents/{path}"

    def remove(self, paths: list[str]):
        self.removed.append(paths)


class _FakeStorageProxy:
    """Minimal fake for ``client.storage``."""

    def __init__(self):
        self._buckets: dict[str, _FakeBucket] = {}

    def from_(self, bucket_name: str) -> _FakeBucket:
        return self._buckets.setdefault(bucket_name, _FakeBucket())


class FakeSupabaseClient:
    def __init__(self):
        self.auth = FakeAuth()
        self.storage = _FakeStorageProxy()
        self.store: dict[str, list[dict]] = deepcopy(_INITIAL_STORE)

    def reset_store(self):
        """Reset store to initial seed data (called between tests)."""
        self.store = deepcopy(_INITIAL_STORE)
        self.storage = _FakeStorageProxy()

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self.store, name)


# ── Session-scoped fixtures (boot app + monkeypatch once per worker) ─────

@pytest.fixture(scope="session")
def _fake_storage_session():
    class FakeStorageService:
        def __init__(self):
            self.files: dict[str, bytes] = {}

        def reset(self):
            self.files.clear()

        async def create_bucket_if_not_exists(self) -> bool:
            return True

        async def upload_file(self, file_path: str, file_content: bytes, content_type: str = "application/pdf") -> str:
            self.files[file_path] = bytes(file_content)
            return f"https://storage.local/{file_path}"

        async def download_file(self, file_path: str) -> bytes:
            content = self.files.get(file_path)
            if content is None:
                raise Exception("file not found")
            return content

        async def delete_file(self, file_path: str) -> bool:
            self.files.pop(file_path, None)
            return True

        async def create_signed_url(self, file_path: str, expires_in: int = 300) -> str:
            if file_path not in self.files:
                raise Exception("file not found")
            return f"https://storage.local/signed/{file_path}?expires_in={expires_in}"

    return FakeStorageService()


@pytest.fixture(scope="session")
def _fake_supabase_session() -> FakeSupabaseClient:
    return FakeSupabaseClient()


@pytest.fixture(scope="session")
def _session_client(_fake_supabase_session, _fake_storage_session) -> TestClient:
    """Boot TestClient + monkeypatch once per xdist worker."""
    from app.api.v1 import associes, biens, charges, export, fiscalite, locataires, loyers, notifications, quitus, scis
    from app.api.v1 import dashboard, scis_biens, notification_preferences
    from app import main
    from app.api.v1 import auth, files, gdpr, stripe, onboarding, finances, admin
    from app.services import subscription_service
    from app.core import supabase_client as supabase_client_mod, paywall as paywall_mod

    fake_supabase = _fake_supabase_session
    fake_storage = _fake_storage_session

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(quitus, "storage_service", fake_storage)

        def fake_service():
            return fake_supabase
        fake_service.cache_clear = lambda: None

        for mod in [associes, biens, charges, export, fiscalite, loyers, locataires, scis,
                    notifications, dashboard, scis_biens, notification_preferences, quitus]:
            mp.setattr(mod, "get_supabase_service_client", fake_service, raising=False)
            mp.setattr(mod, "get_supabase_user_client", lambda request=None: fake_supabase, raising=False)

        def fake_anon():
            return fake_supabase
        fake_anon.cache_clear = lambda: None

        def fake_user_client(request=None):
            return fake_supabase

        for _mod in [auth, files, gdpr, stripe, subscription_service, onboarding, finances]:
            mp.setattr(_mod, "get_supabase_service_client", fake_service, raising=False)
            mp.setattr(_mod, "get_supabase_user_client", lambda request=None: fake_supabase, raising=False)
        mp.setattr(admin, "get_service_client", fake_service)
        mp.setattr(supabase_client_mod, "get_supabase_service_client", fake_service)
        mp.setattr(supabase_client_mod, "get_supabase_anon_client", fake_anon)
        mp.setattr(supabase_client_mod, "get_supabase_user_client", fake_user_client)
        mp.setattr(paywall_mod, "get_supabase_service_client", fake_service)

        mp.setattr(main, "shutdown_event", __import__("asyncio").Event())

        settings.allowed_hosts = ["testserver", "localhost", "*.gerersci.fr"]
        with TestClient(app, base_url="http://testserver") as test_client:
            yield test_client


# ── Function-scoped fixtures (exposed to tests, reset store each time) ───

@pytest.fixture(autouse=True)
def _reset_store(_fake_supabase_session, _fake_storage_session):
    """Reset the in-memory store before each test for isolation."""
    _fake_supabase_session.reset_store()
    _fake_storage_session.reset()


@pytest.fixture
def client(_session_client) -> TestClient:
    return _session_client


@pytest.fixture
def fake_supabase(_fake_supabase_session) -> FakeSupabaseClient:
    return _fake_supabase_session


@pytest.fixture
def fake_storage(_fake_storage_session):
    return _fake_storage_session


@pytest.fixture
def free_plan(fake_supabase: FakeSupabaseClient):
    """Clear subscriptions so user-123 falls back to free plan."""
    fake_supabase.store["subscriptions"] = []


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "user-123", "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
