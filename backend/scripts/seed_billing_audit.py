"""
Seed script: 3 comptes pour l'audit billing & paywall.

Usage:
    cd backend && python scripts/seed_billing_audit.py

Crée:
- Compte A (free@audit.test / password123) — Plan Free, 1 SCI, 2 biens (limites atteintes)
- Compte B (starter@audit.test / password123) — Plan Starter, 2 SCI, 5 biens
- Compte C (pro@audit.test / password123) — Plan Pro, 3 SCI, 8 biens, toutes features
"""
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
)

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation,resolution=merge-duplicates",
}


def api(method, path, json=None):
    r = httpx.request(method, f"{SUPABASE_URL}{path}", headers=HEADERS, json=json, timeout=15)
    if r.status_code >= 400:
        print(f"  ⚠️  {method} {path} → {r.status_code}: {r.text[:200]}")
        return None
    try:
        return r.json()
    except Exception:
        return r.text


def create_user(email, password="password123"):
    """Create Supabase Auth user via admin API."""
    data = api("POST", "/auth/v1/admin/users", json={
        "email": email,
        "password": password,
        "email_confirm": True,
    })
    if data and "id" in data:
        print(f"  ✅ User {email} → {data['id']}")
        return data["id"]
    # Try to find existing user
    users = api("GET", f"/auth/v1/admin/users?filter=email%3D{email}")
    if users and isinstance(users, dict) and users.get("users"):
        uid = users["users"][0]["id"]
        print(f"  ♻️  User {email} exists → {uid}")
        return uid
    print(f"  ❌ Failed to create {email}")
    return None


def upsert(table, rows):
    if not isinstance(rows, list):
        rows = [rows]
    result = api("POST", f"/rest/v1/{table}", json=rows)
    if result:
        print(f"  ✅ {table}: {len(rows)} row(s)")
    return result


def seed_account(email, plan_key, plan_config, scis_data):
    """Seed one complete account."""
    print(f"\n{'='*60}")
    print(f"Seeding: {email} ({plan_key})")
    print(f"{'='*60}")

    user_id = create_user(email)
    if not user_id:
        return

    # Subscription
    # subscriptions table has: user_id, status, stripe_price_id, onboarding_completed
    # plan_key is resolved dynamically from stripe_price_id via entitlements.py
    sub = {
        "user_id": user_id,
        "status": plan_config["status"],
        "stripe_price_id": plan_config.get("stripe_price_id", ""),
        "onboarding_completed": True,
    }
    upsert("subscriptions", sub)

    for sci_data in scis_data:
        sci_id = str(uuid.uuid4())
        upsert("sci", {
            "id": sci_id,
            "nom": sci_data["nom"],
            "siren": sci_data.get("siren", ""),
            "regime_fiscal": sci_data.get("regime", "IR"),
            "adresse_siege": sci_data.get("adresse", ""),
            "capital_social": sci_data.get("capital", 100000),
        })

        # Associé (gérant)
        upsert("associes", {
            "id": str(uuid.uuid4()),
            "id_sci": sci_id,
            "user_id": user_id,
            "nom": sci_data.get("gerant_nom", "Audit User"),
            "email": email,
            "part": 100,
            "role": "gerant",
        })

        for bien_data in sci_data.get("biens", []):
            bien_id = str(uuid.uuid4())
            upsert("biens", {
                "id": bien_id,
                "id_sci": sci_id,
                "adresse": bien_data["adresse"],
                "ville": bien_data["ville"],
                "code_postal": bien_data["cp"],
                "type_locatif": bien_data.get("type", "nu"),
                "loyer_cc": bien_data.get("loyer", 1000),
                "charges": bien_data.get("charges", 100),
                "tmi": 30,
                "surface_m2": bien_data.get("surface", 50),
                "nb_pieces": bien_data.get("pieces", 2),
            })

            # Bail actif
            bail_id = str(uuid.uuid4())
            upsert("baux", {
                "id": bail_id,
                "id_bien": bien_id,
                "statut": "en_cours",
                "loyer_hc": bien_data.get("loyer", 1000),
                "charges_locatives": bien_data.get("charges", 100),
                "date_debut": "2024-01-01",
                "date_fin": "2027-12-31",
            })

            # 3 mois de loyers
            today = date.today()
            for i in range(3):
                d = date(today.year, today.month - i if today.month - i > 0 else 12 + today.month - i, 1)
                upsert("loyers", {
                    "id": str(uuid.uuid4()),
                    "id_bien": bien_id,
                    "id_sci": sci_id,
                    "date_loyer": d.isoformat(),
                    "montant": bien_data.get("loyer", 1000),
                    "statut": "paye" if i > 0 else "en_attente",
                })

    print(f"  🏁 {email} seeded successfully")
    return user_id


