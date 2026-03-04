import pytest
from fastapi.testclient import TestClient

# when running inside backend directory, import from app package directly
from app.main import app

# the client to interact with HTTP endpoints
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# fake Supabase client used by service layer tests and routers
class FakeTable:
    def __init__(self, store):
        self._store = store

    def select(self, *args, **kwargs):
        class Query:
            def __init__(self, store):
                self.data = store
                self.error = None

            def execute(self):
                return self

        return Query(self._store)

    def insert(self, data):
        # simulate database auto-generated id if not provided
        obj = data.copy()
        if "id" not in obj:
            from uuid import uuid4

            obj["id"] = uuid4()
        self._store.append(obj)

        class Query:
            def __init__(self, d):
                self.data = [d]
                self.error = None

            def execute(self):
                return self

        return Query(obj)


class FakeClient:
    def __init__(self):
        self.tables = {}

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = []
        return FakeTable(self.tables[name])


@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch):
    """Automatically replace Supabase client with a fake implementation."""
    from app.core import supabase_client

    fake = FakeClient()
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: fake)
    return fake
