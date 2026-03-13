import pytest

from app.services.auth_service import MagicLinkService


class _FakeAdminLinkResult:
    def __init__(self, email):
        self.properties = type("Props", (), {"action_link": f"https://example.com/auth?token=abc&email={email}"})()


class _FakeAdmin:
    """Mimics client.auth.admin with generate_link()."""

    def generate_link(self, payload):
        email = payload.get("email", "")
        if email == "error@example.com":
            raise RuntimeError("otp failed")
        return _FakeAdminLinkResult(email)


class _FakeAuthClient:
    def __init__(self):
        self.auth = self
        self.admin = _FakeAdmin()

    def sign_in_with_otp(self, payload):
        if payload.get("email") == "error@example.com":
            raise RuntimeError("otp failed")
        return {"otp": "sent"}

    def update_user(self, payload):
        if payload.get("user_metadata", {}).get("force_error"):
            raise RuntimeError("update failed")
        return {"updated": True}

    def get_user(self, access_token):
        if access_token == "bad-token":
            raise RuntimeError("invalid token")
        return {"id": "user-123"}

    def refresh_session(self, refresh_token):
        if refresh_token == "bad-refresh":
            raise RuntimeError("refresh failed")
        return {"access_token": "new-token"}


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.create_client", lambda *_args, **_kwargs: _FakeAuthClient())
    # Mock email_service.send_magic_link so it doesn't actually send emails
    async def _noop_send(email, link):
        pass
    monkeypatch.setattr("app.services.auth_service.email_service.send_magic_link", _noop_send)
    return MagicLinkService()


@pytest.mark.asyncio
async def test_send_magic_link_success(service):
    response = await service.send_magic_link("user@example.com")
    assert response["success"] is True
    assert response["message"] == "Magic link sent to email"


@pytest.mark.asyncio
async def test_send_magic_link_failure(service):
    response = await service.send_magic_link("error@example.com")
    assert response["success"] is False
    assert "otp failed" in response["message"]
    assert response["data"] is None


@pytest.mark.asyncio
async def test_create_user_from_magic_link_with_metadata(service):
    response = await service.create_user_from_magic_link(
        "user@example.com", user_metadata={"role": "manager"}
    )
    assert response["success"] is True
    assert response["data"] == {"updated": True}


@pytest.mark.asyncio
async def test_create_user_from_magic_link_without_metadata(service):
    response = await service.create_user_from_magic_link("user@example.com")
    assert response == {"success": True, "message": "User authenticated"}


@pytest.mark.asyncio
async def test_create_user_from_magic_link_failure(service):
    response = await service.create_user_from_magic_link(
        "user@example.com", user_metadata={"force_error": True}
    )
    assert response["success"] is False
    assert "update failed" in response["message"]


@pytest.mark.asyncio
async def test_get_user_session_success(service):
    response = await service.get_user_session("good-token")
    assert response == {"id": "user-123"}


@pytest.mark.asyncio
async def test_get_user_session_failure(service):
    response = await service.get_user_session("bad-token")
    assert response is None


@pytest.mark.asyncio
async def test_refresh_session_success(service):
    response = await service.refresh_session("good-refresh")
    assert response == {"access_token": "new-token"}


@pytest.mark.asyncio
async def test_refresh_session_failure(service):
    response = await service.refresh_session("bad-refresh")
    assert response is None
