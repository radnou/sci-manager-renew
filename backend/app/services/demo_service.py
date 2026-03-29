"""Service for seeding and cleaning up demo data."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)


def _month_ago(months: int) -> str:
    """Return YYYY-MM-DD string for N months ago, day 05."""
    now = datetime.now(UTC)
    year = now.year
    month = now.month - months
    while month <= 0:
        month += 12
        year -= 1
    return f"{year}-{month:02d}-05"


def _next_month_first() -> str:
    """Return YYYY-MM-DD for the 1st of next month."""
    now = datetime.now(UTC)
    if now.month == 12:
        return f"{now.year + 1}-01-01"
    return f"{now.year}-{now.month + 1:02d}-01"


async def seed_demo_data(client, user_id: str) -> dict:
    """Seed a full set of realistic demo data for a new user.

    Creates: 1 SCI, 2 biens, baux, locataires, 6+ months of loyers, charges, PNO.
    All records marked with is_demo=True for easy cleanup.
    """
    logger.info("demo_seed_start", user_id=user_id)

    # --- SCI ---
    sci_id = str(uuid.uuid4())
    client.table("sci").insert({
        "id": sci_id,
        "nom": "SCI Résidence Belleville",
        "siren": None,  # No SIREN for demo data (avoids unique constraint conflicts)
        "regime_fiscal": "IR",
        "capital_social": 150000,
        "forme_juridique": "SCI",
        "nom_gerant": "Vous (démonstration)",
        "is_demo": True,
    }).execute()

    # --- Associé (user = gérant 100%) ---
    client.table("associes").insert({
        "id": str(uuid.uuid4()),
        "id_sci": sci_id,
        "user_id": user_id,
        "nom": "Gérant Démonstration",
        "email": "demo@gerersci.fr",
        "role": "gerant",
        "part": 100,
        "nb_parts": 1000,
        "is_demo": True,
    }).execute()

    # --- Bien 1: T3 Lyon 7e ---
    bien1_id = str(uuid.uuid4())
    client.table("biens").insert({
        "id": bien1_id,
        "id_sci": sci_id,
        "adresse": "45 avenue Jean Jaurès",
        "ville": "Lyon",
        "code_postal": "69007",
        "type_bien": "appartement",
        "type_locatif": "nu",
        "surface_m2": 65,
        "nb_pieces": 3,
        "dpe_classe": "C",
        "loyer_cc": 850,
        "charges": 50,
        "prix_acquisition": 185000,
        "is_demo": True,
    }).execute()

    # --- Bien 2: Studio Lyon 2e ---
    bien2_id = str(uuid.uuid4())
    client.table("biens").insert({
        "id": bien2_id,
        "id_sci": sci_id,
        "adresse": "12 rue Victor Hugo",
        "ville": "Lyon",
        "code_postal": "69002",
        "type_bien": "appartement",
        "type_locatif": "meuble",
        "surface_m2": 28,
        "nb_pieces": 1,
        "dpe_classe": "D",
        "loyer_cc": 620,
        "charges": 40,
        "prix_acquisition": 95000,
        "is_demo": True,
    }).execute()

    # --- Locataire 1 ---
    loc1_id = str(uuid.uuid4())
    client.table("locataires").insert({
        "id": loc1_id,
        "id_bien": bien1_id,
        "nom": "Marie Lefèvre",
        "email": "marie.lefevre@demo.gerersci.fr",
        "telephone": "06 12 34 56 78",
        "date_debut": _month_ago(8),
        "is_demo": True,
    }).execute()

    # --- Locataire 2 ---
    loc2_id = str(uuid.uuid4())
    client.table("locataires").insert({
        "id": loc2_id,
        "id_bien": bien2_id,
        "nom": "Thomas Durand",
        "email": "thomas.durand@demo.gerersci.fr",
        "telephone": "07 98 76 54 32",
        "date_debut": _month_ago(3),
        "is_demo": True,
    }).execute()

    # --- Bail 1 (Bien 1, 8 months ago) ---
    bail1_id = str(uuid.uuid4())
    client.table("baux").insert({
        "id": bail1_id,
        "id_bien": bien1_id,
        "date_debut": _month_ago(8),
        "loyer_hc": 800,
        "charges_locatives": 50,
        "statut": "en_cours",
        "is_demo": True,
    }).execute()
    # Link locataire to bail
    client.table("bail_locataires").insert({
        "id_bail": bail1_id,
        "id_locataire": loc1_id,
    }).execute()

    # --- Bail 2 (Bien 2, 3 months ago) ---
    bail2_id = str(uuid.uuid4())
    client.table("baux").insert({
        "id": bail2_id,
        "id_bien": bien2_id,
        "date_debut": _month_ago(3),
        "loyer_hc": 580,
        "charges_locatives": 40,
        "statut": "en_cours",
        "is_demo": True,
    }).execute()
    client.table("bail_locataires").insert({
        "id_bail": bail2_id,
        "id_locataire": loc2_id,
    }).execute()

    # --- Loyers Bien 1 (6 months: 4 payés, 1 en attente, 1 en retard) ---
    loyer_statuses_1 = [
        (_month_ago(6), "paye", _month_ago(6)),
        (_month_ago(5), "paye", _month_ago(5)),
        (_month_ago(4), "paye", _month_ago(4)),
        (_month_ago(3), "paye", _month_ago(3)),
        (_month_ago(2), "en_retard", None),
        (_month_ago(1), "en_attente", None),
    ]
    for date_loyer, statut, date_paiement in loyer_statuses_1:
        row = {
            "id": str(uuid.uuid4()),
            "id_bien": bien1_id,
            "montant": 850,
            "statut": statut,
            "date_loyer": date_loyer,
            "id_locataire": loc1_id,
            "is_demo": True,
        }
        if date_paiement:
            row["date_paiement"] = date_paiement
        client.table("loyers").insert(row).execute()

    # --- Loyers Bien 2 (3 months: 2 payés, 1 en attente) ---
    loyer_statuses_2 = [
        (_month_ago(3), "paye", _month_ago(3)),
        (_month_ago(2), "paye", _month_ago(2)),
        (_month_ago(1), "en_attente", None),
    ]
    for date_loyer, statut, date_paiement in loyer_statuses_2:
        row = {
            "id": str(uuid.uuid4()),
            "id_bien": bien2_id,
            "montant": 620,
            "statut": statut,
            "date_loyer": date_loyer,
            "id_locataire": loc2_id,
            "is_demo": True,
        }
        if date_paiement:
            row["date_paiement"] = date_paiement
        client.table("loyers").insert(row).execute()

    # --- Charges Bien 1 ---
    charges_data_1 = [
        ("copropriete", 150, _month_ago(3)),
        ("copropriete", 150, _month_ago(6)),
        ("taxe_fonciere", 800, _month_ago(4)),
    ]
    for type_charge, montant, date in charges_data_1:
        client.table("charges").insert({
            "id": str(uuid.uuid4()),
            "id_bien": bien1_id,
            "type_charge": type_charge,
            "montant": montant,
            "date_paiement": date,
            "is_demo": True,
        }).execute()

    # --- Charges Bien 2 ---
    client.table("charges").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien2_id,
        "type_charge": "copropriete",
        "montant": 90,
        "date_paiement": _month_ago(3),
        "is_demo": True,
    }).execute()

    # --- Assurance PNO (Bien 1) ---
    client.table("assurances_pno").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien1_id,
        "compagnie": "AXA",
        "numero_contrat": "PNO-DEMO-2025-001",
        "montant_annuel": 180,
        "date_echeance": _next_month_first(),
        "is_demo": True,
    }).execute()

    # --- Mark demo as seeded in subscriptions ---
    # Upsert subscription row with demo_seeded=True
    sub_check = (
        client.table("subscriptions")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    if sub_check.data:
        client.table("subscriptions").update({
            "demo_seeded": True,
        }).eq("user_id", user_id).execute()
    else:
        client.table("subscriptions").insert({
            "user_id": user_id,
            "status": "demo",
            "demo_seeded": True,
            "onboarding_completed": False,
        }).execute()

    logger.info("demo_seed_complete", user_id=user_id, sci_id=sci_id)
    return {"sci_id": sci_id, "bien_ids": [bien1_id, bien2_id]}


async def cleanup_demo_data(client, user_id: str) -> int:
    """Remove all demo data for a user. Called after subscription activation."""
    logger.info("demo_cleanup_start", user_id=user_id)

    # Find demo SCIs for this user (via associes)
    assoc_res = (
        client.table("associes")
        .select("id_sci")
        .eq("user_id", user_id)
        .eq("is_demo", True)
        .execute()
    )
    sci_ids = [row["id_sci"] for row in (assoc_res.data or [])]

    if not sci_ids:
        logger.info("demo_cleanup_no_data", user_id=user_id)
        return 0

    # Find all demo biens
    biens_res = (
        client.table("biens")
        .select("id")
        .in_("id_sci", sci_ids)
        .eq("is_demo", True)
        .execute()
    )
    bien_ids = [row["id"] for row in (biens_res.data or [])]

    deleted = 0

    # Delete in dependency order (children first)
    if bien_ids:
        # Loyers
        r = client.table("loyers").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Charges
        r = client.table("charges").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Assurance PNO
        r = client.table("assurances_pno").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Bail_locataires (via baux)
        baux_res = client.table("baux").select("id").in_("id_bien", bien_ids).eq("is_demo", True).execute()
        bail_ids = [row["id"] for row in (baux_res.data or [])]
        if bail_ids:
            client.table("bail_locataires").delete().in_("id_bail", bail_ids).execute()

        # Locataires
        r = client.table("locataires").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Baux
        r = client.table("baux").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Biens
        r = client.table("biens").delete().in_("id_sci", sci_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

    # Associes
    r = client.table("associes").delete().eq("user_id", user_id).eq("is_demo", True).execute()
    deleted += len(r.data or [])

    # SCIs
    for sci_id in sci_ids:
        r = client.table("sci").delete().eq("id", sci_id).eq("is_demo", True).execute()
        deleted += len(r.data or [])

    # Reset demo_seeded flag
    client.table("subscriptions").update({
        "demo_seeded": False,
    }).eq("user_id", user_id).execute()

    logger.info("demo_cleanup_complete", user_id=user_id, deleted_rows=deleted)
    return deleted
