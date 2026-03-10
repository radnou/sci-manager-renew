from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app

# Override settings for tests
settings.cors_origins = ["http://testserver"]


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


class FakeSupabaseClient:
    def __init__(self):
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
    from app.api.v1 import associes, biens, charges, fiscalite, locataires, loyers, notifications, quitus, scis
    from app import main
    from app.api.v1 import gdpr, stripe
    from app.services import subscription_service

    monkeypatch.setattr(
        associes,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        biens,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        charges,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        fiscalite,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        loyers,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        locataires,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        scis,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        notifications,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(quitus, "storage_service", fake_storage)
    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_supabase)
    monkeypatch.setattr(stripe, "get_supabase_service_client", lambda: fake_supabase)
    monkeypatch.setattr(subscription_service, "get_supabase_service_client", lambda: fake_supabase)
    monkeypatch.setattr(main, "shutdown_event", __import__("asyncio").Event())


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "user-123", "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
