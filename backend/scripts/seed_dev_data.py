"""
Seed script: crée un utilisateur test + données SCI réalistes.

Usage:
    cd backend && python scripts/seed_dev_data.py

Crée:
- 1 utilisateur test (demo@gerersci.fr / password123)
- 2 SCI avec associés
- 4 biens immobiliers (appartements, studio, maison)
- 4 baux actifs avec locataires
- 12 mois de loyers (mix payé/impayé/en attente)
- Charges, assurances PNO, frais agence
- Fiscalité 2024 et 2025
- Notifications réalistes
- Abonnement Pro actif
"""
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

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


def api(method: str, path: str, json=None, headers_override=None):
    url = f"{SUPABASE_URL}{path}"
    h = headers_override or HEADERS
    r = httpx.request(method, url, headers=h, json=json, timeout=15)
    if r.status_code >= 400:
        print(f"  ⚠️  {method} {path} → {r.status_code}: {r.text[:200]}")
        return None
    try:
        return r.json()
    except Exception:
        return r.text


def rpc(fn_name: str, params: dict = None):
    return api("POST", f"/rest/v1/rpc/{fn_name}", json=params or {})


def insert(table: str, data: dict | list):
    return api("POST", f"/rest/v1/{table}", json=data)


def delete_all(table: str):
    """Supprime toutes les lignes d'une table (via service role, bypass RLS)."""
    # Tables avec PK composite ou non-standard
    pk_map = {
        "bail_locataires": "id_bail",
        "admins": "user_id",
    }
    pk = pk_map.get(table, "id")
    return api("DELETE", f"/rest/v1/{table}?{pk}=neq.00000000-0000-0000-0000-000000000000")


def uid():
    return str(uuid.uuid4())


def clean_all_data():
    """Supprime toutes les données seed (ordre respecte les FK)."""
    print("\n🧹 Nettoyage des données existantes ...")
    # Ordre inverse des dépendances FK
    tables = [
        "notification_preferences", "notifications",
        "bail_locataires", "loyers",
        "frais_agence", "assurances_pno", "documents_bien",
        "charges", "baux", "locataires",
        "fiscalite", "biens", "associes", "sci",
        "subscriptions", "admins",
    ]
    for t in tables:
        delete_all(t)
        print(f"  ↳ {t} vidée")

    # Supprimer les users auth
    users = api("GET", "/auth/v1/admin/users?page=1&per_page=50")
    if users and "users" in users:
        for u in users["users"]:
            if u["email"] in (DEMO_EMAIL, "pierre.martin@gerersci.fr"):
                api("DELETE", f"/auth/v1/admin/users/{u['id']}")
                print(f"  ↳ User {u['email']} supprimé")
    print("  ✅ Nettoyage terminé")


