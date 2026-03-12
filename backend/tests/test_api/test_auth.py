from unittest.mock import MagicMock, patch

import stripe

from app.api.v1 import auth


# ── /activate endpoint tests ──────────────────────────────────────────────


def test_activate_missing_session_id(client):
    response = client.get("/api/v1/auth/activate")
    assert response.status_code == 400


def test_activate_invalid_session_id(client):
    response = client.get("/api/v1/auth/activate?session_id=invalid")
    assert response.status_code == 400


def test_activate_unpaid_session(client, monkeypatch):
    """Stripe session exists but payment_status != paid."""
    fake_session = MagicMock()
    fake_session.payment_status = "unpaid"

    with patch("stripe.checkout.Session.retrieve", return_value=fake_session):
        response = client.get("/api/v1/auth/activate?session_id=cs_test_123")
    assert response.status_code == 400
    assert "Payment not completed" in response.json()["error"]


def test_activate_no_email_in_session(client):
    """Paid session but no customer email."""
    fake_session = MagicMock()
    fake_session.payment_status = "paid"
    fake_session.customer_details = None
    fake_session.metadata = {}

    with patch("stripe.checkout.Session.retrieve", return_value=fake_session):
        response = client.get("/api/v1/auth/activate?session_id=cs_test_123")
    assert response.status_code == 400
    assert "No email" in response.json()["error"]


def test_activate_user_not_found(client):
    """Paid session with email but user not yet created in Supabase."""
    fake_session = MagicMock()
    fake_session.payment_status = "paid"
    fake_session.customer_details.email = "buyer@example.com"
    fake_session.metadata = {"plan_key": "pro"}

    with (
        patch("stripe.checkout.Session.retrieve", return_value=fake_session),
        patch("app.api.v1.auth._find_user_by_email", return_value=None),
    ):
        response = client.get("/api/v1/auth/activate?session_id=cs_test_123")
    assert response.status_code == 503
    assert "not yet created" in response.json()["error"]


def test_activate_replay_blocked(client):
    """Anti-replay: second activation of same session_id is rejected."""
    fake_session = MagicMock()
    fake_session.payment_status = "paid"
    fake_session.customer_details.email = "buyer@example.com"
    fake_session.metadata = {"plan_key": "starter"}

    fake_upsert_result = MagicMock()
    fake_upsert_result.data = []  # empty = duplicate ignored

    fake_table = MagicMock()
    fake_table.upsert.return_value.execute.return_value = fake_upsert_result

    fake_client = MagicMock()
    fake_client.table.return_value = fake_table

    with (
        patch("stripe.checkout.Session.retrieve", return_value=fake_session),
        patch("app.api.v1.auth._find_user_by_email", return_value="user-uuid-123"),
        patch("app.api.v1.auth.get_supabase_service_client", return_value=fake_client),
    ):
        response = client.get("/api/v1/auth/activate?session_id=cs_test_123")
    assert response.status_code == 401
    assert "already been used" in response.json()["error"]


def test_activate_success(client):
    """Happy path: valid paid session, user found, first activation."""
    fake_session = MagicMock()
    fake_session.payment_status = "paid"
    fake_session.customer_details.email = "buyer@example.com"
    fake_session.metadata = {"plan_key": "pro"}

    fake_upsert_result = MagicMock()
    fake_upsert_result.data = [{"session_id": "cs_test_123", "user_id": "user-uuid-123"}]

    fake_table = MagicMock()
    fake_table.upsert.return_value.execute.return_value = fake_upsert_result

    fake_link_props = MagicMock()
    fake_link_props.hashed_token = "hashed-token-abc"
    fake_link_result = MagicMock()
    fake_link_result.properties = fake_link_props

    fake_client = MagicMock()
    fake_client.table.return_value = fake_table
    fake_client.auth.admin.generate_link.return_value = fake_link_result

    with (
        patch("stripe.checkout.Session.retrieve", return_value=fake_session),
        patch("app.api.v1.auth._find_user_by_email", return_value="user-uuid-123"),
        patch("app.api.v1.auth.get_supabase_service_client", return_value=fake_client),
    ):
        response = client.get("/api/v1/auth/activate?session_id=cs_test_123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_hash"] == "hashed-token-abc"
    assert payload["type"] == "magiclink"
    assert payload["plan_key"] == "pro"


# ── Magic link endpoint tests ─────────────────────────────────────────────


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


# ── /forgot-password endpoint tests ──────────────────────────────────────


def test_forgot_password_requires_email(client):
    response = client.post("/api/v1/auth/forgot-password", json={})
    assert response.status_code == 422


def test_forgot_password_returns_success_always(client):
    """Always returns success to prevent email enumeration."""
    fake_client = MagicMock()
    with patch("app.api.v1.auth.get_supabase_service_client", return_value=fake_client):
        response = client.post("/api/v1/auth/forgot-password", json={"email": "anyone@test.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "reset link" in data["message"].lower()


def test_forgot_password_returns_success_even_on_error(client):
    """Anti-enumeration: returns 200 even when Supabase raises an error."""
    fake_client = MagicMock()
    fake_client.auth.reset_password_email.side_effect = Exception("user not found")
    with patch("app.api.v1.auth.get_supabase_service_client", return_value=fake_client):
        response = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@test.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_forgot_password_invalid_email_format(client):
    response = client.post("/api/v1/auth/forgot-password", json={"email": "not-an-email"})
    assert response.status_code == 422