def main():
    print("=" * 60)
    print("AUDIT BILLING — Seeding 3 test accounts")
    print("=" * 60)

    # ── COMPTE A: FREE (Essentiel) — limites atteintes ──
    seed_account("free@audit.test", "free", {
        "status": "free",
        "stripe_price_id": "",  # no Stripe price = free plan
    }, [
        {
            "nom": "SCI Audit Free",
            "siren": "111111111",
            "regime": "IR",
            "gerant_nom": "Alice Freemium",
            "biens": [
                {"adresse": "10 rue du Test", "ville": "Paris", "cp": "75001", "loyer": 800, "surface": 30, "pieces": 1},
                {"adresse": "20 avenue Gratuite", "ville": "Paris", "cp": "75002", "loyer": 1200, "surface": 55, "pieces": 2},
            ],
        },
    ])

    # ── COMPTE B: STARTER (Gestion) — usage moyen ──
    seed_account("starter@audit.test", "starter", {
        "status": "active",
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_1TAyt3BCxd3SKdGJ0WbBDbsW"),
    }, [
        {
            "nom": "SCI Starter Paris",
            "siren": "222222221",
            "regime": "IR",
            "gerant_nom": "Bob Starter",
            "biens": [
                {"adresse": "5 rue Starter", "ville": "Paris", "cp": "75003", "loyer": 900, "surface": 40},
                {"adresse": "15 bd Gestion", "ville": "Paris", "cp": "75004", "loyer": 1100, "surface": 60},
                {"adresse": "25 rue Multi", "ville": "Lyon", "cp": "69001", "loyer": 750, "surface": 35},
            ],
        },
        {
            "nom": "SCI Starter Lyon",
            "siren": "222222222",
            "regime": "IR",
            "gerant_nom": "Bob Starter",
            "biens": [
                {"adresse": "8 rue Rhône", "ville": "Lyon", "cp": "69002", "loyer": 850, "surface": 42},
                {"adresse": "12 place Bellecour", "ville": "Lyon", "cp": "69002", "loyer": 1300, "surface": 70},
            ],
        },
    ])

    # ── COMPTE C: PRO (Fiscal) — accès complet ──
    seed_account("pro@audit.test", "pro", {
        "status": "active",
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_1TAyt3BCxd3SKdGJeNgk9G3E"),
    }, [
        {
            "nom": "SCI Pro Immobilier",
            "siren": "333333331",
            "regime": "IR",
            "gerant_nom": "Claire Pro",
            "adresse": "1 place de l'Étoile, 75008 Paris",
            "capital": 500000,
            "biens": [
                {"adresse": "1 place Étoile", "ville": "Paris", "cp": "75008", "loyer": 2500, "surface": 95, "pieces": 4},
                {"adresse": "3 rue Foch", "ville": "Paris", "cp": "75016", "loyer": 1800, "surface": 75, "pieces": 3},
                {"adresse": "7 av Montaigne", "ville": "Paris", "cp": "75008", "loyer": 3200, "surface": 120, "pieces": 5, "type": "meuble"},
            ],
        },
        {
            "nom": "SCI Pro Côte d'Azur",
            "siren": "333333332",
            "regime": "IS",
            "gerant_nom": "Claire Pro",
            "biens": [
                {"adresse": "10 promenade Anglais", "ville": "Nice", "cp": "06000", "loyer": 1500, "surface": 55},
                {"adresse": "5 rue Antibes", "ville": "Cannes", "cp": "06400", "loyer": 2000, "surface": 80, "type": "meuble"},
            ],
        },
        {
            "nom": "SCI Pro Bordeaux",
            "siren": "333333333",
            "regime": "IR",
            "gerant_nom": "Claire Pro",
            "biens": [
                {"adresse": "20 cours Intendance", "ville": "Bordeaux", "cp": "33000", "loyer": 1100, "surface": 50},
                {"adresse": "8 quai Chartrons", "ville": "Bordeaux", "cp": "33000", "loyer": 1400, "surface": 65, "pieces": 3},
                {"adresse": "15 rue Ste-Catherine", "ville": "Bordeaux", "cp": "33000", "loyer": 900, "surface": 38, "type": "meuble"},
            ],
        },
    ])

    print("\n" + "=" * 60)
    print("SEED COMPLETE — 3 comptes prêts pour l'audit")
    print("=" * 60)
    print("  🆓 free@audit.test    / password123  (Essentiel, 1 SCI, 2 biens)")
    print("  📦 starter@audit.test / password123  (Gestion,   2 SCI, 5 biens)")
    print("  🏆 pro@audit.test     / password123  (Fiscal,    3 SCI, 8 biens)")
    print("=" * 60)


if __name__ == "__main__":
    main()
