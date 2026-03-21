"""
Seed script: crée des données réalistes pour développement et recette.

Usage:
    cd backend && python scripts/seed_dev_data.py [--clean]

Crée:
- 2 utilisateurs (demo Pro + associé)
- 2 SCI complètes (IR + IS) avec toutes les informations légales
- 6 biens (dont 1 immeuble avec 3 lots) avec type_bien
- 6 locataires avec baux actifs
- 12 mois de loyers par bien (mix payé/impayé/en attente)
- Charges décomposées (copro, TF, entretien, assurance, intérêts)
- Assurances PNO + frais agence
- Fiscalité 2024-2025 avec décomposition charges
- Assemblées générales (AGO + AGE)
- Mouvements de parts
- Notifications réalistes
- Abonnement Fiscal (plan Pro, toutes features)
"""
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

import httpx

# ── Config ──────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
)

DEMO_EMAIL = "demo@gerersci.fr"
DEMO_PASSWORD = "password123"

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation,resolution=merge-duplicates",
}


def api(method: str, path: str, json=None):
    r = httpx.request(method, f"{SUPABASE_URL}{path}", headers=HEADERS, json=json, timeout=15)
    if r.status_code >= 400:
        print(f"  ⚠️  {method} {path} → {r.status_code}: {r.text[:200]}")
        return None
    try:
        return r.json()
    except Exception:
        return r.text


def insert(table: str, data):
    return api("POST", f"/rest/v1/{table}", json=data)


def delete_all(table: str):
    pk_map = {"bail_locataires": "id_bail", "admins": "user_id", "quittance_compteur": "sci_id"}
    pk = pk_map.get(table, "id")
    return api("DELETE", f"/rest/v1/{table}?{pk}=neq.00000000-0000-0000-0000-000000000000")


def uid():
    return str(uuid.uuid4())


def create_or_find_user(email, password, full_name):
    resp = api("POST", "/auth/v1/admin/users", json={
        "email": email, "password": password,
        "email_confirm": True, "user_metadata": {"full_name": full_name},
    })
    if resp and isinstance(resp, dict) and "id" in resp:
        return resp["id"]
    users = api("GET", "/auth/v1/admin/users?page=1&per_page=50")
    if users and "users" in users:
        for u in users["users"]:
            if u.get("email") == email:
                return u["id"]
    return None


def clean_all_data():
    print("\n🧹 Nettoyage des données existantes ...")
    tables = [
        "notification_preferences", "notifications",
        "deficit_reportable", "quittance_compteur",
        "mouvements_parts", "assemblees_generales",
        "bail_locataires", "loyers",
        "frais_agence", "assurances_pno", "documents_bien",
        "evenements_bien", "charges", "baux", "locataires",
        "fiscalite", "biens", "associes", "sci",
        "subscriptions", "admins",
    ]
    for t in tables:
        delete_all(t)
    # Clean auth users
    users = api("GET", "/auth/v1/admin/users?page=1&per_page=50")
    if users and "users" in users:
        for u in users["users"]:
            if u["email"] in (DEMO_EMAIL, "pierre.martin@gerersci.fr"):
                api("DELETE", f"/auth/v1/admin/users/{u['id']}")
    print("  ✅ Nettoyage terminé")


