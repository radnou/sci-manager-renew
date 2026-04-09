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


def _last_year() -> int:
    return datetime.now(UTC).year - 1


async def seed_demo_data(client, user_id: str) -> dict:
    """Seed a complete demo dataset for a new user.

    Creates: 1 SCI, 1 bien with ALL data filled in:
    identité complète, bail, locataire, 6 mois de loyers, charges,
    PNO, frais agence, crédit immobilier, fiscalité, AG, mouvement de parts,
    événement bien.
    All entity-table records marked with is_demo=True for easy cleanup.
    """
    logger.info("demo_seed_start", user_id=user_id)

    # --- SCI ---
    sci_id = str(uuid.uuid4())
    client.table("sci").insert({
        "id": sci_id,
        "nom": "SCI Résidence Belleville",
        "siren": None,
        "regime_fiscal": "IR",
        "capital_social": 150000,
        "forme_juridique": "SCI",
        "nom_gerant": "Vous (démonstration)",
        "adresse_siege": "12 rue de la Paix, 75002 Paris",
        "date_creation": "2020-06-15",
        "objet_social": "Acquisition, administration et gestion de biens immobiliers",
        "is_demo": True,
    }).execute()

    # --- Associé (user = gérant 70%) ---
    assoc1_id = str(uuid.uuid4())
    client.table("associes").insert({
        "id": assoc1_id,
        "id_sci": sci_id,
        "user_id": user_id,
        "nom": "Gérant Démonstration",
        "email": "demo@gerersci.fr",
        "role": "gerant",
        "part": 70,
        "nb_parts": 700,
        "is_demo": True,
    }).execute()

    # --- Associé 2 (co-associé 30%) ---
    assoc2_id = str(uuid.uuid4())
    client.table("associes").insert({
        "id": assoc2_id,
        "id_sci": sci_id,
        "nom": "Sophie Martin",
        "email": "sophie.martin@demo.gerersci.fr",
        "role": "associe",
        "part": 30,
        "nb_parts": 300,
        "is_demo": True,
    }).execute()

    # --- Bien: T3 Lyon 7e (COMPLET) ---
    bien_id = str(uuid.uuid4())
    client.table("biens").insert({
        "id": bien_id,
        "id_sci": sci_id,
        "adresse": "45 avenue Jean Jaurès",
        "ville": "Lyon",
        "code_postal": "69007",
        "type_bien": "appartement",
        "type_locatif": "nu",
        "surface_m2": 65,
        "nb_pieces": 3,
        "etage": "3ème",
        "annee_construction": 1985,
        "dpe_classe": "C",
        "ges_classe": "B",
        "loyer_cc": 850,
        "charges": 50,
        "prix_acquisition": 185000,
        "date_acquisition": "2021-03-10",
        "is_demo": True,
    }).execute()

    # --- Locataire ---
    loc_id = str(uuid.uuid4())
    client.table("locataires").insert({
        "id": loc_id,
        "id_bien": bien_id,
        "nom": "Marie Lefèvre",
        "email": "marie.lefevre@demo.gerersci.fr",
        "telephone": "06 12 34 56 78",
        "date_debut": _month_ago(8),
        "is_demo": True,
    }).execute()

    # --- Bail (8 months ago, with état des lieux) ---
    bail_id = str(uuid.uuid4())
    client.table("baux").insert({
        "id": bail_id,
        "id_bien": bien_id,
        "date_debut": _month_ago(8),
        "date_fin": None,
        "loyer_hc": 800,
        "charges_locatives": 50,
        "depot_garantie": 800,
        "statut": "en_cours",
        "etat_lieux_date": _month_ago(8),
        "etat_lieux_notes": "Bon état général. Traces d'usure normales sur le parquet du salon.",
        "is_demo": True,
    }).execute()
    client.table("bail_locataires").insert({
        "id_bail": bail_id,
        "id_locataire": loc_id,
    }).execute()

    # --- Loyers: 6 mois (4 payés, 1 en retard, 1 en attente) ---
    loyer_statuses = [
        (_month_ago(6), "paye", _month_ago(6)),
        (_month_ago(5), "paye", _month_ago(5)),
        (_month_ago(4), "paye", _month_ago(4)),
        (_month_ago(3), "paye", _month_ago(3)),
        (_month_ago(2), "en_retard", None),
        (_month_ago(1), "en_attente", None),
    ]
    for date_loyer, statut, date_paiement in loyer_statuses:
        row = {
            "id": str(uuid.uuid4()),
            "id_bien": bien_id,
            "montant": 850,
            "statut": statut,
            "date_loyer": date_loyer,
            "id_locataire": loc_id,
            "is_demo": True,
        }
        if date_paiement:
            row["date_paiement"] = date_paiement
        client.table("loyers").insert(row).execute()

    # --- Charges ---
    charges_data = [
        ("copropriete", 150, _month_ago(3)),
        ("copropriete", 150, _month_ago(6)),
        ("taxe_fonciere", 800, _month_ago(4)),
        ("entretien", 120, _month_ago(2)),
    ]
    for type_charge, montant, date in charges_data:
        client.table("charges").insert({
            "id": str(uuid.uuid4()),
            "id_bien": bien_id,
            "type_charge": type_charge,
            "montant": montant,
            "date_paiement": date,
            "is_demo": True,
        }).execute()

    # --- Assurance PNO ---
    client.table("assurances_pno").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien_id,
        "compagnie": "AXA",
        "numero_contrat": "PNO-DEMO-2025-001",
        "montant_annuel": 180,
        "date_echeance": _next_month_first(),
        "is_demo": True,
    }).execute()

    # --- Frais Agence ---
    client.table("frais_agence").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien_id,
        "nom_agence": "Nexity Gestion",
        "contact": "contact@nexity-lyon7.fr",
        "type_frais": "pourcentage",
        "montant_ou_pourcentage": 7.5,
    }).execute()

    # --- Crédit Immobilier ---
    client.table("credits_immobiliers").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien_id,
        "banque": "Crédit Agricole",
        "numero_contrat": "CA-2021-DEMO-456",
        "montant_emprunte": 148000,
        "taux_nominal": 1.350,
        "taux_assurance": 0.250,
        "duree_mois": 240,
        "date_debut": "2021-04-01",
        "mensualite": 695.42,
        "capital_restant_du": 118200,
        "type_credit": "amortissable",
        "statut": "en_cours",
    }).execute()

    # --- Fiscalité (année précédente) ---
    year = _last_year()
    client.table("fiscalite").insert({
        "id": str(uuid.uuid4()),
        "id_sci": sci_id,
        "annee": year,
        "total_revenus": 10200,
        "total_charges": 3420,
        "resultat_fiscal": 6780,
        "interets_emprunt": 1850,
        "travaux": 0,
        "frais_gestion": 720,
        "assurance": 180,
        "taxe_fonciere": 800,
        "copropriete": 300,
    }).execute()

    # --- Assemblée Générale ---
    client.table("assemblees_generales").insert({
        "id": str(uuid.uuid4()),
        "id_sci": sci_id,
        "date_ag": f"{year}-06-15",
        "type_ag": "ordinaire",
        "exercice_annee": year,
        "ordre_du_jour": "Approbation des comptes de l'exercice, quitus au gérant, budget prévisionnel",
        "resolutions": "Résolution 1 : Approbation des comptes — adoptée à l'unanimité.\nRésolution 2 : Quitus au gérant — adopté à l'unanimité.",
        "quorum_atteint": True,
        "notes": "AG tenue au siège social. Présents : 2 associés sur 2 (100% des parts).",
    }).execute()

    # --- Mouvement de parts ---
    client.table("mouvements_parts").insert({
        "id": str(uuid.uuid4()),
        "id_sci": sci_id,
        "date_mouvement": "2023-01-15",
        "type": "cession",
        "cedant": "Pierre Dupont (fondateur)",
        "cessionnaire": "Sophie Martin",
        "nb_parts": 300,
        "prix_total": 45000,
    }).execute()

    # --- Événement Bien ---
    client.table("evenements_bien").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien_id,
        "type": "travaux",
        "titre": "Remplacement chaudière",
        "description": "Remplacement de la chaudière gaz par une pompe à chaleur air/eau. Travaux réalisés par Daikin Lyon.",
        "date_evenement": _month_ago(2),
        "montant": 4800,
        "prestataire": "Daikin Lyon",
        "deductible_fiscalement": True,
    }).execute()

    # --- Mark demo as seeded in subscriptions ---
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
    return {"sci_id": sci_id, "bien_ids": [bien_id]}


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

        # Frais agence (no is_demo — clean by FK)
        r = client.table("frais_agence").delete().in_("id_bien", bien_ids).execute()
        deleted += len(r.data or [])

        # Crédits immobiliers (no is_demo — clean by FK)
        r = client.table("credits_immobiliers").delete().in_("id_bien", bien_ids).execute()
        deleted += len(r.data or [])

        # Événements bien (no is_demo — clean by FK)
        r = client.table("evenements_bien").delete().in_("id_bien", bien_ids).execute()
        deleted += len(r.data or [])

        # Régularisations charges (no is_demo — clean by FK)
        r = client.table("regularisations_charges").delete().in_("id_bien", bien_ids).execute()
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

    # SCI-level tables (no is_demo — clean by FK)
    for sci_id in sci_ids:
        # Fiscalité
        r = client.table("fiscalite").delete().eq("id_sci", sci_id).execute()
        deleted += len(r.data or [])

        # Assemblées générales
        r = client.table("assemblees_generales").delete().eq("id_sci", sci_id).execute()
        deleted += len(r.data or [])

        # Mouvements de parts
        r = client.table("mouvements_parts").delete().eq("id_sci", sci_id).execute()
        deleted += len(r.data or [])

    # Associes
    r = client.table("associes").delete().eq("user_id", user_id).eq("is_demo", True).execute()
    deleted += len(r.data or [])

    # SCIs
    for sci_id in sci_ids:
        r = client.table("sci").delete().eq("id", sci_id).eq("is_demo", True).execute()
        deleted += len(r.data or [])

    # Reset demo_seeded flag and onboarding_completed so the user starts fresh
    client.table("subscriptions").update({
        "demo_seeded": False,
        "onboarding_completed": False,
    }).eq("user_id", user_id).execute()

    logger.info("demo_cleanup_complete", user_id=user_id, deleted_rows=deleted)
    return deleted
