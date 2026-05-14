"""Tests for security headers, especially Content-Security-Policy.

Regression test for P0: after Stripe checkout, browser blocked POST to
https://api.gerersci.fr/api/v1/scis/ with "Failed to fetch" because the
CSP connect-src did not include the public API origin.

Uses a fresh TestClient (no supabase mocks) so the test is independent of
the heavier _session_client fixture in conftest.py.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def app_client() -> TestClient:
    from app.main import app
    return TestClient(app)


def _csp(client: TestClient) -> str:
    resp = client.get("/health/live")
    assert resp.status_code == 200
    csp = resp.headers.get("Content-Security-Policy")
    assert csp, "Content-Security-Policy header is missing"
    return csp


def _connect_src(csp: str) -> str:
    for directive in csp.split(";"):
        directive = directive.strip()
        if directive.startswith("connect-src "):
            return directive[len("connect-src "):]
    raise AssertionError(f"connect-src directive missing from CSP: {csp}")


def test_csp_header_present(app_client: TestClient):
    csp = _csp(app_client)
    # Core hardening directives we never want to lose.
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp


def test_csp_connect_src_includes_public_api_origin(
    app_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """The browser must be allowed to fetch the public API origin.

    Without this, POST /api/v1/scis/ from the SPA fails with 'Failed to fetch'
    and the request never reaches the backend (no 401, no log entry).
    """
    # Force production-style API URL and rebuild the client to pick it up.
    monkeypatch.setenv("VITE_API_URL", "https://api.gerersci.fr")
    from app.main import app
    fresh = TestClient(app)
    csp = _csp(fresh)
    connect_src = _connect_src(csp)
    assert "https://api.gerersci.fr" in connect_src, (
        f"connect-src missing public API origin: {connect_src}"
    )


def test_csp_connect_src_includes_stripe_and_analytics(app_client: TestClient):
    csp = _csp(app_client)
    connect_src = _connect_src(csp)
    assert "stripe.com" in connect_src
    assert "analytics.gerersci.fr" in connect_src or "matomo" in connect_src.lower()


def test_csp_script_src_allows_stripe(app_client: TestClient):
    csp = _csp(app_client)
    # Stripe.js must be loadable from js.stripe.com.
    assert "https://js.stripe.com" in csp


def test_security_headers_complete(app_client: TestClient):
    resp = app_client.get("/health/live")
    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in headers
    assert "Referrer-Policy" in headers
