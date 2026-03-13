from __future__ import annotations

import pytest
from types import SimpleNamespace

from tests.conftest import FakeSupabaseClient


@pytest.fixture(autouse=True)
def _restore_table_method(fake_supabase: FakeSupabaseClient):
    """Restore .table() after tests that monkeypatch it."""
    original = FakeSupabaseClient.table
    yield
    fake_supabase.table = original.__get__(fake_supabase, FakeSupabaseClient)


class FakeAuthAdmin:
    def __init__(self):
        self.deleted_user_id: str | None = None

    def get_user_by_id(self, user_id: str):
        return SimpleNamespace(
            user=SimpleNamespace(
                id=user_id,
                email="user@example.test",
                created_at="2026-01-01T00:00:00Z",
                email_confirmed_at="2026-01-01T00:01:00Z",
                last_sign_in_at="2026-03-01T10:00:00Z",
            )
        )

    def delete_user(self, user_id: str):
        self.deleted_user_id = user_id


def build_gdpr_client(fake_supabase):
    fake_supabase.auth = SimpleNamespace(admin=FakeAuthAdmin())
    fake_supabase.store.update(
        {
            "associes": [
                {
                    "id": "associe-1",
                    "id_sci": "sci-1",
                    "user_id": "user-123",
                    "nom": "Test User",
                    "part": 100,
                }
            ],
            "biens": [
                {
                    "id": "bien-1",
                    "id_sci": "sci-1",
                    "adresse": "10 rue de Test",
                    "ville": "Paris",
                }
            ],
            "loyers": [
                {
                    "id": "loyer-1",
                    "id_bien": "bien-1",
                    "id_sci": "sci-1",
                    "date_loyer": "2026-03-01",
                    "montant": 1200,
                    "statut": "en_attente",
                }
            ],
            "charges": [
                {
                    "id": "charge-1",
                    "id_bien": "bien-1",
                    "type_charge": "copro",
                    "montant": 120,
                    "date_paiement": "2026-03-05",
                }
            ],
            "fiscalite": [
                {
                    "id": "fisc-1",
                    "id_sci": "sci-1",
                    "annee": 2026,
                    "total_revenus": 14400,
                    "total_charges": 1440,
                    "resultat_fiscal": 12960,
                }
            ],
            "subscriptions": [
                {
                    "id": "sub-1",
                    "user_id": "user-123",
                    "stripe_customer_id": "cus_123",
                    "status": "active",
                }
            ],
            "gdpr_exports": [],
        }
    )
    return fake_supabase


