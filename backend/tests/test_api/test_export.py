"""Tests for export API endpoints — CSV export for loyers and biens."""

from __future__ import annotations


def test_export_loyers_csv_returns_csv(client, auth_headers, fake_supabase, monkeypatch):
    """Export loyers returns a valid CSV response."""
    from app.api.v1 import export

    monkeypatch.setattr(export, "create_client", lambda *a, **kw: fake_supabase)

    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


def test_export_biens_csv_returns_csv(client, auth_headers, fake_supabase, monkeypatch):
    """Export biens returns a valid CSV response."""
    from app.api.v1 import export

    monkeypatch.setattr(export, "create_client", lambda *a, **kw: fake_supabase)

    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


def test_export_loyers_csv_unauthorized(client):
    """Request without auth returns 401."""
    resp = client.get("/api/v1/export/loyers/csv")
    assert resp.status_code in (401, 403)


def test_export_biens_csv_unauthorized(client):
    """Request without auth returns 401."""
    resp = client.get("/api/v1/export/biens/csv")
    assert resp.status_code in (401, 403)


def test_get_user_sci_ids_returns_ids(fake_supabase):
    """Unit test _get_user_sci_ids helper directly."""
    from app.api.v1.export import _get_user_sci_ids

    sci_ids = _get_user_sci_ids(fake_supabase, "user-123")
    assert "sci-1" in sci_ids
    assert "sci-2" in sci_ids


def test_get_user_sci_ids_empty_for_unknown_user(fake_supabase):
    """Unknown user returns empty list."""
    from app.api.v1.export import _get_user_sci_ids

    sci_ids = _get_user_sci_ids(fake_supabase, "unknown-user")
    assert sci_ids == []


def test_get_user_sci_ids_filters_none_values(fake_supabase):
    """Rows with no id_sci are filtered out."""
    from app.api.v1.export import _get_user_sci_ids

    fake_supabase.store["associes"].append(
        {"id": "a-x", "id_sci": None, "user_id": "user-123", "role": "associe"}
    )
    sci_ids = _get_user_sci_ids(fake_supabase, "user-123")
    assert None not in sci_ids
    # Original 2 SCIs remain
    assert "sci-1" in sci_ids
    assert "sci-2" in sci_ids
