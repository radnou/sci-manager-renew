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
    def __init__(self, data: list[dict], error: str | None = None):
        self.data = data
        self.error = error


class FakeQuery:
    def __init__(self, store: dict[str, list[dict]], table_name: str):
        self._store = store
        self._table_name = table_name
        self._filters: list[tuple[str, str]] = []
        self._in_filters: list[tuple[str, set[str]]] = []
        self._gte_filters: list[tuple[str, str]] = []
        self._lte_filters: list[tuple[str, str]] = []
        self._operation = "select"
        self._payload: list[dict] = []
        self._update_payload: dict = {}

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
        return True

    def execute(self) -> FakeResult:
        rows = self._store.setdefault(self._table_name, [])

        if self._operation == "select":
            data = [deepcopy(row) for row in rows if self._matches(row)]
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
            "biens": [],
            "loyers": [],
            "associes": [
                {
                    "id": "associe-1",
                    "id_sci": "sci-1",
                    "user_id": "user-123",
                    "nom": "Test User",
                    "part": 100,
                },
                {
                    "id": "associe-2",
                    "id_sci": "sci-2",
                    "user_id": "user-123",
                    "nom": "Test User",
                    "part": 100,
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

    return FakeStorageService()


@pytest.fixture
def fake_supabase() -> FakeSupabaseClient:
    return FakeSupabaseClient()


@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch: pytest.MonkeyPatch, fake_supabase: FakeSupabaseClient, fake_storage):
    from app.api.v1 import biens, loyers, quitus

    monkeypatch.setattr(
        biens,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(
        loyers,
        "create_client",
        lambda *_args, **_kwargs: fake_supabase,
    )
    monkeypatch.setattr(quitus, "storage_service", fake_storage)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "user-123", "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
