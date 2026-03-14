"""
Seed script: marketing-quality demo data for screenshots and demos.

Usage:
    cd backend && python scripts/seed_marketing_data.py

Creates ONE perfect user (sophie@gerersci.fr / password123) with:
- 2 SCI (Paris + Lyon)
- 4 biens immobiliers
- 12 months of loyers ALL status="paye" (100% recouvrement)
- Charges, assurances PNO, frais agence
- Fiscalite 2025
- Pro subscription active

Idempotent: deletes existing data for sophie@gerersci.fr before seeding.
"""
import os
import sys
import uuid
from datetime import date, timedelta

import httpx

# ── Config ──────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
)
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "price_1TAyt3BCxd3SKdGJeNgk9G3E")

SOPHIE_EMAIL = "sophie@gerersci.fr"
SOPHIE_PASSWORD = "password123"

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation,resolution=merge-duplicates",
}


def api(method: str, path: str, json=None):
    url = f"{SUPABASE_URL}{path}"
    r = httpx.request(method, url, headers=HEADERS, json=json, timeout=15)
    if r.status_code >= 400:
        print(f"  ⚠️  {method} {path} → {r.status_code}: {r.text[:200]}")
        return None
    try:
        return r.json()
    except Exception:
        return r.text


def insert(table: str, data: dict | list, critical: bool = False):
    result = api("POST", f"/rest/v1/{table}", json=data)
    if result is None and critical:
        print(f"  ❌ CRITICAL: Failed to insert into {table}. Aborting.")
        sys.exit(1)
    return result


def uid():
    return str(uuid.uuid4())


# Known SIRENs used by this seed (for orphan cleanup)
MARKETING_SIRENS = ["823456789", "912345678"]


# ── Cleanup ────────────────────────────────────────────────────
def delete_sci_cascade(sci_id: str):
    """Delete a SCI and all its dependent data (FK order)."""
    # Get bien ids for this SCI
    bien_rows = api("GET", f"/rest/v1/biens?id_sci=eq.{sci_id}&select=id")
    bien_ids = [r["id"] for r in (bien_rows or []) if r.get("id")]

    for bien_id in bien_ids:
        # Delete dependent data per bien (FK order)
        api("DELETE", f"/rest/v1/frais_agence?id_bien=eq.{bien_id}")
        api("DELETE", f"/rest/v1/assurances_pno?id_bien=eq.{bien_id}")
        api("DELETE", f"/rest/v1/charges?id_bien=eq.{bien_id}")
        # Get baux for bail_locataires
        baux_rows = api("GET", f"/rest/v1/baux?id_bien=eq.{bien_id}&select=id")
        for bail in (baux_rows or []):
            if bail.get("id"):
                api("DELETE", f"/rest/v1/bail_locataires?id_bail=eq.{bail['id']}")
        api("DELETE", f"/rest/v1/baux?id_bien=eq.{bien_id}")
        api("DELETE", f"/rest/v1/locataires?id_bien=eq.{bien_id}")
        api("DELETE", f"/rest/v1/documents_bien?id_bien=eq.{bien_id}")

    # Delete loyers, biens, fiscalite, associes, sci
    api("DELETE", f"/rest/v1/loyers?id_sci=eq.{sci_id}")
    api("DELETE", f"/rest/v1/fiscalite?id_sci=eq.{sci_id}")
    for bien_id in bien_ids:
        api("DELETE", f"/rest/v1/biens?id=eq.{bien_id}")
    api("DELETE", f"/rest/v1/associes?id_sci=eq.{sci_id}")
    api("DELETE", f"/rest/v1/sci?id=eq.{sci_id}")
    print(f"  ↳ SCI {sci_id} et données associées supprimées")