def main():
    if "--clean" in sys.argv or "--reset" in sys.argv:
        clean_all_data()

    print("\n🌱 Seed GérerSCI — données de démonstration complètes")
    print("=" * 60)
    today = date.today()

    # ── Utilisateurs ──────────────────────────────────────────────
    print("\n👤 Utilisateurs ...")
    user_id = create_or_find_user(DEMO_EMAIL, DEMO_PASSWORD, "Marie Dupont")
    print(f"  ✅ {DEMO_EMAIL}: {user_id}")

    user2_id = create_or_find_user("pierre.martin@gerersci.fr", "password123", "Pierre Martin")
    print(f"  ✅ pierre.martin@gerersci.fr: {user2_id}")

    # ── SCI 1: SCI Belleville Patrimoine (IR) ─────────────────────
    print("\n🏢 SCI Belleville Patrimoine (IR) ...")
    sci1_id = uid()
    insert("sci", {
        "id": sci1_id,
        "nom": "SCI Belleville Patrimoine",
        "siren": "912345678",
        "regime_fiscal": "IR",
        "statut": "exploitation",
        "capital_social": 150000,
        "nb_parts_total": 1000,
        "valeur_nominale_part": 150,
        "objet_social": "Acquisition, gestion et administration de biens immobiliers situés à Paris et en Île-de-France",
        "date_creation": "2019-01-15",
        "rcs_ville": "Paris",
        "rcs_numero": "912 345 678",
        "forme_juridique": "SCI",
        "nom_gerant": "Marie Dupont",
        "adresse_siege": "12 rue de Belleville, 75020 Paris",
    })

    # Associés SCI 1
    associes_sci1 = [
        {"id": uid(), "id_sci": sci1_id, "user_id": user_id,
         "nom": "Marie Dupont", "email": DEMO_EMAIL,
         "part": 60, "role": "gerant"},
    ]
    if user2_id:
        associes_sci1.append({
            "id": uid(), "id_sci": sci1_id, "user_id": user2_id,
            "nom": "Pierre Martin", "email": "pierre.martin@gerersci.fr",
            "part": 40, "role": "associe",
        })
    insert("associes", associes_sci1)
    print(f"  ✅ SCI 1 + {len(associes_sci1)} associés")

    # ── SCI 2: SCI Horizon Lyon (IS) ──────────────────────────────
    print("\n🏢 SCI Horizon Lyon (IS) ...")
    sci2_id = uid()
    insert("sci", {
        "id": sci2_id,
        "nom": "SCI Horizon Lyon",
        "siren": "987654321",
        "regime_fiscal": "IS",
        "statut": "exploitation",
        "capital_social": 200000,
        "nb_parts_total": 500,
        "valeur_nominale_part": 400,
        "objet_social": "Gestion patrimoniale immobilière dans la métropole de Lyon",
        "date_creation": "2022-06-01",
        "rcs_ville": "Lyon",
        "rcs_numero": "987 654 321",
        "forme_juridique": "SCI",
        "nom_gerant": "Marie Dupont",
        "adresse_siege": "15 rue de la République, 69002 Lyon",
    })
    insert("associes", {
        "id": uid(), "id_sci": sci2_id, "user_id": user_id,
        "nom": "Marie Dupont", "email": DEMO_EMAIL,
        "part": 100, "role": "gerant",
    })
    print("  ✅ SCI 2 + 1 associé")

    # ── Biens ─────────────────────────────────────────────────────
    print("\n🏠 Biens immobiliers ...")

    # SCI 1: 3 biens classiques + 1 immeuble avec 2 lots
    biens_sci1 = [
        {
            "id": uid(), "id_sci": sci1_id,
            "adresse": "12 rue de Belleville — Apt 1", "ville": "Paris",
            "code_postal": "75020", "type_locatif": "nu", "type_bien": "appartement",
            "loyer_cc": 1450, "charges": 150, "tmi": 30,
            "surface_m2": 65, "nb_pieces": 3, "dpe_classe": "D",
            "prix_acquisition": 320000,
        },
        {
            "id": uid(), "id_sci": sci1_id,
            "adresse": "12 rue de Belleville — Apt 2", "ville": "Paris",
            "code_postal": "75020", "type_locatif": "meuble", "type_bien": "appartement",
            "loyer_cc": 1100, "charges": 100, "tmi": 30,
            "surface_m2": 42, "nb_pieces": 2, "dpe_classe": "C",
            "prix_acquisition": 245000,
        },
        {
            "id": uid(), "id_sci": sci1_id,
            "adresse": "8 rue du Commerce", "ville": "Paris",
            "code_postal": "75015", "type_locatif": "nu", "type_bien": "appartement",
            "loyer_cc": 780, "charges": 80, "tmi": 30,
            "surface_m2": 22, "nb_pieces": 1, "dpe_classe": "E",
            "prix_acquisition": 175000,
        },
    ]

    # SCI 2: 1 maison + 1 local commercial
    biens_sci2 = [
        {
            "id": uid(), "id_sci": sci2_id,
            "adresse": "15 rue de la République", "ville": "Lyon",
            "code_postal": "69002", "type_locatif": "nu", "type_bien": "maison",
            "loyer_cc": 1800, "charges": 200, "tmi": 30,
            "surface_m2": 95, "nb_pieces": 4, "dpe_classe": "B",
            "prix_acquisition": 410000,
        },
        {
            "id": uid(), "id_sci": sci2_id,
            "adresse": "22 cours Lafayette — Local A", "ville": "Lyon",
            "code_postal": "69003", "type_locatif": "nu", "type_bien": "local_commercial",
            "loyer_cc": 2200, "charges": 300, "tmi": 30,
            "surface_m2": 55, "nb_pieces": 2, "dpe_classe": "C",
            "prix_acquisition": 280000,
        },
    ]

    all_biens = biens_sci1 + biens_sci2
    insert("biens", all_biens)
    print(f"  ✅ {len(all_biens)} biens (dont 2 lots même adresse + 1 local commercial)")

    # ── Locataires ────────────────────────────────────────────────
    print("\n👥 Locataires ...")
    locataires = [
        {"id": uid(), "id_bien": biens_sci1[0]["id"],
         "nom": "Jean-Marc Lefebvre", "email": "jm.lefebvre@email.fr",
         "telephone": "06 12 34 56 78", "date_debut": "2023-01-01"},
        {"id": uid(), "id_bien": biens_sci1[1]["id"],
         "nom": "Sophie Nguyen", "email": "sophie.nguyen@email.fr",
         "telephone": "06 98 76 54 32", "date_debut": "2023-06-01"},
        {"id": uid(), "id_bien": biens_sci1[2]["id"],
         "nom": "Lucas Bernard", "email": "lucas.b@email.fr",
         "telephone": "07 11 22 33 44", "date_debut": "2024-01-15"},
        {"id": uid(), "id_bien": biens_sci2[0]["id"],
         "nom": "Famille Moreau", "email": "moreau.famille@email.fr",
         "telephone": "06 55 44 33 22", "date_debut": "2023-09-01"},
        {"id": uid(), "id_bien": biens_sci2[1]["id"],
         "nom": "SARL Boulangerie Centrale", "email": "contact@boulangerie-centrale.fr",
         "telephone": "04 78 99 88 77", "date_debut": "2024-03-01"},
    ]
    insert("locataires", locataires)
    print(f"  ✅ {len(locataires)} locataires (dont 1 professionnel)")

    # ── Baux ──────────────────────────────────────────────────────
    print("\n📋 Baux ...")
    baux = [
        {"id": uid(), "id_bien": biens_sci1[0]["id"],
         "date_debut": "2023-01-01", "date_fin": "2025-12-31",
         "loyer_hc": 1300, "charges_locatives": 150, "depot_garantie": 1300,
         "statut": "en_cours"},
        {"id": uid(), "id_bien": biens_sci1[1]["id"],
         "date_debut": "2023-06-01", "date_fin": "2026-05-31",
         "loyer_hc": 1000, "charges_locatives": 100, "depot_garantie": 1000,
         "statut": "en_cours"},
        {"id": uid(), "id_bien": biens_sci1[2]["id"],
         "date_debut": "2024-01-15", "date_fin": "2027-01-14",
         "loyer_hc": 700, "charges_locatives": 80, "depot_garantie": 700,
         "statut": "en_cours"},
        {"id": uid(), "id_bien": biens_sci2[0]["id"],
         "date_debut": "2023-09-01", "date_fin": "2026-08-31",
         "loyer_hc": 1600, "charges_locatives": 200, "depot_garantie": 1600,
         "statut": "en_cours"},
        {"id": uid(), "id_bien": biens_sci2[1]["id"],
         "date_debut": "2024-03-01", "date_fin": "2030-02-28",
         "loyer_hc": 1900, "charges_locatives": 300, "depot_garantie": 3800,
         "statut": "en_cours"},
    ]
    insert("baux", baux)
    # Liaison bail-locataire
    for i in range(min(len(baux), len(locataires))):
        insert("bail_locataires", {"id_bail": baux[i]["id"], "id_locataire": locataires[i]["id"]})
    print(f"  ✅ {len(baux)} baux + liaisons locataires")

    # ── Loyers (12 mois par bien) ─────────────────────────────────
    print("\n💰 Loyers (12 mois) ...")
    loyer_count = 0
    montants = [1450, 1100, 780, 1800, 2200]
    seen_months = set()
    for month_offset in range(12, 0, -1):
        d = today.replace(day=1) - timedelta(days=month_offset * 30)
        loyer_date = d.replace(day=1)
        month_key = (loyer_date.year, loyer_date.month)
        if month_key in seen_months:
            continue
        seen_months.add(month_key)

        for i, bien in enumerate(all_biens):
            if i >= len(locataires):
                continue
            montant = montants[i]
            statut = "paye"
            paiement_date = str(loyer_date + timedelta(days=5))
            if month_offset <= 2:
                statut = "en_attente"
                paiement_date = None
            elif month_offset == 5 and i == 2:
                statut = "en_retard"
                paiement_date = None
            elif month_offset == 8 and i == 0:
                statut = "en_retard"
                paiement_date = None

            insert("loyers", {
                "id": uid(), "id_bien": bien["id"],
                "id_locataire": locataires[i]["id"],
                "date_loyer": str(loyer_date),
                "montant": montant, "statut": statut,
                "date_paiement": paiement_date,
                "mode_paiement": "virement" if statut == "paye" else None,
                "quitus_genere": statut == "paye",
            })
            loyer_count += 1
    print(f"  ✅ {loyer_count} loyers")

    # ── Charges décomposées ────────────────────────────────────────
    print("\n📊 Charges ...")
    charge_count = 0
    charge_definitions = [
        ("copropriete", 250), ("taxe_fonciere", 180),
        ("entretien", 120), ("assurance", 90),
        ("interets_emprunt", 350),
    ]
    for bien in all_biens:
        for type_charge, montant in charge_definitions:
            if type_charge == "interets_emprunt" and bien.get("prix_acquisition", 0) < 200000:
                continue  # Pas d'emprunt sur petits biens
            for q in range(1, 5):
                insert("charges", {
                    "id": uid(), "id_bien": bien["id"],
                    "type_charge": type_charge,
                    "montant": montant,
                    "date_paiement": f"2025-{q*3:02d}-01",
                })
                charge_count += 1
    print(f"  ✅ {charge_count} charges (copro, TF, entretien, assurance, intérêts)")

    # ── Événements bien ──────────────────────────────────────────
    print("\n📅 Événements bien ...")
    evenements = [
        {
            "id": uid(), "id_bien": biens_sci1[0]["id"],
            "type": "reparation", "titre": "Remplacement chaudière",
            "description": "Remplacement de la chaudière gaz par un modèle à condensation",
            "date_evenement": "2025-03-15", "montant": 2800,
            "prestataire": "Plomberie Martin & Fils",
            "deductible_fiscalement": True,
        },
        {
            "id": uid(), "id_bien": biens_sci1[0]["id"],
            "type": "diagnostic", "titre": "Diagnostic DPE",
            "description": "Diagnostic de performance énergétique réalisé par bureau certifié",
            "date_evenement": "2025-01-20", "montant": 150,
            "prestataire": "DiagImmo Paris",
            "deductible_fiscalement": False,
        },
        {
            "id": uid(), "id_bien": biens_sci1[1]["id"],
            "type": "sinistre", "titre": "Dégât des eaux",
            "description": "Fuite canalisation salle de bain — dégâts plafond et mur",
            "date_evenement": "2025-06-10", "montant": 1200,
            "prestataire": "Assurance MAIF — sinistre n°2025-4421",
            "deductible_fiscalement": False,
        },
        {
            "id": uid(), "id_bien": biens_sci1[2]["id"],
            "type": "travaux", "titre": "Peinture rafraîchissement",
            "description": "Remise en peinture complète du studio (murs + plafond)",
            "date_evenement": "2025-08-01", "montant": 950,
            "prestataire": "Peinture Express",
            "deductible_fiscalement": True,
        },
        {
            "id": uid(), "id_bien": biens_sci2[0]["id"],
            "type": "controle", "titre": "Contrôle annuel cheminée",
            "description": "Ramonage et contrôle annuel obligatoire du conduit de cheminée",
            "date_evenement": "2025-10-05", "montant": 120,
            "prestataire": "Ramonage Lyon Sud",
            "deductible_fiscalement": False,
        },
    ]
    for evt in evenements:
        insert("evenements_bien", evt)
    print(f"  ✅ {len(evenements)} événements (réparation, diagnostic, sinistre, travaux, contrôle)")

    # ── Assurances PNO ────────────────────────────────────────────
    print("\n🛡️  Assurances PNO ...")
    for bien in all_biens:
        insert("assurances_pno", {
            "id": uid(), "id_bien": bien["id"],
            "compagnie": "MAIF" if bien["id_sci"] == sci1_id else "AXA",
            "numero_contrat": f"PNO-{bien['code_postal']}-{uid()[:6]}",
            "montant_annuel": 280 if bien.get("nb_pieces", 2) > 1 else 150,
            "date_echeance": "2026-06-01",
        })
    print(f"  ✅ {len(all_biens)} assurances PNO")

    # ── Frais agence ──────────────────────────────────────────────
    print("\n🏪 Frais agence ...")
    insert("frais_agence", {
        "id": uid(), "id_bien": biens_sci2[0]["id"],
        "nom_agence": "Nexity Lyon Presqu'île",
        "contact": "04 72 10 20 30",
        "type_frais": "pourcentage", "montant_ou_pourcentage": 7.5,
    })
    insert("frais_agence", {
        "id": uid(), "id_bien": biens_sci2[1]["id"],
        "nom_agence": "Century 21 Part-Dieu",
        "contact": "04 78 60 50 40",
        "type_frais": "fixe", "montant_ou_pourcentage": 180,
    })
    print("  ✅ 2 frais agence")

    # ── Fiscalité avec décomposition ──────────────────────────────
    print("\n📈 Fiscalité ...")
    for annee in [2024, 2025]:
        insert("fiscalite", {
            "id": uid(), "id_sci": sci1_id, "annee": annee,
            "total_revenus": 39960 if annee == 2024 else 20000,
            "total_charges": 10240 if annee == 2024 else 5500,
            "resultat_fiscal": 29720 if annee == 2024 else 14500,
            "interets_emprunt": 4200 if annee == 2024 else 3800,
            "travaux": 2500 if annee == 2024 else 0,
            "frais_gestion": 60,
            "assurance": 840, "taxe_fonciere": 2160, "copropriete": 3000,
        })
        insert("fiscalite", {
            "id": uid(), "id_sci": sci2_id, "annee": annee,
            "total_revenus": 48000 if annee == 2024 else 24000,
            "total_charges": 12800 if annee == 2024 else 6400,
            "resultat_fiscal": 35200 if annee == 2024 else 17600,
            "interets_emprunt": 5600 if annee == 2024 else 5000,
            "travaux": 0, "frais_gestion": 40,
            "assurance": 560, "taxe_fonciere": 3600, "copropriete": 3000,
        })
    print("  ✅ Fiscalité 2024 + 2025 (avec décomposition charges)")

    # ── Abonnement Fiscal (Pro) — TOUTES les features ─────────────
    print("\n💳 Abonnement Fiscal (plan Pro) ...")
    insert("subscriptions", {
        "id": uid(), "user_id": user_id,
        "stripe_customer_id": f"cus_demo_{uid()[:8]}",
        "stripe_subscription_id": f"sub_demo_{uid()[:8]}",
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_demo"),
        "mode": "subscription", "status": "active",
        "current_period_end": str(today + timedelta(days=365)),
        "onboarding_completed": True,
    })
    print("  ✅ Abonnement Fiscal actif (toutes features débloquées)")

    # ── Notifications ─────────────────────────────────────────────
    print("\n🔔 Notifications ...")
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "late_payment",
        "title": "Loyer impayé — 8 rue du Commerce",
        "message": "Le loyer de Lucas Bernard est en retard de 15 jours. Montant dû : 780 €.",
        "metadata": {"bien_id": biens_sci1[2]["id"], "locataire": "Lucas Bernard",
                     "montant": 780, "jours_retard": 15},
    })
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "bail_expiring",
        "title": "Bail expirant — 12 rue de Belleville Apt 1",
        "message": "Le bail de Jean-Marc Lefebvre expire le 31/12/2025. Pensez au renouvellement.",
        "metadata": {"bail_id": baux[0]["id"], "locataire": "Jean-Marc Lefebvre",
                     "date_fin": "2025-12-31"},
    })
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "pno_expiring",
        "title": "Assurance PNO — Renouvellement à prévoir",
        "message": "L'assurance PNO MAIF pour 12 rue de Belleville expire le 01/06/2026.",
        "metadata": {"bien_adresse": "12 rue de Belleville"},
    })
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "info",
        "title": "Bienvenue sur GérerSCI !",
        "message": "Votre espace de gestion SCI est prêt. Explorez le tableau de bord pour commencer.",
        "metadata": {},
        "read_at": str(datetime.now(timezone.utc)),
    })

    # Préférences notifications (tous les types)
    for ntype in ["late_payment", "bail_expiring", "quittance_pending",
                   "pno_expiring", "new_loyer", "new_associe", "subscription_expiring"]:
        insert("notification_preferences", {
            "id": uid(), "user_id": user_id, "type": ntype,
            "email_enabled": ntype in ("late_payment", "bail_expiring", "pno_expiring"),
            "in_app_enabled": True,
        })
    print("  ✅ 4 notifications + 7 préférences")

    # ── Assemblées générales ──────────────────────────────────────
    print("\n📋 Assemblées générales ...")
    insert("assemblees_generales", {
        "id": uid(), "id_sci": sci1_id,
        "date_ag": "2025-06-15", "type_ag": "ordinaire",
        "exercice_concerne": 2024,
        "ordre_du_jour": "1. Approbation des comptes de l'exercice 2024\n2. Affectation du résultat\n3. Renouvellement du mandat de gérant\n4. Questions diverses",
        "notes": "Comptes approuvés à l'unanimité. Résultat net de 29 720 € affecté en report à nouveau. Mandat de gérant renouvelé pour 3 ans.",
        "resolutions": "Résolution 1 : Les comptes de l'exercice 2024 sont approuvés à l'unanimité.\nRésolution 2 : Le résultat de 29 720 € est affecté en report à nouveau.\nRésolution 3 : Le mandat de gérant de Mme Dupont est renouvelé pour 3 ans.",
        "quorum_atteint": True,
        "pv_url": "https://example.com/pv-ago-2025.pdf",
    })
    insert("assemblees_generales", {
        "id": uid(), "id_sci": sci1_id,
        "date_ag": "2025-11-20", "type_ag": "extraordinaire",
        "exercice_concerne": 2025,
        "ordre_du_jour": "1. Augmentation du capital social\n2. Modification de l'article 7 des statuts",
        "notes": "Capital porté de 150 000 € à 200 000 € par création de 333 parts nouvelles de 150 € chacune, souscrites en numéraire.",
        "resolutions": "Résolution unique : Le capital social est augmenté de 50 000 € pour être porté à 200 000 €.",
        "quorum_atteint": True,
        "pv_url": None,
    })
    print("  ✅ 2 AG (AGO + AGE)")

    # ── Mouvements de parts ───────────────────────────────────────
    if user2_id:
        print("\n📊 Mouvements de parts ...")
        insert("mouvements_parts", {
            "id": uid(), "id_sci": sci1_id,
            "type_mouvement": "souscription",
            "cedant": None, "cessionnaire": "Marie Dupont",
            "nombre_parts": 1000, "prix_unitaire": 150,
            "date_mouvement": "2019-01-15",
            "acte_reference": "Statuts constitutifs — Acte SSP du 15/01/2019",
        })
        insert("mouvements_parts", {
            "id": uid(), "id_sci": sci1_id,
            "type_mouvement": "cession",
            "cedant": "Marie Dupont", "cessionnaire": "Pierre Martin",
            "nombre_parts": 400, "prix_unitaire": 150,
            "date_mouvement": "2023-03-15",
            "acte_reference": "Acte de cession notarié — Me Lefèvre, Paris 20e — Enregistré le 18/03/2023",
        })
        print("  ✅ 2 mouvements (souscription + cession)")

    # ── Admin + résumé ────────────────────────────────────────────
    insert("admins", {"user_id": user_id})

    print("\n" + "=" * 60)
    print("🎉 Seed terminé avec succès !")
    print("=" * 60)
    print(f"""
📧 Email:    {DEMO_EMAIL}
🔑 Password: {DEMO_PASSWORD}
👑 Admin:    oui
💳 Plan:     Fiscal (toutes features)

📊 Données créées:
  • 2 SCI complètes (Belleville IR + Horizon Lyon IS)
  • {len(all_biens)} biens (dont lots immeuble + local commercial)
  • {len(locataires)} locataires (dont 1 professionnel)
  • {len(baux)} baux avec liaisons locataires
  • {loyer_count} loyers (payé/impayé/en attente + date paiement)
  • {charge_count} charges (copro, TF, entretien, assurance, intérêts)
  • {len(all_biens)} assurances PNO
  • 2 frais agence
  • Fiscalité 2024-2025 (avec décomposition charges)
  • 2 AG (AGO + AGE avec résolutions)
  • 2 mouvements de parts
  • 4 notifications + 7 préférences
  • Abonnement Fiscal actif

🌐 URLs:
  • Frontend:  http://localhost:5173
  • Backend:   http://localhost:8001
  • Supabase:  http://localhost:54323 (Studio)
  • Mailpit:   http://localhost:54324 (Emails)
""")


if __name__ == "__main__":
    main()
