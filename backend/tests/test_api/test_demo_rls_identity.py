"""Non-régression : le seed/cleanup demo doit écrire en service_role.

Depuis la migration 043 (audit C3), la policy `associes_member_insert` exige
d'être déjà gérant de la SCI ciblée. La SCI de démonstration vient d'être créée
et n'a encore aucun associé : avec le client utilisateur, l'insertion du gérant
est rejetée par RLS et tout le parcours demo-first casse en production.

Les tests fonctionnels ne peuvent pas l'attraper (le faux client Supabase
n'applique pas RLS) — d'où ce test d'identité du client.
"""

import pytest

from app.api.v1 import demo as demo_module


class _ServiceSentinel:
    """Objet distinctif renvoyé à la place du client service_role."""


@pytest.fixture
def service_sentinel(monkeypatch):
    sentinel = _ServiceSentinel()
    monkeypatch.setattr(demo_module, "get_supabase_service_client", lambda: sentinel)
    return sentinel


def test_seed_demo_uses_service_role_client(
    client, auth_headers, fake_supabase, monkeypatch, service_sentinel
):
    captured = {}

    async def fake_seed(supabase_client, user_id):
        captured["client"] = supabase_client
        return {"sci_id": "sci-demo"}

    monkeypatch.setattr(demo_module, "seed_demo_data", fake_seed)
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "status": "demo", "demo_seeded": False}
    ]

    resp = client.post("/api/v1/demo/seed", headers=auth_headers)

    assert resp.status_code == 201
    assert captured["client"] is service_sentinel


def test_cleanup_demo_uses_service_role_client(
    client, auth_headers, monkeypatch, service_sentinel
):
    captured = {}

    async def fake_cleanup(supabase_client, user_id):
        captured["client"] = supabase_client
        return 3

    monkeypatch.setattr(demo_module, "cleanup_demo_data", fake_cleanup)

    resp = client.delete("/api/v1/demo/cleanup", headers=auth_headers)

    assert resp.status_code == 200
    assert captured["client"] is service_sentinel