def cleanup_sophie():
    """Delete all existing data for sophie@gerersci.fr (idempotent re-seed)."""
    print("\n🧹 Nettoyage des données existantes ...")

    # 1. Clean up any orphan SCIs by known SIREN (handles partial previous runs)
    for siren in MARKETING_SIRENS:
        sci_rows = api("GET", f"/rest/v1/sci?siren=eq.{siren}&select=id")
        for row in (sci_rows or []):
            if row.get("id"):
                delete_sci_cascade(row["id"])

    # 2. Find Sophie's user_id and clean user-level data
    users = api("GET", "/auth/v1/admin/users?page=1&per_page=100")
    sophie_id = None
    if users and "users" in users:
        for u in users["users"]:
            if u.get("email") == SOPHIE_EMAIL:
                sophie_id = u["id"]

    if sophie_id:
        print(f"  ↳ User trouvé: {sophie_id}")

        # Get any remaining SCI ids owned by Sophie
        sci_rows = api("GET", f"/rest/v1/associes?user_id=eq.{sophie_id}&select=id_sci")
        for row in (sci_rows or []):
            if row.get("id_sci"):
                delete_sci_cascade(row["id_sci"])

        # Delete subscription, notifications, notification_preferences, admin
        api("DELETE", f"/rest/v1/subscriptions?user_id=eq.{sophie_id}")
        api("DELETE", f"/rest/v1/notifications?user_id=eq.{sophie_id}")
        api("DELETE", f"/rest/v1/notification_preferences?user_id=eq.{sophie_id}")
        api("DELETE", f"/rest/v1/admins?user_id=eq.{sophie_id}")

        # Delete auth user
        api("DELETE", f"/auth/v1/admin/users/{sophie_id}")
        print(f"  ↳ User auth {SOPHIE_EMAIL} supprimé")
    else:
        print("  ↳ Aucun user existant trouvé")

    print("  ✅ Nettoyage terminé")