def test_data_export_returns_signed_url(client, auth_headers, monkeypatch, fake_storage, fake_supabase):
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)

    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    response = client.get("/api/v1/gdpr/data-export", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["export_url"].startswith("https://storage.local/signed/gdpr/user-123/")
    assert payload["expires_at"]
    assert len(fake_client.store["gdpr_exports"]) == 1


def test_account_delete_cleans_user_data(client, auth_headers, monkeypatch, fake_storage, fake_supabase):
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    fake_client.store["gdpr_exports"] = [
        {
            "id": "exp-1",
            "user_id": "user-123",
            "file_path": "gdpr/user-123/export-1.json",
            "size_bytes": 2,
            "expires_at": "2026-03-05T12:00:00Z",
        }
    ]

    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    fake_storage.files["gdpr/user-123/export-1.json"] = b"{}"

    response = client.delete("/api/v1/gdpr/account", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True

    assert fake_client.auth.admin.deleted_user_id == "user-123"
    assert fake_client.store["associes"] == []
    assert fake_client.store["biens"] == []
    assert fake_client.store["loyers"] == []
    assert fake_client.store["charges"] == []
    assert fake_client.store["fiscalite"] == []
    assert fake_client.store["gdpr_exports"] == []
    assert fake_storage.files == {}

    subscriptions = fake_client.store["subscriptions"]
    assert len(subscriptions) == 1
    assert subscriptions[0]["status"] == "deleted"
    assert subscriptions[0]["stripe_customer_id"] is None


def test_data_export_failure_returns_structured_error(client, auth_headers, monkeypatch):
    from app.api.v1 import gdpr

    def fake_client():
        raise RuntimeError("supabase unavailable")

    monkeypatch.setattr(gdpr, "get_supabase_service_client", fake_client)

    response = client.get("/api/v1/gdpr/data-export", headers=auth_headers)

    assert response.status_code == 500
    payload = response.json()
    assert payload["code"] == "gdpr_export_failed"
    assert payload["error"] == "Échec de l'export des données."


# ── data-summary endpoint ──────────────────────────────────────────────


def test_data_summary_returns_counts(client, auth_headers, monkeypatch, fake_supabase):
    """GET /data-summary returns user info and correct data counts."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)

    response = client.get("/api/v1/gdpr/data-summary", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "user-123"
    assert payload["email"] == "user@example.test"
    assert payload["created_at"] == "2026-01-01T00:00:00Z"

    summary = payload["data_summary"]
    assert summary["sci_count"] == 1
    assert summary["biens_count"] == 1
    assert summary["loyers_count"] == 1
    assert summary["associes_count"] == 1


def test_data_summary_empty_user(client, auth_headers, monkeypatch, fake_supabase):
    """GET /data-summary for user with no data returns zero counts."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    # Clear all user-related data
    fake_client.store["associes"] = []
    fake_client.store["biens"] = []
    fake_client.store["loyers"] = []

    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)

    response = client.get("/api/v1/gdpr/data-summary", headers=auth_headers)

    assert response.status_code == 200
    summary = response.json()["data_summary"]
    assert summary["sci_count"] == 0
    assert summary["biens_count"] == 0
    assert summary["loyers_count"] == 0


def test_data_summary_failure_returns_structured_error(client, auth_headers, monkeypatch):
    """GET /data-summary returns 500 with code when supabase fails."""
    from app.api.v1 import gdpr

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(gdpr, "get_supabase_service_client", boom)

    response = client.get("/api/v1/gdpr/data-summary", headers=auth_headers)

    assert response.status_code == 500
    payload = response.json()
    assert payload["code"] == "gdpr_summary_failed"


# ── data-export: gdpr_exports insert failure (lines 156-158) ──────────


def test_data_export_continues_when_gdpr_exports_insert_fails(
    client, auth_headers, monkeypatch, fake_storage, fake_supabase
):
    """Export succeeds even when tracking metadata insert raises."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    # Make gdpr_exports insert raise
    original_table = fake_client.table

    def table_with_error(name):
        query = original_table(name)
        if name == "gdpr_exports":
            original_insert = query.insert

            def failing_insert(payload):
                result = original_insert(payload)
                original_execute = result.execute

                def exploding_execute():
                    raise RuntimeError("insert tracking failed")

                result.execute = exploding_execute
                return result

            query.insert = failing_insert
        return query

    fake_client.table = table_with_error

    response = client.get("/api/v1/gdpr/data-export", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["export_url"] is not None


# ── account delete: storage cleanup exception (lines 303-314) ─────────


def test_account_delete_continues_when_storage_cleanup_fails(
    client, auth_headers, monkeypatch, fake_storage, fake_supabase
):
    """Account delete succeeds even when document storage cleanup raises (outer except, lines 313-314)."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    fake_client.store["documents_bien"] = [
        {
            "id": "doc-1",
            "id_bien": "bien-1",
            "url": "https://storage.local/storage/v1/object/public/documents/sci-1/doc.pdf",
        }
    ]
    fake_client.store["baux"] = []
    fake_client.store["locataires"] = []

    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    # Make only the FIRST documents_bien call (select in try block) raise,
    # while the SECOND call (delete outside try) works normally.
    original_table = fake_client.table
    doc_call_count = {"n": 0}

    def table_raising_first_documents_bien(name):
        if name == "documents_bien":
            doc_call_count["n"] += 1
            if doc_call_count["n"] == 1:
                raise RuntimeError("storage query failed")
        return original_table(name)

    fake_client.table = table_raising_first_documents_bien

    response = client.delete("/api/v1/gdpr/account", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert fake_client.auth.admin.deleted_user_id == "user-123"


def test_account_delete_continues_when_individual_doc_storage_remove_fails(
    client, auth_headers, monkeypatch, fake_storage, fake_supabase
):
    """Account delete succeeds even when individual doc remove raises (inner except, lines 311-312)."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    fake_client.store["documents_bien"] = [
        {
            "id": "doc-1",
            "id_bien": "bien-1",
            "url": "https://storage.local/storage/v1/object/public/documents/sci-1/doc.pdf",
        }
    ]
    fake_client.store["baux"] = []
    fake_client.store["locataires"] = []

    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    # Make storage.from_("documents").remove() raise
    bucket = fake_client.storage.from_("documents")

    def exploding_remove(paths):
        raise RuntimeError("storage remove failed")

    bucket.remove = exploding_remove

    response = client.delete("/api/v1/gdpr/account", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True


# ── account delete: subscription anonymization exception (lines 345-347) ──


def test_account_delete_continues_when_subscription_anonymize_fails(
    client, auth_headers, monkeypatch, fake_storage, fake_supabase
):
    """Account delete succeeds even when subscription update raises."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    original_table = fake_client.table

    def table_raising_on_subscriptions(name):
        query = original_table(name)
        if name == "subscriptions":
            original_update = query.update

            def failing_update(payload):
                result = original_update(payload)
                original_execute = result.execute

                def exploding_execute():
                    raise RuntimeError("subscription update failed")

                result.execute = exploding_execute
                return result

            query.update = failing_update
        return query

    fake_client.table = table_raising_on_subscriptions

    response = client.delete("/api/v1/gdpr/account", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert fake_client.auth.admin.deleted_user_id == "user-123"


# ── account delete: gdpr exports cleanup exception (lines 357-359) ────


def test_account_delete_continues_when_gdpr_exports_cleanup_fails(
    client, auth_headers, monkeypatch, fake_storage, fake_supabase
):
    """Account delete succeeds even when gdpr_exports cleanup raises."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)
    monkeypatch.setattr(gdpr, "storage_service", fake_storage)

    original_table = fake_client.table
    call_count = {"gdpr_exports": 0}

    def table_raising_on_gdpr_exports(name):
        if name == "gdpr_exports":
            call_count["gdpr_exports"] += 1
            raise RuntimeError("gdpr exports table broken")
        return original_table(name)

    fake_client.table = table_raising_on_gdpr_exports

    response = client.delete("/api/v1/gdpr/account", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert fake_client.auth.admin.deleted_user_id == "user-123"


# ── account delete: main exception handler (lines 377-385) ────────────


def test_account_delete_failure_returns_structured_error(client, auth_headers, monkeypatch):
    """DELETE /account returns 500 with code when supabase fails early."""
    from app.api.v1 import gdpr

    def boom():
        raise RuntimeError("db connection lost")

    monkeypatch.setattr(gdpr, "get_supabase_service_client", boom)

    response = client.delete("/api/v1/gdpr/account", headers=auth_headers)

    assert response.status_code == 500
    payload = response.json()
    assert payload["code"] == "gdpr_account_delete_failed"
    assert payload["error"] == "Échec de la suppression du compte."


# ── data-summary: with sci but no biens (branch coverage) ────────────


def test_data_summary_sci_no_biens(client, auth_headers, monkeypatch, fake_supabase):
    """data-summary handles sci_ids present but no biens correctly."""
    from app.api.v1 import gdpr

    fake_client = build_gdpr_client(fake_supabase)
    fake_client.store["biens"] = []
    fake_client.store["loyers"] = []

    monkeypatch.setattr(gdpr, "get_supabase_service_client", lambda: fake_client)

    response = client.get("/api/v1/gdpr/data-summary", headers=auth_headers)

    assert response.status_code == 200
    summary = response.json()["data_summary"]
    assert summary["sci_count"] == 1
    assert summary["biens_count"] == 0
    assert summary["loyers_count"] == 0
