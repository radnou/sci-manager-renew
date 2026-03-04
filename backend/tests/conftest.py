import pytest
from fastapi.testclient import TestClient

# when running inside backend directory, import from app package directly
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
