from __future__ import annotations

from types import SimpleNamespace


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
