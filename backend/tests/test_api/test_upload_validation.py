"""Tests for upload validation in document upload endpoint."""

from __future__ import annotations

import io

import pytest

# Valid UUID for sci_id (router requires UUID)
SCI_UUID = "11111111-1111-1111-1111-111111111111"
BIEN_ID = "bien-abc"
DOCS_URL = f"/api/v1/scis/{SCI_UUID}/biens/{BIEN_ID}/documents"

GERANT_ASSOCIE = {
    "id": "associe-uuid-1",
    "id_sci": SCI_UUID,
    "user_id": "user-123",
    "nom": "Test User",
    "email": "test.user@sci.local",
    "part": 100,
    "role": "gerant",
}

ACTIVE_SUB = {
    "user_id": "user-123",
    "plan_key": "pro",
    "status": "active",
}

BIEN_ROW = {
    "id": BIEN_ID,
    "id_sci": SCI_UUID,
    "adresse": "1 rue Test",
}


def _setup(fake_supabase):
    """Seed the store with the minimal data for upload tests."""
    fake_supabase.store["subscriptions"] = [ACTIVE_SUB]
    fake_supabase.store["associes"] = [GERANT_ASSOCIE]
    fake_supabase.store.setdefault("biens", [])
    if not any(b["id"] == BIEN_ID for b in fake_supabase.store["biens"]):
        fake_supabase.store["biens"].append(dict(BIEN_ROW))


def test_upload_rejects_oversized_file(client, auth_headers, fake_supabase):
    """Files over 10MB should be rejected."""
    _setup(fake_supabase)

    large_content = b"x" * (10 * 1024 * 1024 + 1)

    response = client.post(
        DOCS_URL,
        headers=auth_headers,
        files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
        data={"nom": "Test Doc", "categorie": "autre"},
    )
    assert response.status_code == 400
    assert "volumineux" in response.json()["error"].lower()


def test_upload_rejects_forbidden_extension(client, auth_headers, fake_supabase):
    """Dangerous extensions like .exe should be rejected."""
    _setup(fake_supabase)

    response = client.post(
        DOCS_URL,
        headers=auth_headers,
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        data={"nom": "Test Doc", "categorie": "autre"},
    )
    assert response.status_code == 400
    assert "non autorisée" in response.json()["error"].lower()


def test_upload_rejects_empty_file(client, auth_headers, fake_supabase):
    """Empty files should be rejected."""
    _setup(fake_supabase)

    response = client.post(
        DOCS_URL,
        headers=auth_headers,
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        data={"nom": "Test Doc", "categorie": "autre"},
    )
    assert response.status_code == 400
    assert "vide" in response.json()["error"].lower()


def test_upload_rejects_mismatched_magic_bytes(client, auth_headers, fake_supabase):
    """A .pdf file that starts with PNG magic bytes should be rejected."""
    _setup(fake_supabase)

    png_content = b"\x89PNG\r\n\x1a\n" + b"x" * 100

    response = client.post(
        DOCS_URL,
        headers=auth_headers,
        files={"file": ("fake.pdf", io.BytesIO(png_content), "application/pdf")},
        data={"nom": "Test Doc", "categorie": "autre"},
    )
    assert response.status_code == 400
    assert "ne correspond pas" in response.json()["error"].lower()


def test_upload_rejects_no_extension(client, auth_headers, fake_supabase):
    """A file without extension should be rejected."""
    _setup(fake_supabase)

    response = client.post(
        DOCS_URL,
        headers=auth_headers,
        files={"file": ("noextension", io.BytesIO(b"some content"), "application/octet-stream")},
        data={"nom": "Test Doc", "categorie": "autre"},
    )
    assert response.status_code == 400
    assert "non autorisée" in response.json()["error"].lower()
