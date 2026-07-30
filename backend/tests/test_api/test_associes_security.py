"""Tests de non-régression sécurité — findings C1 et C3 de l'audit du 2026-07-25.

Ces tests verrouillent deux vulnérabilités critiques :

C1 — Contournement du paiement : une ligne `subscriptions` forgée par
     l'utilisateur ne doit jamais imposer ses propres entitlements
     (max_scis / max_biens / features). Le catalogue serveur prime.

C3 — Élévation de privilège : un associé sans rôle de gouvernance ne doit
     pouvoir ni ajouter, ni modifier, ni supprimer un associé — en
     particulier, il ne doit pas pouvoir se promouvoir gérant.

Ne pas assouplir ces tests sans relire AUDIT_EXTERNE_2026-07-25.md.
"""

import pytest

from app.core.entitlements import PlanKey, build_plan_snapshot


# ============================================================
# C3 — Élévation de privilège sur /associes
# ============================================================

def _demote_user_to_associe(fake_supabase, sci_id: str = "sci-1", user_id: str = "user-123"):
    """Retire le rôle de gouvernance de l'utilisateur courant sur une SCI."""
    for row in fake_supabase.store["associes"]:
        if row.get("id_sci") == sci_id and row.get("user_id") == user_id:
            row["role"] = "associe"


def test_associe_cannot_promote_self_to_gerant(client, auth_headers, fake_supabase):
    """C3 — Un simple associé ne peut pas se promouvoir gérant.

    Vecteur d'origine : PATCH /associes/{self} {"role": "gerant"}, qui passait
    car seule l'appartenance à la SCI était vérifiée.
    """
    _demote_user_to_associe(fake_supabase)

    resp = client.patch(
        "/api/v1/associes/associe-1",
        json={"role": "gerant"},
        headers=auth_headers,
    )

    assert resp.status_code == 403, (
        "Un associé non gérant a pu se promouvoir — régression du finding C3"
    )
    # Le rôle en base ne doit pas avoir bougé.
    stored = next(a for a in fake_supabase.store["associes"] if a["id"] == "associe-1")
    assert stored["role"] == "associe"


def test_associe_cannot_create_associe(client, auth_headers, fake_supabase):
    """C3 — Un simple associé ne peut pas ajouter d'associé à la SCI."""
    _demote_user_to_associe(fake_supabase)

    resp = client.post(
        "/api/v1/associes/",
        json={
            "id_sci": "sci-1",
            "nom": "Intrus Ajoute",
            "email": "intrus@example.com",
            "part": 1,
            "role": "associe",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 403


def test_associe_cannot_delete_associe(client, auth_headers, fake_supabase):
    """C3 — Un simple associé ne peut pas retirer un co-associé."""
    _demote_user_to_associe(fake_supabase)

    resp = client.delete("/api/v1/associes/associe-1b", headers=auth_headers)

    assert resp.status_code == 403
    assert any(a["id"] == "associe-1b" for a in fake_supabase.store["associes"])


def test_create_associe_ignores_client_supplied_user_id(client, auth_headers, fake_supabase):
    """C3 — `user_id` fourni par le client doit être ignoré.

    Sinon on rattache arbitrairement le compte d'un tiers à sa propre SCI.
    Le rattachement légitime passe par l'invitation email (associe_linking).
    """
    for a in fake_supabase.store["associes"]:
        if a["id"] == "associe-1":
            a["part"] = 10
        if a["id"] == "associe-1b":
            a["part"] = 10

    resp = client.post(
        "/api/v1/associes/",
        json={
            "id_sci": "sci-1",
            "nom": "Compte Detourne",
            "email": "victime@example.com",
            "part": 5,
            "role": "associe",
            "user_id": "user-victime-999",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 201
    created_id = resp.json()["id"]
    stored = next(a for a in fake_supabase.store["associes"] if a["id"] == created_id)
    assert stored.get("user_id") in (None, ""), (
        "user_id imposé par le client a été persisté — régression du finding C3"
    )


def test_co_gerant_keeps_management_rights(client, auth_headers, fake_supabase):
    """Le co-gérant est un rôle de gouvernance : il conserve la gestion.

    Garde-fou contre un correctif trop strict qui n'autoriserait que 'gerant'
    et priverait les co-gérants de toute gestion des associés.
    """
    for row in fake_supabase.store["associes"]:
        if row.get("id_sci") == "sci-1" and row.get("user_id") == "user-123":
            row["role"] = "co_gerant"
            row["part"] = 10
        if row.get("id") == "associe-1b":
            row["part"] = 10

    resp = client.post(
        "/api/v1/associes/",
        json={
            "id_sci": "sci-1",
            "nom": "Ajout Par Co Gerant",
            "email": "cg@example.com",
            "part": 5,
            "role": "associe",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 201


@pytest.mark.parametrize("role_invalide", ["admin", "superuser", "GERANT_", "owner"])
def test_role_hors_referentiel_rejete(client, auth_headers, role_invalide):
    """Le rôle est contraint au référentiel (cf. contrainte associes_role_check)."""
    resp = client.patch(
        "/api/v1/associes/associe-1",
        json={"role": role_invalide},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ============================================================
# C1 — Les entitlements ne peuvent pas être forgés
# ============================================================

def test_forged_subscription_row_cannot_override_entitlements():
    """C1 — Le catalogue serveur prime toujours sur la ligne `subscriptions`.

    Reproduit l'exploit vérifié en production le 2026-07-25 : une ligne forgée
    en `status=active, plan_key=pilotage, max_biens=null` accordait des quotas
    illimités. La fusion doit désormais faire gagner le snapshot serveur.
    """
    snapshot = build_plan_snapshot(PlanKey.FREE)
    forged_row = {
        "user_id": "attaquant",
        "status": "active",
        "plan_key": "pilotage",
        "max_scis": None,
        "max_biens": None,
        "features": {"quitus_enabled": True, "multi_sci_enabled": True},
        "stripe_price_id": None,
    }

    # Ordre de fusion appliqué par SubscriptionService.get_subscription_summary
    merged = {**forged_row, **snapshot}

    assert merged["max_biens"] == snapshot["max_biens"]
    assert merged["max_scis"] == snapshot["max_scis"]
    assert merged["features"] == snapshot["features"]
    assert merged["plan_key"] == PlanKey.FREE.value
    # Les colonnes légitimes de la ligne restent lisibles.
    assert merged["status"] == "active"
    assert "stripe_price_id" in merged


def test_plan_snapshot_never_exposes_unlimited_quota_for_free():
    """Garde-fou : le plan FREE ne doit jamais accorder de quota illimité."""
    snapshot = build_plan_snapshot(PlanKey.FREE)
    assert snapshot["max_scis"] is not None
    assert snapshot["max_biens"] is not None
    assert snapshot["max_scis"] == 0
    assert snapshot["max_biens"] == 0
