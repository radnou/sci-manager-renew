from app.api.v1 import auth


def test_send_magic_link_success(client, monkeypatch):
    async def fake_send_magic_link(email: str):
        return {"success": True, "message": f"ok {email}"}

    monkeypatch.setattr(auth.magic_link_service, "send_magic_link", fake_send_magic_link)

    response = client.post("/api/v1/auth/magic-link/send", json={"email": "user@example.com"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "Magic link sent to user@example.com" in payload["message"]


def test_send_magic_link_business_failure(client, monkeypatch):
    async def fake_send_magic_link(_email: str):
        return {"success": False, "message": "Email not allowed"}

    monkeypatch.setattr(auth.magic_link_service, "send_magic_link", fake_send_magic_link)

    response = client.post("/api/v1/auth/magic-link/send", json={"email": "blocked@example.com"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "Email not allowed"


def test_send_magic_link_internal_error(client, monkeypatch):
    async def fake_send_magic_link(_email: str):
        raise RuntimeError("provider down")

    monkeypatch.setattr(auth.magic_link_service, "send_magic_link", fake_send_magic_link)

    response = client.post("/api/v1/auth/magic-link/send", json={"email": "user@example.com"})
    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "external_service_error"
    assert "Failed to send magic link" in payload["error"]


def test_verify_magic_link_success(client, monkeypatch):
    async def fake_verify_magic_link(token: str):
        return {"success": token == "valid-token", "message": "ok"}

    monkeypatch.setattr(auth.magic_link_service, "verify_magic_link", fake_verify_magic_link)

    response = client.post("/api/v1/auth/magic-link/verify", params={"token": "valid-token"})
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"success": True, "message": "Magic link verified"}


def test_verify_magic_link_invalid_token(client, monkeypatch):
    async def fake_verify_magic_link(_token: str):
        return {"success": False, "message": "Invalid token"}

    monkeypatch.setattr(auth.magic_link_service, "verify_magic_link", fake_verify_magic_link)

    response = client.post("/api/v1/auth/magic-link/verify", params={"token": "invalid"})
    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "authentication_error"
    assert payload["error"] == "Invalid token"


def test_logout_success(client, monkeypatch):
    async def fake_sign_out(access_token: str):
        return {"success": bool(access_token), "message": "ok"}

    monkeypatch.setattr(auth.magic_link_service, "sign_out", fake_sign_out)

    response = client.post("/api/v1/auth/logout", params={"access_token": "token-123"})
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"success": True, "message": "Signed out successfully"}


def test_logout_failure(client, monkeypatch):
    async def fake_sign_out(_access_token: str):
        return {"success": False, "message": "logout failed"}

    monkeypatch.setattr(auth.magic_link_service, "sign_out", fake_sign_out)

    response = client.post("/api/v1/auth/logout", params={"access_token": "token-123"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "logout failed"
