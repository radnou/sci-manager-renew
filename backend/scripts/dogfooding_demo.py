#!/usr/bin/env python3
"""
Dogfooding script — Parcours complet gestionnaire débutant.

Usage (depuis le conteneur backend):
    python3 -m scripts.dogfooding_demo

Parcours:
1. Connexion (crée ou réutilise compte démo)
2. Création SCI
3. Création bien
4. Création bail
5. Génération quittance
6. Vérification fiche bien
"""

import os
import sys
import requests
from datetime import datetime, date
from uuid import uuid4

# ── Configuration ─────────────────────────────────────────────────
API_BASE = os.environ.get("API_URL", "http://localhost:8000")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

from supabase import create_client

DEMO_EMAIL = "demo@gerersci.fr"
DEMO_PASSWORD = "DemoTest123!"

# ── Helpers ────────────────────────────────────────────────────────

def get_demo_token():
    """Crée ou récupère un compte démo et retourne un token valide."""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Essayer de supprimer l'utilisateur s'il existe pour s'assurer des identifiants frais
    try:
        res = supabase.auth.admin.list_users()
        user_list = res.users if hasattr(res, 'users') else res
        for u in user_list:
            if u.email == DEMO_EMAIL:
                supabase.auth.admin.delete_user(u.id)
                print(f"🗑️ Utilisateur démo existant supprimé")
                break
    except Exception as e:
         print(f"⚠️ Erreur lors du nettoyage de l'ancien compte démo: {e}")

    # Créer l'utilisateur
    try:
        result = supabase.auth.admin.create_user({
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "email_confirm": True,
            "user_metadata": {"full_name": "Gérant Test"}
        })
        print(f"✅ Utilisateur créé: {result.user.id}")
    except Exception as e:
        print(f"⚠️ Erreur création: {e}")

    # Se connecter pour obtenir un token frais
    result = supabase.auth.sign_in_with_password({
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    })

    token = result.session.access_token
    user_id = result.user.id
    print(f"🔑 Token obtenu (expire: {result.session.expires_in}s)")

    # Activer l'abonnement démo (Plan Pro)
    try:
        sub_data = {
            "user_id": user_id,
            "status": "active",
            "is_active": True,
            "plan_key": "pro",
            "mode": "subscription",
            "current_period_end": "2030-01-01T00:00:00+00:00",
            "onboarding_completed": True
        }
        supabase.table("subscriptions").upsert(sub_data, on_conflict="user_id").execute()
        print("💳 Abonnement démo activé (Plan Pro).")
    except Exception as e:
        print(f"⚠️ Erreur activation abonnement: {e}")

    return token, user_id


def api_call(method, path, token, json=None, params=None):
    """Appel API avec auth."""
    url = f"{API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.request(method, url, headers=headers, json=json, params=params)
    return r


# ── Parcours Dogfooding ────────────────────────────────────────────