# ── Main ───────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("SEED MARKETING — Données de démonstration parfaites")
    print("=" * 60)

    cleanup_sophie()

    # ── 1. Create Sophie user ──────────────────────────────────
    print("\n👤 Création utilisateur sophie@gerersci.fr ...")
    user_resp = api("POST", "/auth/v1/admin/users", json={
        "email": SOPHIE_EMAIL,
        "password": SOPHIE_PASSWORD,
        "email_confirm": True,
        "user_metadata": {"full_name": "Sophie Moreau"},
    })
    if user_resp and isinstance(user_resp, dict) and "id" in user_resp:
        sophie_id = user_resp["id"]
        print(f"  ✅ User créé: {sophie_id}")
    else:
        print("  ❌ Impossible de créer l'utilisateur")
        sys.exit(1)

    # ── 2. Pro subscription ────────────────────────────────────
    print("\n💳 Abonnement Pro ...")
    today = date.today()
    insert("subscriptions", {
        "user_id": sophie_id,
        "stripe_customer_id": f"cus_marketing_{uid()[:8]}",
        "stripe_subscription_id": f"sub_marketing_{uid()[:8]}",
        "stripe_price_id": STRIPE_PRO_PRICE_ID,
        "mode": "subscription",
        "status": "active",
        "current_period_end": str(today + timedelta(days=30)),
        "onboarding_completed": True,
    })
    print("  ✅ Abonnement Pro actif")

    # ════════════════════════════════════════════════════════════
    # SCI 1 — SCI Résidence Belleville
    # ════════════════════════════════════════════════════════════
    print("\n🏢 SCI 1: SCI Résidence Belleville ...")
    sci1_id = uid()
    insert("sci", {
        "id": sci1_id,
        "nom": "SCI Résidence Belleville",
        "siren": "823456789",
        "regime_fiscal": "IR",
        "capital_social": 150000,
        "adresse_siege": "12 rue de Belleville, 75020 Paris",
    }, critical=True)
    print(f"  ✅ SCI créée: {sci1_id}")

    # Associés SCI 1 (insert separately: user_id differs)
    insert("associes", {
        "id": uid(), "id_sci": sci1_id, "user_id": sophie_id,
        "nom": "Sophie Moreau", "email": SOPHIE_EMAIL,
        "part": 60, "role": "gerant",
    }, critical=True)
    insert("associes", {
        "id": uid(), "id_sci": sci1_id,
        "nom": "Marc Moreau", "email": "marc.moreau@famille.fr",
        "part": 40, "role": "associe",
    })
    print("  ✅ 2 associés (Sophie 60%, Marc 40%)")

    # Bien 1.1 — T3 Belleville
    bien1_1_id = uid()
    insert("biens", {
        "id": bien1_1_id, "id_sci": sci1_id,
        "adresse": "12 rue de Belleville", "ville": "Paris",
        "code_postal": "75020", "type_locatif": "nu",
        "loyer_cc": 1430, "charges": 180, "tmi": 30,
        "surface_m2": 65, "nb_pieces": 3, "dpe_classe": "D",
        "prix_acquisition": 310000,
        "acquisition_date": "2020-03-15",
    })
    print("  ✅ Bien 1: T3 Belleville (65m², 1250€ HC + 180€ charges)")

    # Bien 1.2 — Studio Les Lilas
    bien1_2_id = uid()
    insert("biens", {
        "id": bien1_2_id, "id_sci": sci1_id,
        "adresse": "8 rue des Lilas", "ville": "Paris",
        "code_postal": "75020", "type_locatif": "meuble",
        "loyer_cc": 840, "charges": 90, "tmi": 30,
        "surface_m2": 28, "nb_pieces": 1, "dpe_classe": "C",
        "prix_acquisition": 185000,
        "acquisition_date": "2021-09-01",
    })
    print("  ✅ Bien 2: Studio Les Lilas (28m², 750€ HC + 90€ charges)")

    # Locataires SCI 1
    loc1_1_id = uid()
    insert("locataires", {
        "id": loc1_1_id, "id_bien": bien1_1_id,
        "nom": "Julien Lefèvre", "email": "julien.lefevre@email.fr",
        "telephone": "06 12 34 56 78",
        "date_debut": "2023-04-01",
    })
    loc1_2_id = uid()
    insert("locataires", {
        "id": loc1_2_id, "id_bien": bien1_2_id,
        "nom": "Camille Petit", "email": "camille.petit@email.fr",
        "telephone": "06 98 76 54 32",
        "date_debut": "2023-10-01",
    })
    print("  ✅ 2 locataires")

    # Baux SCI 1
    bail1_1_id = uid()
    insert("baux", {
        "id": bail1_1_id, "id_bien": bien1_1_id,
        "date_debut": "2023-04-01", "date_fin": "2026-03-31",
        "loyer_hc": 1250, "charges_locatives": 180,
        "depot_garantie": 1250, "statut": "en_cours",
        "indice_irl_reference": "T1 2023",
        "date_revision": "2024-04-01",
        "etat_lieux_entree": "2023-04-01",
    })
    bail1_2_id = uid()
    insert("baux", {
        "id": bail1_2_id, "id_bien": bien1_2_id,
        "date_debut": "2023-10-01", "date_fin": "2024-09-30",
        "loyer_hc": 750, "charges_locatives": 90,
        "depot_garantie": 750, "statut": "en_cours",
        "indice_irl_reference": "T3 2023",
        "date_revision": "2024-10-01",
        "etat_lieux_entree": "2023-10-01",
    })
    print("  ✅ 2 baux actifs")

    # Bail-locataire links
    insert("bail_locataires", [
        {"id_bail": bail1_1_id, "id_locataire": loc1_1_id},
        {"id_bail": bail1_2_id, "id_locataire": loc1_2_id},
    ])
    print("  ✅ Liaisons bail↔locataire")

    # ════════════════════════════════════════════════════════════
    # SCI 2 — SCI Patrimoine Lyon
    # ════════════════════════════════════════════════════════════
    print("\n🏢 SCI 2: SCI Patrimoine Lyon ...")
    sci2_id = uid()
    insert("sci", {
        "id": sci2_id,
        "nom": "SCI Patrimoine Lyon",
        "siren": "912345678",
        "regime_fiscal": "IS",
        "capital_social": 200000,
        "adresse_siege": "45 avenue Jean Jaurès, 69007 Lyon",
    }, critical=True)
    print(f"  ✅ SCI créée: {sci2_id}")

    # Associés SCI 2 (3 associés, insert separately for key consistency)
    insert("associes", {
        "id": uid(), "id_sci": sci2_id, "user_id": sophie_id,
        "nom": "Sophie Moreau", "email": SOPHIE_EMAIL,
        "part": 50, "role": "gerant",
    }, critical=True)
    insert("associes", {
        "id": uid(), "id_sci": sci2_id,
        "nom": "Antoine Moreau", "email": "antoine.moreau@famille.fr",
        "part": 30, "role": "associe",
    })
    insert("associes", {
        "id": uid(), "id_sci": sci2_id,
        "nom": "Claire Durand", "email": "claire.durand@cabinet.fr",
        "part": 20, "role": "associe",
    })
    print("  ✅ 3 associés (Sophie 50%, Antoine 30%, Claire 20%)")

    # Bien 2.1 — T4 Jean Jaurès
    bien2_1_id = uid()
    insert("biens", {
        "id": bien2_1_id, "id_sci": sci2_id,
        "adresse": "45 avenue Jean Jaurès", "ville": "Lyon",
        "code_postal": "69007", "type_locatif": "nu",
        "loyer_cc": 1250, "charges": 150, "tmi": 30,
        "surface_m2": 85, "nb_pieces": 4, "dpe_classe": "C",
        "prix_acquisition": 280000,
        "acquisition_date": "2019-11-20",
    })
    print("  ✅ Bien 3: T4 Jean Jaurès (85m², 1100€ HC + 150€ charges)")

    # Bien 2.2 — Local commercial Victor Hugo
    bien2_2_id = uid()
    insert("biens", {
        "id": bien2_2_id, "id_sci": sci2_id,
        "adresse": "22 rue Victor Hugo", "ville": "Lyon",
        "code_postal": "69002", "type_locatif": "commercial",
        "loyer_cc": 3150, "charges": 350, "tmi": 30,
        "surface_m2": 120, "nb_pieces": 3, "dpe_classe": "B",
        "prix_acquisition": 520000,
        "acquisition_date": "2021-06-10",
    })
    print("  ✅ Bien 4: Local commercial Victor Hugo (120m², 2800€ HC + 350€ charges)")

    # Locataires SCI 2
    loc2_1_id = uid()
    insert("locataires", {
        "id": loc2_1_id, "id_bien": bien2_1_id,
        "nom": "Famille Nguyen", "email": "nguyen.famille@email.fr",
        "telephone": "04 72 11 22 33",
        "date_debut": "2023-01-15",
    })
    loc2_2_id = uid()
    insert("locataires", {
        "id": loc2_2_id, "id_bien": bien2_2_id,
        "nom": "SARL Boulangerie Victor Hugo", "email": "contact@boulangerie-vh.fr",
        "telephone": "04 78 44 55 66",
        "date_debut": "2022-06-01",
    })
    print("  ✅ 2 locataires")

    # Baux SCI 2
    bail2_1_id = uid()
    insert("baux", {
        "id": bail2_1_id, "id_bien": bien2_1_id,
        "date_debut": "2023-01-15", "date_fin": "2026-01-14",
        "loyer_hc": 1100, "charges_locatives": 150,
        "depot_garantie": 1100, "statut": "en_cours",
        "indice_irl_reference": "T4 2022",
        "date_revision": "2024-01-15",
        "etat_lieux_entree": "2023-01-15",
    })
    bail2_2_id = uid()
    insert("baux", {
        "id": bail2_2_id, "id_bien": bien2_2_id,
        "date_debut": "2022-06-01", "date_fin": "2031-05-31",
        "loyer_hc": 2800, "charges_locatives": 350,
        "depot_garantie": 5600, "statut": "en_cours",
        "indice_irl_reference": "T2 2022",
        "date_revision": "2023-06-01",
        "etat_lieux_entree": "2022-06-01",
    })
    print("  ✅ 2 baux actifs (résidentiel 3 ans + commercial 9 ans)")

    insert("bail_locataires", [
        {"id_bail": bail2_1_id, "id_locataire": loc2_1_id},
        {"id_bail": bail2_2_id, "id_locataire": loc2_2_id},
    ])
    print("  ✅ Liaisons bail↔locataire")

    # ════════════════════════════════════════════════════════════
    # Loyers — 12 mois, ALL status="paye"
    # ════════════════════════════════════════════════════════════
    print("\n💰 Création des loyers (12 mois, tous payés) ...")
    all_biens_config = [
        {"id": bien1_1_id, "id_sci": sci1_id, "montant": 1250, "loc_id": loc1_1_id},
        {"id": bien1_2_id, "id_sci": sci1_id, "montant": 750, "loc_id": loc1_2_id},
        {"id": bien2_1_id, "id_sci": sci2_id, "montant": 1100, "loc_id": loc2_1_id},
        {"id": bien2_2_id, "id_sci": sci2_id, "montant": 2800, "loc_id": loc2_2_id},
    ]

    loyer_count = 0
    loyers_batch = []
    for month_offset in range(12, 0, -1):
        # Calculate month: go back month_offset months from today
        year = today.year
        month = today.month - month_offset
        while month <= 0:
            month += 12
            year -= 1
        loyer_date = date(year, month, 1)

        for bien_cfg in all_biens_config:
            loyers_batch.append({
                "id": uid(),
                "id_bien": bien_cfg["id"],
                "id_sci": bien_cfg["id_sci"],
                "id_locataire": bien_cfg["loc_id"],
                "date_loyer": str(loyer_date),
                "montant": bien_cfg["montant"],
                "statut": "paye",
                "quitus_genere": True,
            })
            loyer_count += 1

    # Insert in batches of 12 to avoid too-large requests
    for i in range(0, len(loyers_batch), 12):
        insert("loyers", loyers_batch[i:i + 12])
    print(f"  ✅ {loyer_count} loyers créés (tous payés)")

    # ════════════════════════════════════════════════════════════
    # Charges
    # ════════════════════════════════════════════════════════════
    print("\n📊 Création des charges ...")
    charge_count = 0
    all_bien_ids = [bien1_1_id, bien1_2_id, bien2_1_id, bien2_2_id]
    taxe_fonciere = [1200, 600, 950, 2400]
    copropriete = [2400, 1200, 1800, 3600]

    for idx, bien_id in enumerate(all_bien_ids):
        # Taxe foncière (annual, paid in Q4)
        insert("charges", {
            "id": uid(), "id_bien": bien_id,
            "type_charge": "taxe_fonciere",
            "montant": taxe_fonciere[idx],
            "date_paiement": "2025-10-15",
        })
        charge_count += 1

        # Copropriété (quarterly)
        quarterly_amount = copropriete[idx] // 4
        for q in range(1, 5):
            insert("charges", {
                "id": uid(), "id_bien": bien_id,
                "type_charge": "copropriete",
                "montant": quarterly_amount,
                "date_paiement": f"2025-{q * 3:02d}-01",
            })
            charge_count += 1

    print(f"  ✅ {charge_count} charges créées")

    # ════════════════════════════════════════════════════════════
    # Assurances PNO
    # ════════════════════════════════════════════════════════════
    print("\n🛡️  Assurances PNO ...")
    pno_data = [
        (bien1_1_id, "AXA", 400, "PNO-2024-BEL-001"),
        (bien1_2_id, "AXA", 280, "PNO-2024-LIL-002"),
        (bien2_1_id, "MAIF", 350, "PNO-2024-JJA-003"),
        (bien2_2_id, "MAIF", 550, "PNO-2024-VHU-004"),
    ]
    for bien_id, compagnie, montant, contrat in pno_data:
        insert("assurances_pno", {
            "id": uid(), "id_bien": bien_id,
            "compagnie": compagnie,
            "numero_contrat": contrat,
            "montant_annuel": montant,
            "date_echeance": "2026-01-01",
        })
    print("  ✅ 4 assurances PNO (AXA Paris, MAIF Lyon)")

    # ════════════════════════════════════════════════════════════
    # Frais agence
    # ════════════════════════════════════════════════════════════
    print("\n🏪 Frais agence ...")
    insert("frais_agence", {
        "id": uid(), "id_bien": bien1_1_id,
        "nom_agence": "Agence Belleville Immobilier",
        "contact": "01 43 58 12 34",
        "type_frais": "fixe",
        "montant_ou_pourcentage": 80,
    })
    print("  ✅ 1 frais agence (Bien 1, fixe 80€/mois)")

    # ════════════════════════════════════════════════════════════
    # Fiscalité 2025
    # ════════════════════════════════════════════════════════════
    print("\n📈 Fiscalité 2025 ...")

    # SCI 1: 12 months * (1250 + 750) = 24,000€ revenus
    sci1_revenus = 12 * (1250 + 750)  # 24,000
    sci1_charges = (1200 + 600) + (2400 + 1200) + (400 + 280) + (80 * 12)  # 7,040
    insert("fiscalite", {
        "id": uid(), "id_sci": sci1_id,
        "annee": 2025,
        "total_revenus": sci1_revenus,
        "total_charges": sci1_charges,
        "resultat_fiscal": sci1_revenus - sci1_charges,
    })

    # SCI 2: 12 months * (1100 + 2800) = 46,800€ revenus
    sci2_revenus = 12 * (1100 + 2800)  # 46,800
    sci2_charges = (950 + 2400) + (1800 + 3600) + (350 + 550)  # 9,650
    insert("fiscalite", {
        "id": uid(), "id_sci": sci2_id,
        "annee": 2025,
        "total_revenus": sci2_revenus,
        "total_charges": sci2_charges,
        "resultat_fiscal": sci2_revenus - sci2_charges,
    })
    print(f"  ✅ Fiscalité 2025: SCI 1 = {sci1_revenus - sci1_charges}€, SCI 2 = {sci2_revenus - sci2_charges}€")

    # ════════════════════════════════════════════════════════════
    # Admin flag (for admin panel access)
    # ════════════════════════════════════════════════════════════
    print("\n👑 Admin flag ...")
    insert("admins", {"user_id": sophie_id})
    print("  ✅ Sophie est admin")

    # ── Summary ────────────────────────────────────────────────
    total_loyers_mensuel = 1250 + 750 + 1100 + 2800
    print("\n" + "=" * 60)
    print("🎉 SEED MARKETING TERMINÉ")
    print("=" * 60)
    print(f"""
📧 Email:    {SOPHIE_EMAIL}
🔑 Password: {SOPHIE_PASSWORD}
👑 Admin:    oui
💳 Plan:     Pro (actif)

📊 Données créées:
  • 2 SCI
    ├─ SCI Résidence Belleville (IR, 150k€, Paris 75020)
    │  ├─ T3 Belleville    — 65m² — 1 250€ HC + 180€ charges
    │  └─ Studio Les Lilas — 28m² —   750€ HC +  90€ charges
    └─ SCI Patrimoine Lyon (IS, 200k€, Lyon)
       ├─ T4 Jean Jaurès         —  85m² — 1 100€ HC + 150€ charges
       └─ Local Victor Hugo      — 120m² — 2 800€ HC + 350€ charges
  • 4 biens, 4 locataires, 4 baux actifs
  • {loyer_count} loyers (100% payés)
  • Revenus mensuels: {total_loyers_mensuel}€
  • Revenus annuels: {total_loyers_mensuel * 12}€
  • Charges annuelles: {sci1_charges + sci2_charges}€

🎯 Dashboard attendu:
  • 100% taux de recouvrement
  • 0 alertes
  • 2 SCI, 4 biens
  • Cashflow positif

🌐 URLs:
  • Frontend:  http://localhost:5173
  • Backend:   http://localhost:8000
  • Supabase:  http://localhost:54323 (Studio)
""")


if __name__ == "__main__":
    main()
