"""
Seed complet GérerSCI — TOUS les champs de TOUTES les tables.

Usage: cd backend && python scripts/seed_dev_data.py [--clean]
"""
import os, sys, uuid
from datetime import date, datetime, timedelta, timezone
import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
)
DEMO_EMAIL = "demo@gerersci.fr"
DEMO_PASSWORD = "password123"
HEADERS = {
    "apikey": SERVICE_ROLE_KEY, "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation,resolution=merge-duplicates",
}

def api(method, path, json=None):
    r = httpx.request(method, f"{SUPABASE_URL}{path}", headers=HEADERS, json=json, timeout=15)
    if r.status_code >= 400:
        print(f"  ⚠️  {method} {path} → {r.status_code}: {r.text[:200]}")
        return None
    try: return r.json()
    except: return r.text

def insert(table, data): return api("POST", f"/rest/v1/{table}", json=data)
def delete_all(table):
    pk = {"bail_locataires": "id_bail", "admins": "user_id", "quittance_compteur": "sci_id"}.get(table, "id")
    return api("DELETE", f"/rest/v1/{table}?{pk}=neq.00000000-0000-0000-0000-000000000000")
def uid(): return str(uuid.uuid4())

def create_or_find_user(email, password, name):
    resp = api("POST", "/auth/v1/admin/users", json={"email": email, "password": password, "email_confirm": True, "user_metadata": {"full_name": name}})
    if resp and isinstance(resp, dict) and "id" in resp: return resp["id"]
    users = api("GET", "/auth/v1/admin/users?page=1&per_page=50")
    if users and "users" in users:
        for u in users["users"]:
            if u.get("email") == email: return u["id"]
    return None

def clean():
    print("\n🧹 Nettoyage ...")
    for t in ["notification_preferences", "notifications", "deficit_reportable", "quittance_compteur",
              "mouvements_parts", "assemblees_generales", "bail_locataires", "loyers", "frais_agence",
              "assurances_pno", "documents_bien", "evenements_bien", "charges", "baux", "locataires",
              "fiscalite", "biens", "associes", "sci", "subscriptions", "admins"]:
        delete_all(t)
    users = api("GET", "/auth/v1/admin/users?page=1&per_page=50")
    if users and "users" in users:
        for u in users["users"]:
            if u["email"] in (DEMO_EMAIL, "pierre.martin@gerersci.fr"):
                api("DELETE", f"/auth/v1/admin/users/{u['id']}")
    print("  ✅ OK")