# ── Main ────────────────────────────────────────────────────────
def main():
    clean = "--clean" in sys.argv or "--reset" in sys.argv

    print("🌱 Seed GererSCI — données de démonstration")
    print("=" * 50)

    if clean:
        clean_all_data()

    # 1. Créer l'utilisateur via Supabase Auth Admin API
    print("\n👤 Création utilisateur demo@gerersci.fr ...")
    user_resp = api("POST", "/auth/v1/admin/users", json={
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD,
        "email_confirm": True,
        "user_metadata": {"full_name": "Marie Dupont"},
    })
    if user_resp and isinstance(user_resp, dict) and "id" in user_resp:
        user_id = user_resp["id"]
        print(f"  ✅ User créé: {user_id}")
    else:
        # User existe peut-être déjà — le chercher
        print("  🔄 User existe peut-être déjà, recherche...")
        users = api("GET", f"/auth/v1/admin/users?page=1&per_page=50")
        if users and "users" in users:
            for u in users["users"]:
                if u.get("email") == DEMO_EMAIL:
                    user_id = u["id"]
                    print(f"  ✅ User existant trouvé: {user_id}")
                    break
            else:
                print("  ❌ Impossible de créer/trouver l'utilisateur")
                sys.exit(1)
        else:
            print("  ❌ Impossible de lister les utilisateurs")
            sys.exit(1)

    # 2. Créer un 2ème utilisateur (associé)
    print("\n👤 Création 2ème utilisateur (associé) ...")
    user2_resp = api("POST", "/auth/v1/admin/users", json={
        "email": "pierre.martin@gerersci.fr",
        "password": "password123",
        "email_confirm": True,
        "user_metadata": {"full_name": "Pierre Martin"},
    })
    user2_id = None
    if user2_resp and isinstance(user2_resp, dict) and "id" in user2_resp:
        user2_id = user2_resp["id"]
        print(f"  ✅ User 2 créé: {user2_id}")
    else:
        users = api("GET", f"/auth/v1/admin/users?page=1&per_page=50")
        if users and "users" in users:
            for u in users["users"]:
                if u.get("email") == "pierre.martin@gerersci.fr":
                    user2_id = u["id"]
                    print(f"  ✅ User 2 existant: {user2_id}")
                    break

    # ── SCI 1: SCI Belleville Patrimoine ────────────────────────
    print("\n🏢 Création SCI Belleville Patrimoine ...")
    sci1_id = uid()
    insert("sci", {
        "id": sci1_id,
        "nom": "SCI Belleville Patrimoine",
        "siren": "912345678",
        "regime_fiscal": "IR",
    })
    print(f"  ✅ SCI 1: {sci1_id}")

    # Associés SCI 1
    insert("associes", [
        {
            "id": uid(), "id_sci": sci1_id, "user_id": user_id,
            "nom": "Marie Dupont", "email": DEMO_EMAIL,
            "part": 60, "role": "gerant",
        },
        {
            "id": uid(), "id_sci": sci1_id, "user_id": user2_id,
            "nom": "Pierre Martin", "email": "pierre.martin@gerersci.fr",
            "part": 40, "role": "associe",
        },
    ] if user2_id else [
        {
            "id": uid(), "id_sci": sci1_id, "user_id": user_id,
            "nom": "Marie Dupont", "email": DEMO_EMAIL,
            "part": 100, "role": "gerant",
        },
    ])
    print("  ✅ Associés ajoutés")

    # ── SCI 2: SCI Horizon Lyon ─────────────────────────────────
    print("\n🏢 Création SCI Horizon Lyon ...")
    sci2_id = uid()
    insert("sci", {
        "id": sci2_id,
        "nom": "SCI Horizon Lyon",
        "siren": "987654321",
        "regime_fiscal": "IS",
    })
    insert("associes", {
        "id": uid(), "id_sci": sci2_id, "user_id": user_id,
        "nom": "Marie Dupont", "email": DEMO_EMAIL,
        "part": 100, "role": "gerant",
    })
    print(f"  ✅ SCI 2: {sci2_id}")

    # ── Biens SCI 1 ────────────────────────────────────────────
    print("\n🏠 Création des biens immobiliers ...")
    biens = [
        {
            "id": uid(), "id_sci": sci1_id,
            "adresse": "12 rue de Belleville", "ville": "Paris",
            "code_postal": "75020", "type_locatif": "T3",
            "loyer_cc": 1450, "charges": 150, "tmi": 30,
            "surface_m2": 65, "nb_pieces": 3, "dpe_classe": "D",
            "prix_acquisition": 320000,
            "acquisition_date": "2019-06-15",
        },
        {
            "id": uid(), "id_sci": sci1_id,
            "adresse": "45 avenue Jean Jaurès", "ville": "Paris",
            "code_postal": "75019", "type_locatif": "T2",
            "loyer_cc": 1100, "charges": 100, "tmi": 30,
            "surface_m2": 42, "nb_pieces": 2, "dpe_classe": "C",
            "prix_acquisition": 245000,
            "acquisition_date": "2020-03-01",
        },
        {
            "id": uid(), "id_sci": sci1_id,
            "adresse": "8 rue du Commerce", "ville": "Paris",
            "code_postal": "75015", "type_locatif": "Studio",
            "loyer_cc": 780, "charges": 80, "tmi": 30,
            "surface_m2": 22, "nb_pieces": 1, "dpe_classe": "E",
            "prix_acquisition": 175000,
            "acquisition_date": "2021-09-10",
        },
    ]

    # Bien SCI 2
    bien4 = {
        "id": uid(), "id_sci": sci2_id,
        "adresse": "15 rue de la République", "ville": "Lyon",
        "code_postal": "69002", "type_locatif": "T4",
        "loyer_cc": 1800, "charges": 200, "tmi": 30,
        "surface_m2": 95, "nb_pieces": 4, "dpe_classe": "B",
        "prix_acquisition": 410000,
        "acquisition_date": "2022-01-20",
    }

    all_biens = biens + [bien4]
    insert("biens", all_biens)
    print(f"  ✅ {len(all_biens)} biens créés")

    # ── Locataires ──────────────────────────────────────────────
    print("\n👥 Création des locataires ...")
    locataires = [
        {
            "id": uid(), "id_bien": biens[0]["id"],
            "nom": "Jean-Marc Lefebvre", "email": "jm.lefebvre@email.fr",
            "telephone": "06 12 34 56 78",
            "date_debut": "2023-01-01",
        },
        {
            "id": uid(), "id_bien": biens[1]["id"],
            "nom": "Sophie Nguyen", "email": "sophie.nguyen@email.fr",
            "telephone": "06 98 76 54 32",
            "date_debut": "2023-06-01",
        },
        {
            "id": uid(), "id_bien": biens[2]["id"],
            "nom": "Lucas Bernard", "email": "lucas.b@email.fr",
            "telephone": "07 11 22 33 44",
            "date_debut": "2024-01-15",
        },
        {
            "id": uid(), "id_bien": bien4["id"],
            "nom": "Famille Moreau", "email": "moreau.famille@email.fr",
            "telephone": "06 55 44 33 22",
            "date_debut": "2023-09-01",
        },
    ]
    insert("locataires", locataires)
    print(f"  ✅ {len(locataires)} locataires créés")

    # ── Baux ────────────────────────────────────────────────────
    print("\n📋 Création des baux ...")
    baux = [
        {
            "id": uid(), "id_bien": biens[0]["id"],
            "date_debut": "2023-01-01", "date_fin": "2025-12-31",
            "loyer_hc": 1300, "charges_locatives": 150,
            "depot_garantie": 1300, "statut": "en_cours",
            "indice_irl_reference": "T1 2023",
            "date_revision": "2024-01-01",
            "etat_lieux_entree": "2023-01-01",
        },
        {
            "id": uid(), "id_bien": biens[1]["id"],
            "date_debut": "2023-06-01", "date_fin": "2026-05-31",
            "loyer_hc": 1000, "charges_locatives": 100,
            "depot_garantie": 1000, "statut": "en_cours",
            "indice_irl_reference": "T2 2023",
            "date_revision": "2024-06-01",
            "etat_lieux_entree": "2023-06-01",
        },
        {
            "id": uid(), "id_bien": biens[2]["id"],
            "date_debut": "2024-01-15", "date_fin": "2027-01-14",
            "loyer_hc": 700, "charges_locatives": 80,
            "depot_garantie": 700, "statut": "en_cours",
            "indice_irl_reference": "T4 2023",
            "date_revision": "2025-01-15",
            "etat_lieux_entree": "2024-01-15",
        },
        {
            "id": uid(), "id_bien": bien4["id"],
            "date_debut": "2023-09-01", "date_fin": "2026-08-31",
            "loyer_hc": 1600, "charges_locatives": 200,
            "depot_garantie": 1600, "statut": "en_cours",
            "indice_irl_reference": "T3 2023",
            "date_revision": "2024-09-01",
            "etat_lieux_entree": "2023-09-01",
        },
    ]
    insert("baux", baux)
    print(f"  ✅ {len(baux)} baux créés")

    # Liaison bail-locataire
    bail_locataires = [
        {"id_bail": baux[i]["id"], "id_locataire": locataires[i]["id"]}
        for i in range(4)
    ]
    insert("bail_locataires", bail_locataires)
    print("  ✅ Liaisons bail↔locataire")

    # ── Loyers (12 derniers mois) ───────────────────────────────
    print("\n💰 Création des loyers (12 mois) ...")
    loyer_count = 0
    today = date.today()
    seen_months = set()
    for month_offset in range(12, 0, -1):
        d = today.replace(day=1) - timedelta(days=month_offset * 30)
        loyer_date = d.replace(day=1)
        # Éviter les doublons de mois (timedelta approximatif)
        month_key = (loyer_date.year, loyer_date.month)
        if month_key in seen_months:
            continue
        seen_months.add(month_key)

        for i, bien in enumerate(all_biens):
            montant = [1450, 1100, 780, 1800][i]
            loc = locataires[i]

            # Réalisme: quelques impayés
            if month_offset <= 2:
                statut = "en_attente"  # Mois récents en attente
            elif month_offset == 5 and i == 2:
                statut = "en_retard"  # Lucas en retard sur un mois
            elif month_offset == 8 and i == 0:
                statut = "en_retard"  # Lefebvre en retard un mois
            else:
                statut = "paye"

            insert("loyers", {
                "id": uid(),
                "id_bien": bien["id"],
                "id_locataire": loc["id"],
                "date_loyer": str(loyer_date),
                "montant": montant,
                "statut": statut,
                "quitus_genere": statut == "paye",
            })
            loyer_count += 1

    print(f"  ✅ {loyer_count} loyers créés")

    # ── Charges ─────────────────────────────────────────────────
    print("\n📊 Création des charges ...")
    charge_types = [
        ("copropriete", 250), ("taxe_fonciere", 180),
        ("entretien", 120), ("assurance", 90),
    ]
    charge_count = 0
    for bien in all_biens:
        for type_charge, montant in charge_types:
            for q in range(1, 5):  # 4 trimestres
                insert("charges", {
                    "id": uid(),
                    "id_bien": bien["id"],
                    "type_charge": type_charge,
                    "montant": montant,
                    "date_paiement": f"2025-{q*3:02d}-01",
                })
                charge_count += 1
    print(f"  ✅ {charge_count} charges créées")

    # ── Assurances PNO ──────────────────────────────────────────
    print("\n🛡️  Assurances PNO ...")
    for bien in all_biens:
        insert("assurances_pno", {
            "id": uid(),
            "id_bien": bien["id"],
            "compagnie": "MAIF" if bien["id_sci"] == sci1_id else "AXA",
            "numero_contrat": f"PNO-{bien['code_postal']}-{uid()[:6]}",
            "montant_annuel": 280 if bien["type_locatif"] != "Studio" else 150,
            "date_echeance": "2026-01-01",
        })
    print("  ✅ 4 assurances PNO")

    # ── Frais agence ────────────────────────────────────────────
    print("\n🏪 Frais agence ...")
    insert("frais_agence", {
        "id": uid(),
        "id_bien": bien4["id"],
        "nom_agence": "Nexity Lyon Presqu'île",
        "contact": "04 72 10 20 30",
        "type_frais": "pourcentage",
        "montant_ou_pourcentage": 7.5,
    })
    print("  ✅ 1 frais agence (bien Lyon)")

    # ── Fiscalité ───────────────────────────────────────────────
    print("\n📈 Fiscalité ...")
    for annee in [2024, 2025]:
        insert("fiscalite", {
            "id": uid(),
            "id_sci": sci1_id,
            "annee": annee,
            "total_revenus": 39960 if annee == 2024 else 20000,
            "total_charges": 10240 if annee == 2024 else 5500,
            "resultat_fiscal": 29720 if annee == 2024 else 14500,
        })
        insert("fiscalite", {
            "id": uid(),
            "id_sci": sci2_id,
            "annee": annee,
            "total_revenus": 21600 if annee == 2024 else 10800,
            "total_charges": 5120 if annee == 2024 else 2700,
            "resultat_fiscal": 16480 if annee == 2024 else 8100,
        })
    print("  ✅ Fiscalité 2024 + 2025")

    # ── Abonnement Pro ──────────────────────────────────────────
    print("\n💳 Abonnement Pro ...")
    insert("subscriptions", {
        "id": uid(),
        "user_id": user_id,
        "stripe_customer_id": f"cus_demo_{uid()[:8]}",
        "stripe_subscription_id": f"sub_demo_{uid()[:8]}",
        "stripe_price_id": "price_pro_demo",
        "mode": "subscription",
        "status": "active",
        "current_period_end": str(today + timedelta(days=30)),
        "onboarding_completed": True,
    })
    print("  ✅ Abonnement Pro actif")

    # ── Notifications ───────────────────────────────────────────
    print("\n🔔 Notifications ...")
    # Insert notifications one by one (different columns per row)
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "late_payment",
        "title": "Loyer impayé — Studio Commerce",
        "message": "Le loyer de Lucas Bernard (8 rue du Commerce) est en retard depuis 15 jours.",
        "metadata": {"bien_id": biens[2]["id"], "locataire": "Lucas Bernard"},
    })
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "info",
        "title": "Bienvenue sur GererSCI !",
        "message": "Votre espace de gestion SCI est prêt. Découvrez toutes les fonctionnalités.",
        "metadata": {},
        "read_at": str(datetime.now(timezone.utc)),
    })
    insert("notifications", {
        "id": uid(), "user_id": user_id,
        "type": "system",
        "title": "Bail bientôt expiré",
        "message": "Le bail de Jean-Marc Lefebvre (12 rue de Belleville) expire dans 9 mois.",
        "metadata": {"bail_id": baux[0]["id"]},
    })
    notifs = [1, 2, 3]  # count placeholder
    print(f"  ✅ {len(notifs)} notifications")

    # ── Préférences notifications ───────────────────────────────
    for ntype in ["late_payment", "status_change", "document_ready", "system"]:
        insert("notification_preferences", {
            "id": uid(), "user_id": user_id, "type": ntype,
            "email_enabled": ntype in ("late_payment", "document_ready"),
            "in_app_enabled": True,
        })
    print("  ✅ Préférences notifications")

    # ── Admin flag ──────────────────────────────────────────────
    print("\n👑 Admin flag ...")
    insert("admins", {"user_id": user_id})
    print("  ✅ User est admin")

    # ── Résumé ──────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("🎉 Seed terminé avec succès !")
    print("=" * 50)
    print(f"""
📧 Email:    {DEMO_EMAIL}
🔑 Password: {DEMO_PASSWORD}
👑 Admin:    oui

📊 Données créées:
  • 2 SCI (Belleville Patrimoine IR + Horizon Lyon IS)
  • 4 biens (3 Paris + 1 Lyon)
  • 4 locataires avec baux actifs
  • {loyer_count} loyers (mix payé/impayé/en attente)
  • {charge_count} charges trimestrielles
  • 4 assurances PNO
  • 1 frais agence
  • Fiscalité 2024-2025
  • Abonnement Pro actif
  • 3 notifications + préférences

🌐 URLs:
  • Frontend:  http://localhost:5173
  • Backend:   http://localhost:8000
  • Supabase:  http://localhost:54323 (Studio)
  • Mailpit:   http://localhost:54324 (Emails)
""")


if __name__ == "__main__":
    main()
