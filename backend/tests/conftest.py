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


@pytest.fixture
def client() -> TestClient:
    # Temporarily allow testserver host
    original_allowed = settings.allowed_hosts if hasattr(settings, "allowed_hosts") else None
    settings.allowed_hosts = ["testserver", "localhost", "*.gerersci.fr"]
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    if original_allowed:
        settings.allowed_hosts = original_allowed


class FakeResult:
    def __init__(self, data: list[dict], error: str | None = None, count: int | None = None):
        self.data = data
        self.error = error
        self.count = len(data) if count is None else count


class FakeQuery:
    def __init__(self, store: dict[str, list[dict]], table_name: str):
        self._store = store
        self._table_name = table_name
        self._filters: list[tuple[str, str]] = []
        self._in_filters: list[tuple[str, set[str]]] = []
        self._gte_filters: list[tuple[str, str]] = []
        self._lte_filters: list[tuple[str, str]] = []
        self._is_filters: list[tuple[str, str]] = []
        self._operation = "select"
        self._payload: list[dict] = []
        self._update_payload: dict = {}
        self._order_key: str | None = None
        self._order_desc: bool = False
        self._limit: int | None = None

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


class FakeSupabaseClient:
    def __init__(self):
        self.auth = FakeAuth()
        self.store: dict[str, list[dict]] = {
            "sci": [
                {
                    "id": "sci-1",
                    "nom": "SCI Mosa Belleville",
                    "siren": "123456789",
                    "regime_fiscal": "IR",
                },
                {
                    "id": "sci-2",
                    "nom": "SCI Horizon Lyon",
                    "siren": "987654321",
                    "regime_fiscal": "IS",
                },
            ],
            "biens": [],
            "locataires": [],
            "loyers": [],
            "charges": [],
            "fiscalite": [],
            "admins": [
                {"user_id": "user-123"},
            ],
            "subscriptions": [],
            "associes": [
                {
                    "id": "associe-1",
                    "id_sci": "sci-1",
                    "user_id": "user-123",
                    "nom": "Test User",
                    "email": "test.user@sci.local",
                    "part": 60,
                    "role": "gerant",
                },
                {
                    "id": "associe-1b",
                    "id_sci": "sci-1",
                    "user_id": "user-456",
                    "nom": "Camille Bernard",
                    "email": "camille.bernard@sci.local",
                    "part": 40,
                    "role": "associe",
                },
                {
                    "id": "associe-2",
                    "id_sci": "sci-2",
                    "user_id": "user-123",
                    "nom": "Test User",
                    "email": "test.user@sci.local",
                    "part": 100,
                    "role": "associe",
                },
            ],
        }

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self.store, name)


@pytest.fixture
def fake_storage():
    class FakeStorageService:
        def __init__(self):
            self.files: dict[str, bytes] = {}

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


@pytest.fixture
def fake_supabase() -> FakeSupabaseClient:
    return FakeSupabaseClient()


@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch: pytest.MonkeyPatch, fake_supabase: FakeSupabaseClient, fake_storage):
    from app.api.v1 import associes, biens, charges, export, fiscalite, locataires, loyers, notifications, quitus, scis
    from app.api.v1 import dashboard, scis_biens, notification_preferences
    from app import main
    from app.api.v1 import auth, files, gdpr, stripe, onboarding, finances, admin
    from app.services import subscription_service
    from app.core import supabase_client as supabase_client_mod, paywall as paywall_mod

    monkeypatch.setattr(quitus, "storage_service", fake_storage)

    # Patch get_supabase_service_client everywhere it's used
    # Must have cache_clear() to satisfy shutdown handler
    def fake_service():
        return fake_supabase
    fake_service.cache_clear = lambda: None

    # Patch all 12 API modules that now use get_supabase_service_client via _get_client()
    for mod in [associes, biens, charges, export, fiscalite, loyers, locataires, scis,
                notifications, dashboard, scis_biens, notification_preferences]:
        monkeypatch.setattr(mod, "get_supabase_service_client", fake_service)

    def fake_anon():
        return fake_supabase
    fake_anon.cache_clear = lambda: None

    monkeypatch.setattr(auth, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(files, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(gdpr, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(stripe, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(subscription_service, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(onboarding, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(finances, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(admin, "get_service_client", fake_service)
    monkeypatch.setattr(supabase_client_mod, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(supabase_client_mod, "get_supabase_anon_client", fake_anon)
    monkeypatch.setattr(paywall_mod, "get_supabase_service_client", fake_service)

    monkeypatch.setattr(main, "shutdown_event", __import__("asyncio").Event())


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "user-123", "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