def main():
    if "--clean" in sys.argv or "--reset" in sys.argv: clean()
    print("\n🌱 Seed GérerSCI — données complètes (tous les champs)")
    print("=" * 60)
    today = date.today()

    # ── Users ─────────────────────────────────────────────────────
    user_id = create_or_find_user(DEMO_EMAIL, DEMO_PASSWORD, "Marie Dupont")
    user2_id = create_or_find_user("pierre.martin@gerersci.fr", "password123", "Pierre Martin")
    print(f"  ✅ 2 users: {DEMO_EMAIL}, pierre.martin@gerersci.fr")

    # ── SCI 1: Belleville (IR) ────────────────────────────────────
    sci1_id = uid()
    insert("sci", {
        "id": sci1_id, "nom": "SCI Belleville Patrimoine",
        "siren": "912345678", "regime_fiscal": "IR",
        "capital_social": 150000, "nb_parts_total": 1000, "valeur_nominale_part": 150,
        "objet_social": "Acquisition et gestion de biens immobiliers à Paris et Île-de-France",
        "date_creation": "2019-01-15",
        "rcs_ville": "Paris", "rcs_numero": "912 345 678",
        "forme_juridique": "SCI", "nom_gerant": "Marie Dupont",
        "adresse_siege": "12 rue de Belleville, 75020 Paris",
    })

    # ── SCI 2: Lyon (IS) ─────────────────────────────────────────
    sci2_id = uid()
    insert("sci", {
        "id": sci2_id, "nom": "SCI Horizon Lyon",
        "siren": "987654321", "regime_fiscal": "IS",
        "capital_social": 200000, "nb_parts_total": 500, "valeur_nominale_part": 400,
        "objet_social": "Gestion patrimoniale immobilière dans la métropole de Lyon",
        "date_creation": "2022-06-01",
        "rcs_ville": "Lyon", "rcs_numero": "987 654 321",
        "forme_juridique": "SCI", "nom_gerant": "Marie Dupont",
        "adresse_siege": "15 rue de la République, 69002 Lyon",
    })
    print("  ✅ 2 SCI (IR + IS) avec tous les champs légaux")

    # ── Associés ──────────────────────────────────────────────────
    assoc1 = [
        {"id": uid(), "id_sci": sci1_id, "user_id": user_id,
         "nom": "Marie Dupont", "email": DEMO_EMAIL,
         "part": 60, "nb_parts": 600, "role": "gerant"},
    ]
    if user2_id:
        assoc1.append({"id": uid(), "id_sci": sci1_id, "user_id": user2_id,
         "nom": "Pierre Martin", "email": "pierre.martin@gerersci.fr",
         "part": 40, "nb_parts": 400, "role": "associe"})
    insert("associes", assoc1)
    insert("associes", {"id": uid(), "id_sci": sci2_id, "user_id": user_id,
         "nom": "Marie Dupont", "email": DEMO_EMAIL,
         "part": 100, "nb_parts": 500, "role": "gerant"})
    print(f"  ✅ {len(assoc1)+1} associés avec nb_parts")

    # ── Biens (TOUS les champs) ───────────────────────────────────
    biens = [
        {"id": uid(), "id_sci": sci1_id,
         "adresse": "12 rue de Belleville — Apt 1", "ville": "Paris", "code_postal": "75020",
         "type_locatif": "nu", "type_bien": "appartement",
         "loyer_cc": 1450, "charges": 150, "tmi": 30,
         "surface_m2": 65, "nb_pieces": 3, "dpe_classe": "D",
         "prix_acquisition": 320000, "acquisition_date": "2019-06-15",
         "dpe_date": "2023-05-10",
         "diagnostic_amiante_date": "2019-06-01",
         "diagnostic_electricite_date": "2022-03-15",
         "diagnostic_gaz_date": "2022-03-15",
         "diagnostic_plomb_date": "2019-06-01",
         "photo_url": None},
        {"id": uid(), "id_sci": sci1_id,
         "adresse": "12 rue de Belleville — Apt 2", "ville": "Paris", "code_postal": "75020",
         "type_locatif": "meuble", "type_bien": "appartement",
         "loyer_cc": 1100, "charges": 100, "tmi": 30,
         "surface_m2": 42, "nb_pieces": 2, "dpe_classe": "C",
         "prix_acquisition": 245000, "acquisition_date": "2020-03-01",
         "dpe_date": "2023-05-10",
         "diagnostic_amiante_date": "2020-02-15",
         "diagnostic_electricite_date": "2022-03-15",
         "diagnostic_gaz_date": "2022-03-15",
         "diagnostic_plomb_date": "2020-02-15",
         "photo_url": None},
        {"id": uid(), "id_sci": sci1_id,
         "adresse": "8 rue du Commerce — Studio", "ville": "Paris", "code_postal": "75015",
         "type_locatif": "nu", "type_bien": "appartement",
         "loyer_cc": 780, "charges": 80, "tmi": 30,
         "surface_m2": 22, "nb_pieces": 1, "dpe_classe": "E",
         "prix_acquisition": 175000, "acquisition_date": "2021-09-10",
         "dpe_date": "2016-03-01",  # DPE 10y validity → expires 2026-02 → dépassée/critique
         "diagnostic_amiante_date": "2021-08-20",
         "diagnostic_electricite_date": "2021-08-20",
         "diagnostic_gaz_date": None,
         "diagnostic_plomb_date": "2021-08-20",
         "photo_url": None},
        {"id": uid(), "id_sci": sci2_id,
         "adresse": "15 rue de la République", "ville": "Lyon", "code_postal": "69002",
         "type_locatif": "nu", "type_bien": "maison",
         "loyer_cc": 1800, "charges": 200, "tmi": 30,
         "surface_m2": 95, "nb_pieces": 4, "dpe_classe": "B",
         "prix_acquisition": 410000, "acquisition_date": "2022-01-20",
         "dpe_date": "2022-01-10",
         "diagnostic_amiante_date": "2022-01-05",
         "diagnostic_electricite_date": "2022-01-05",
         "diagnostic_gaz_date": "2022-01-05",
         "diagnostic_plomb_date": "2022-01-05",
         "photo_url": None},
        {"id": uid(), "id_sci": sci2_id,
         "adresse": "22 cours Lafayette — Local A", "ville": "Lyon", "code_postal": "69003",
         "type_locatif": "nu", "type_bien": "local_commercial",
         "loyer_cc": 2200, "charges": 300, "tmi": 30,
         "surface_m2": 55, "nb_pieces": 2, "dpe_classe": "C",
         "prix_acquisition": 280000, "acquisition_date": "2023-04-15",
         "dpe_date": "2023-04-01",
         "diagnostic_amiante_date": "2023-03-20",
         "diagnostic_electricite_date": "2023-03-20",
         "diagnostic_gaz_date": None,
         "diagnostic_plomb_date": None,
         "photo_url": None},
    ]
    insert("biens", biens)
    print(f"  ✅ {len(biens)} biens (tous les champs: DPE, diagnostics, acquisition)")

    # ── Locataires ────────────────────────────────────────────────
    locataires = [
        {"id": uid(), "id_bien": biens[0]["id"], "nom": "Jean-Marc Lefebvre",
         "email": "jm.lefebvre@email.fr", "telephone": "06 12 34 56 78",
         "date_debut": "2023-01-01", "date_fin": None},
        {"id": uid(), "id_bien": biens[1]["id"], "nom": "Sophie Nguyen",
         "email": "sophie.nguyen@email.fr", "telephone": "06 98 76 54 32",
         "date_debut": "2023-06-01", "date_fin": None},
        {"id": uid(), "id_bien": biens[2]["id"], "nom": "Lucas Bernard",
         "email": "lucas.b@email.fr", "telephone": "07 11 22 33 44",
         "date_debut": "2024-01-15", "date_fin": None},
        {"id": uid(), "id_bien": biens[3]["id"], "nom": "Famille Moreau",
         "email": "moreau.famille@email.fr", "telephone": "06 55 44 33 22",
         "date_debut": "2023-09-01", "date_fin": None},
        {"id": uid(), "id_bien": biens[4]["id"], "nom": "SARL Boulangerie Centrale",
         "email": "contact@boulangerie-centrale.fr", "telephone": "04 78 99 88 77",
         "date_debut": "2024-03-01", "date_fin": None},
    ]
    insert("locataires", locataires)
    print(f"  ✅ {len(locataires)} locataires (avec date_debut, telephone, email)")

    # ── Baux (TOUS les champs) ────────────────────────────────────
    baux = [
        {"id": uid(), "id_bien": biens[0]["id"],
         "date_debut": "2023-01-01", "date_fin": "2025-12-31",  # EXPIRED → dépassée
         "loyer_hc": 1300, "charges_locatives": 150, "depot_garantie": 1300,
         "statut": "en_cours",
         "indice_irl_reference": "T1 2023", "date_revision": "2024-01-01",
         "etat_lieux_entree": "2023-01-01", "etat_lieux_sortie": None,
         "document_url": None},
        {"id": uid(), "id_bien": biens[1]["id"],
         "date_debut": "2023-06-01", "date_fin": "2026-05-31",
         "loyer_hc": 1000, "charges_locatives": 100, "depot_garantie": 1000,
         "statut": "en_cours",
         "indice_irl_reference": "T2 2023", "date_revision": "2024-06-01",
         "etat_lieux_entree": "2023-06-01", "etat_lieux_sortie": None,
         "document_url": None},
        {"id": uid(), "id_bien": biens[2]["id"],
         "date_debut": "2024-01-15", "date_fin": "2027-01-14",
         "loyer_hc": 700, "charges_locatives": 80, "depot_garantie": 700,
         "statut": "en_cours",
         "indice_irl_reference": "T4 2023", "date_revision": "2025-01-15",
         "etat_lieux_entree": "2024-01-15", "etat_lieux_sortie": None,
         "document_url": None},
        {"id": uid(), "id_bien": biens[3]["id"],
         "date_debut": "2023-09-01", "date_fin": "2026-08-31",
         "loyer_hc": 1600, "charges_locatives": 200, "depot_garantie": 1600,
         "statut": "en_cours",
         "indice_irl_reference": "T3 2023", "date_revision": "2024-09-01",
         "etat_lieux_entree": "2023-09-01", "etat_lieux_sortie": None,
         "document_url": None},
        {"id": uid(), "id_bien": biens[4]["id"],
         "date_debut": "2024-03-01", "date_fin": "2030-02-28",
         "loyer_hc": 1900, "charges_locatives": 300, "depot_garantie": 3800,
         "statut": "en_cours",
         "indice_irl_reference": "T1 2024", "date_revision": "2025-03-01",
         "etat_lieux_entree": "2024-03-01", "etat_lieux_sortie": None,
         "document_url": None},
    ]
    insert("baux", baux)
    for i in range(len(baux)):
        insert("bail_locataires", {"id_bail": baux[i]["id"], "id_locataire": locataires[i]["id"]})
    print(f"  ✅ {len(baux)} baux (IRL, révision, état lieux, dépôt)")

    # ── Loyers (12 mois, TOUS les champs) ─────────────────────────
    loyer_count = 0
    montants = [1450, 1100, 780, 1800, 2200]
    seen = set()
    for offset in range(12, 0, -1):
        d = today.replace(day=1) - timedelta(days=offset * 30)
        ld = d.replace(day=1)
        mk = (ld.year, ld.month)
        if mk in seen: continue
        seen.add(mk)
        for i, bien in enumerate(biens):
            if i >= len(locataires): continue
            statut = "paye"
            pdate = str(ld + timedelta(days=5))
            mode = "virement"
            if offset <= 2:
                statut, pdate, mode = "en_attente", None, None
            elif offset == 5 and i == 2:
                statut, pdate, mode = "en_retard", None, None
            elif offset == 8 and i == 0:
                statut, pdate, mode = "en_retard", None, None
            insert("loyers", {
                "id": uid(), "id_bien": bien["id"], "id_locataire": locataires[i]["id"],
                "id_sci": bien["id_sci"],
                "date_loyer": str(ld), "montant": montants[i],
                "statut": statut, "date_paiement": pdate, "mode_paiement": mode,
                "quitus_genere": statut == "paye",
            })
            loyer_count += 1
    print(f"  ✅ {loyer_count} loyers (id_sci, date_paiement, mode_paiement)")

    # ── Charges (types conformes CHARGE_TYPES) ────────────────────
    charge_count = 0
    for bien in biens:
        for tc, m in [("copropriete", 250), ("taxe_fonciere", 180), ("travaux_entretien", 120),
                      ("assurance_pno", 90), ("interets_emprunt", 350)]:
            if tc == "interets_emprunt" and (bien.get("prix_acquisition") or 0) < 200000: continue
            for q in range(1, 5):
                insert("charges", {"id": uid(), "id_bien": bien["id"],
                    "type_charge": tc, "montant": m, "date_paiement": f"2025-{q*3:02d}-01"})
                charge_count += 1
    print(f"  ✅ {charge_count} charges (copro, TF, travaux, PNO, intérêts)")

    # ── Événements bien ───────────────────────────────────────────
    evts = [
        {"id": uid(), "id_bien": biens[0]["id"], "type": "reparation",
         "titre": "Remplacement chaudière", "description": "Chaudière gaz → condensation",
         "date_evenement": "2025-03-15", "montant": 2800,
         "prestataire": "Plomberie Martin & Fils", "deductible_fiscalement": True},
        {"id": uid(), "id_bien": biens[0]["id"], "type": "diagnostic",
         "titre": "Diagnostic DPE", "description": "DPE par bureau certifié COFRAC",
         "date_evenement": "2025-01-20", "montant": 150,
         "prestataire": "DiagImmo Paris", "deductible_fiscalement": False},
        {"id": uid(), "id_bien": biens[1]["id"], "type": "sinistre",
         "titre": "Dégât des eaux", "description": "Fuite canalisation SDB — plafond et mur",
         "date_evenement": "2025-06-10", "montant": 1200,
         "prestataire": "MAIF — sinistre n°2025-4421", "deductible_fiscalement": False},
        {"id": uid(), "id_bien": biens[2]["id"], "type": "travaux",
         "titre": "Peinture rafraîchissement", "description": "Remise en peinture complète studio",
         "date_evenement": "2025-08-01", "montant": 950,
         "prestataire": "Peinture Express", "deductible_fiscalement": True},
        {"id": uid(), "id_bien": biens[3]["id"], "type": "controle",
         "titre": "Ramonage cheminée", "description": "Ramonage annuel obligatoire",
         "date_evenement": "2025-10-05", "montant": 120,
         "prestataire": "Ramonage Lyon Sud", "deductible_fiscalement": False},
        {"id": uid(), "id_bien": biens[4]["id"], "type": "visite",
         "titre": "Visite conformité local commercial",
         "description": "Vérification normes ERP et accessibilité",
         "date_evenement": "2025-04-20", "montant": 350,
         "prestataire": "Bureau Veritas", "deductible_fiscalement": False},
    ]
    for e in evts: insert("evenements_bien", e)
    print(f"  ✅ {len(evts)} événements (réparation, diagnostic, sinistre, travaux, contrôle, visite)")

    # ── Assurances PNO ────────────────────────────────────────────
    for bien in biens:
        insert("assurances_pno", {"id": uid(), "id_bien": bien["id"],
            "compagnie": "MAIF" if bien["id_sci"] == sci1_id else "AXA",
            "numero_contrat": f"PNO-{bien['code_postal']}-{uid()[:6]}",
            "montant_annuel": 280 if (bien.get("nb_pieces") or 2) > 1 else 150,
            "date_echeance": "2026-06-01"})  # PNO within ~3 months → urgente
    print(f"  ✅ {len(biens)} PNO")

    # ── Frais agence ──────────────────────────────────────────────
    insert("frais_agence", {"id": uid(), "id_bien": biens[3]["id"],
        "nom_agence": "Nexity Lyon Presqu'île", "contact": "04 72 10 20 30",
        "type_frais": "pourcentage", "montant_ou_pourcentage": 7.5})
    insert("frais_agence", {"id": uid(), "id_bien": biens[4]["id"],
        "nom_agence": "Century 21 Part-Dieu", "contact": "04 78 60 50 40",
        "type_frais": "fixe", "montant_ou_pourcentage": 180})
    print("  ✅ 2 frais agence")

    # ── Fiscalité (avec décomposition) ────────────────────────────
    for a in [2024, 2025]:
        insert("fiscalite", {"id": uid(), "id_sci": sci1_id, "annee": a,
            "total_revenus": 39960 if a == 2024 else 20000,
            "total_charges": 10240 if a == 2024 else 5500,
            "resultat_fiscal": 29720 if a == 2024 else 14500,
            "interets_emprunt": 4200 if a == 2024 else 3800,
            "travaux": 2500 if a == 2024 else 0,
            "frais_gestion": 60, "assurance": 840, "taxe_fonciere": 2160, "copropriete": 3000})
        insert("fiscalite", {"id": uid(), "id_sci": sci2_id, "annee": a,
            "total_revenus": 48000 if a == 2024 else 24000,
            "total_charges": 12800 if a == 2024 else 6400,
            "resultat_fiscal": 35200 if a == 2024 else 17600,
            "interets_emprunt": 5600 if a == 2024 else 5000,
            "travaux": 0, "frais_gestion": 40, "assurance": 560,
            "taxe_fonciere": 3600, "copropriete": 3000})
    print("  ✅ Fiscalité 2024-2025 (décomposition complète)")

    # ── AG ─────────────────────────────────────────────────────────
    insert("assemblees_generales", {"id": uid(), "id_sci": sci1_id,
        "date_ag": "2025-06-15", "type_ag": "ordinaire", "exercice_annee": 2024,
        "ordre_du_jour": "1. Approbation des comptes 2024\n2. Affectation du résultat\n3. Renouvellement mandat gérant",
        "notes": "Comptes approuvés à l'unanimité. Résultat 29 720 € en report à nouveau.",
        "resolutions": "R1: Comptes 2024 approuvés.\nR2: Résultat en report à nouveau.\nR3: Mandat gérant renouvelé 3 ans.",
        "quorum_atteint": True, "pv_url": "https://example.com/pv-ago-2025.pdf"})
    insert("assemblees_generales", {"id": uid(), "id_sci": sci1_id,
        "date_ag": "2025-11-20", "type_ag": "extraordinaire", "exercice_annee": 2025,
        "ordre_du_jour": "1. Augmentation capital social\n2. Modification article 7 statuts",
        "notes": "Capital porté de 150 000 € à 200 000 € par création de 333 parts.",
        "resolutions": "R1: Augmentation capital de 50 000 €.",
        "quorum_atteint": True, "pv_url": None})
    print("  ✅ 2 AG (AGO + AGE)")

    # ── Mouvements de parts ───────────────────────────────────────
    if user2_id:
        insert("mouvements_parts", {"id": uid(), "id_sci": sci1_id,
            "type_mouvement": "apport", "cedant_nom": None, "cessionnaire_nom": "Marie Dupont",
            "nb_parts": 1000, "prix_unitaire": 150, "prix_total": 150000,
            "date_mouvement": "2019-01-15",
            "notes": "Statuts constitutifs — Acte SSP du 15/01/2019",
            "document_url": None})
        insert("mouvements_parts", {"id": uid(), "id_sci": sci1_id,
            "type_mouvement": "cession", "cedant_nom": "Marie Dupont", "cessionnaire_nom": "Pierre Martin",
            "nb_parts": 400, "prix_unitaire": 150, "prix_total": 60000,
            "date_mouvement": "2023-03-15",
            "notes": "Cession notariée — Me Lefèvre, Paris 20e — Enregistré le 18/03/2023",
            "document_url": None})
        print("  ✅ 2 mouvements de parts")

    # ── Subscription Fiscal (Pro) ─────────────────────────────────
    insert("subscriptions", {"id": uid(), "user_id": user_id,
        "stripe_customer_id": f"cus_demo_{uid()[:8]}",
        "stripe_subscription_id": f"sub_demo_{uid()[:8]}",
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_demo"),
        "mode": "subscription", "status": "active",
        "current_period_end": str(today + timedelta(days=365)),
        "onboarding_completed": True})
    print("  ✅ Abonnement Fiscal (toutes features)")

    # ── Notifications ─────────────────────────────────────────────
    insert("notifications", {"id": uid(), "user_id": user_id, "type": "late_payment",
        "title": "Loyer impayé — 8 rue du Commerce",
        "message": "Lucas Bernard est en retard de 15 jours. Montant : 780 €.",
        "metadata": {"bien_id": biens[2]["id"], "locataire": "Lucas Bernard", "montant": 780, "dedup_key": "late_seed"}})
    insert("notifications", {"id": uid(), "user_id": user_id, "type": "bail_expiring",
        "title": "Bail expirant — Apt 1 Belleville",
        "message": "Le bail de J.-M. Lefebvre expire le 31/12/2025.",
        "metadata": {"bail_id": baux[0]["id"], "dedup_key": "bail_seed"}})
    insert("notifications", {"id": uid(), "user_id": user_id, "type": "pno_expiring",
        "title": "PNO — Renouvellement",
        "message": "L'assurance PNO MAIF pour Belleville Apt 1 expire le 01/06/2026.",
        "metadata": {"dedup_key": "pno_seed"}})
    insert("notifications", {"id": uid(), "user_id": user_id, "type": "info",
        "title": "Bienvenue sur GérerSCI !", "message": "Votre espace est prêt.",
        "metadata": {}, "read_at": str(datetime.now(timezone.utc))})
    for nt in ["late_payment", "bail_expiring", "quittance_pending", "pno_expiring",
               "new_loyer", "new_associe", "subscription_expiring"]:
        insert("notification_preferences", {"id": uid(), "user_id": user_id, "type": nt,
            "email_enabled": nt in ("late_payment", "bail_expiring", "pno_expiring"),
            "in_app_enabled": True})
    print("  ✅ 4 notifications + 7 préférences")

    # ── Admin ─────────────────────────────────────────────────────
    insert("admins", {"user_id": user_id})

    print(f"""
{'='*60}
🎉 Seed terminé — TOUS les champs alimentés
{'='*60}

📧 {DEMO_EMAIL} / 🔑 {DEMO_PASSWORD}
👑 Admin + 💳 Fiscal (toutes features)

📊 {len(biens)} biens · {len(locataires)} locataires · {len(baux)} baux
   {loyer_count} loyers · {charge_count} charges · {len(evts)} événements
   2 SCI · 2 AG · 2 mouvements · 5 PNO · 2 frais agence
   Fiscalité 2024+2025 · 4 notifications · 7 préférences

🌐 http://localhost:5173 (Frontend)
   http://localhost:8001 (Backend)
""")


if __name__ == "__main__":
    main()
