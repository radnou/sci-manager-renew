import jwt

from app.core.config import settings


def test_invalid_token_returns_401(client):
    response = client.get(
        "/api/v1/biens/",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401


def test_token_without_sub_returns_401(client):
    token = jwt.encode({"role": "authenticated"}, settings.supabase_jwt_secret, algorithm="HS256")
    response = client.get(
        "/api/v1/biens/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