def run_dogfooding():
    print("=" * 60)
    print("🐕 DOGFOODING — Parcours gestionnaire débutant")
    print("=" * 60)

    # 1. AUTH
    print("\n📍 ÉTAPE 1: Authentification")
    token, user_id = get_demo_token()

    # 2. CRÉER SCI
    print("\n📍 ÉTAPE 2: Création SCI")
    sci_data = {
        "nom": "SCI Familiale Test",
        "adresse": "12 Rue de la Paix, 75002 Paris",
        "capital_social": 15000,
        "date_creation": "2024-01-15",
        "regime_fiscal": "IR",
        "type_sci": "familiale",
        "siret": "12345678900013"
    }
    r = api_call("POST", "/api/v1/scis", token, json=sci_data)
    print(f"   Status: {r.status_code}")

    if r.status_code == 201:
        sci = r.json()
        sci_id = sci["id"]
        print(f"   ✅ SCI créée: {sci_id}")
    elif r.status_code == 409:
        # Récupérer SCI existante
        r = api_call("GET", "/api/v1/scis", token)
        scis = r.json()
        if scis:
            sci = scis[0]
            sci_id = sci["id"]
            print(f"   ℹ️ SCI existante: {sci_id}")
        else:
            print("   ❌ Pas de SCI trouvée")
            return
    else:
        print(f"   ❌ Erreur: {r.text}")
        return

    # 3. CRÉER BIEN
    print("\n📍 ÉTAPE 3: Création bien")
    bien_data = {
        "adresse": "42 Rue du Commerce",
        "ville": "Sainte-Suzanne",
        "code_postal": "97441",
        "type_bien": "appartement",
        "type_locatif": "meuble",
        "surface_m2": 65.5,
        "loyer_cc": 850.00,
        "prix_acquisition": 180000.00,
        "acquisition_date": "2023-03-15",
        "charges": 120.00,
        "frais_notaire": 14400.00,
        "frais_agence_acquisition": 5400.00
    }
    r = api_call("POST", f"/api/v1/scis/{sci_id}/biens/", token, json=bien_data)
    print(f"   Status: {r.status_code}")

    if r.status_code == 201:
        bien = r.json()
        bien_id = bien["id"]
        print(f"   ✅ Bien créé: {bien_id}")
        print(f"   💰 Loyer: {bien['loyer_cc']}€ | Surface: {bien['surface_m2']}m²")
    elif r.status_code == 409:
        r = api_call("GET", f"/api/v1/scis/{sci_id}/biens/", token)
        biens = r.json()
        if biens:
            bien = biens[0]
            bien_id = bien["id"]
            print(f"   ℹ️ Bien existant: {bien_id}")
        else:
            print("   ❌ Pas de bien trouvé")
            return
    else:
        print(f"   ❌ Erreur: {r.text[:500]}")
        return

    # 4. CRÉER BAIL
    print("\n📍 ÉTAPE 4: Création bail")
    bail_data = {
        "id_bien": bien_id,
        "date_debut": "2024-01-01",
        "date_fin": "2026-12-31",
        "loyer_mensuel": 850.00,
        "loyer_hc": 730.00,
        "charges_mensuelles": 120.00,
        "depot_garantie": 1460.00,  # 2 mois loyer HC (bail meublé)
        "type_bail": "bail_meuble",
        "indexation_ilm": True,
        "locataire_nom": "Martin Dupont",
        "locataire_email": "martin.dupont@example.com"
    }
    r = api_call("POST", f"/api/v1/scis/{sci_id}/biens/{bien_id}/baux", token, json=bail_data)
    print(f"   Status: {r.status_code}")

    if r.status_code == 201:
        bail = r.json()
        print(f"   ✅ Bail créé: {bail['id']}")
    else:
        print(f"   ⚠️ Info: {r.text[:200]}")

    # 5. FICHE BIEN (rentabilité)
    print("\n📍 ÉTAPE 5: Vérification fiche bien")
    r = api_call("GET", f"/api/v1/scis/{sci_id}/biens/{bien_id}", token)
    print(f"   Status: {r.status_code}")

    if r.status_code == 200:
        fiche = r.json()
        renta = fiche.get("rentabilite", {})
        print(f"   📊 Rentabilité brute: {renta.get('brute', 'N/A')}%")
        print(f"   📊 Cashflow annuel: {renta.get('cashflow_annuel', 'N/A')}€")
        print(f"   📊 Rendement net: {renta.get('net', 'N/A')}%")
    else:
        print(f"   ⚠️ Info: {r.text[:200]}")

    # 6. LISTE DES ASSOCIÉS
    print("\n📍 ÉTAPE 6: Vérification associés")
    r = api_call("GET", f"/api/v1/scis/{sci_id}/associes", token)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        associes = r.json()
        print(f"   👥 {len(associes)} associé(s)")

    # 7. DÉCLARATION 2065
    print("\n📍 ÉTAPE 7: Génération déclaration 2065")
    r = api_call("POST", f"/api/v1/scis/{sci_id}/declaration-2065/generate", token, json={
        "exercice": 2024,
        "methode_comptable": "recettes_depenses"
    })
    print(f"   Status: {r.status_code}")
    if r.status_code in (200, 201):
        decl = r.json()
        print(f"   ✅ Déclaration générée")
        print(f"   📄 Chiffre d'affaires: {decl.get('chiffre_affaires', 'N/A')}€")
        print(f"   📄 Bénéfice: {decl.get('resultat', 'N/A')}€")
    else:
        print(f"   ⚠️ Info: {r.text[:300]}")

    print("\n" + "=" * 60)
    print("✅ DOGFOODING TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    run_dogfooding()
