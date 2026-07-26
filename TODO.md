# TODO — actions immédiates

Checklist opérationnelle courte. Le registre complet des 67 findings est dans
[`BACKLOG.md`](./BACKLOG.md) ; les preuves dans [`AUDIT_EXTERNE_2026-07-25.md`](./AUDIT_EXTERNE_2026-07-25.md).

---

## 🔥 Aujourd'hui

### 1. Sauvegarder la base (CRITICAL-8)
Aucune sauvegarde n'existe. À faire **avant toute autre action**.

- [ ] `pg_dump` manuel, copié hors du VPS
- [ ] Vérifier que le dump est lisible (`pg_restore --list`)

### 2. Déployer le correctif C1/C3
Le contournement de paiement est **actif en production**.

- [ ] `psql "$DATABASE_URL" -f supabase/migrations/043_security_fix_c1_c3_rls.sql`
- [ ] Déployer le backend (migration + patches applicatifs vont ensemble)
- [ ] Rejouer l'exploit → doit renvoyer 401/403 :
      ```bash
      curl -X POST "https://api.gerersci.fr/rest/v1/subscriptions" \
        -H "apikey: $ANON" -H "Authorization: Bearer $USER_JWT" \
        -d '{"user_id":"<self>","status":"active","plan_key":"pilotage"}'
      ```
- [ ] Vérifier la non-régression : inscription → `/welcome` → onboarding → `/complete`
- [ ] Vérifier la suppression de compte RGPD

### 3. Fermer l'exposition Supabase (CRITICAL-2 + HIGH-1/HIGH-2)
**Dans le dépôt `vps-infra`**, pas ici.

- [ ] Retirer `/rest/`, `/storage/`, `/realtime/` du vhost `api.gerersci.fr`
- [ ] Désactiver le signup public GoTrue (`disable_signup: true`)
- [ ] Désactiver `/docs`, `/redoc`, `/openapi.json` en production
- [ ] Vérifier : `curl https://api.gerersci.fr/rest/v1/sci` → 404

### 4. Nettoyage
- [ ] Purger le compte de test de l'audit : `be2e22f5-a401-4d25-b2e4-67003bc85df8`
- [ ] `stripe login` sur le compte **C** (`acct_1SFrY0ApRgYAyPDH`) puis
      `stripe prices list --live` → résout le « produits Stripe disparus »
      (la prod est saine : `/health/ready` renvoie `stripe.mode: live`, 4 prix validés)

---

## ✅ Suite de tests — exécutée le 2026-07-26

`PYTHONPATH=. pytest` est **verte** (venv `backend/.venv`, Python 3.11 — 3.12
n'était pas requis, `datetime.UTC` existe depuis 3.11).

Le commit d'audit introduisait 12 régressions, toutes corrigées :

| Test | Cause | Correctif |
|---|---|---|
| `test_scis::test_*_requires_gerant` (2) | le fixture `associe-2` avait été passé à `gerant`, supprimant la seule base négative du projet | fixture remis à `associe` ; les tests concernés promeuvent localement |
| `test_associes::test_*_generic_exception` (3) | patchaient `_get_user_sci_ids`, que create/update/delete n'appellent plus | patch sur `_require_gerant` |
| `test_associes::test_delete_single_gerant_blocked` | scénario devenu inatteignable (l'appelant se rétrogradait avant l'appel) | le gérant unique supprime sa propre ligne |
| `test_plan_enforcement` (6) | fixtures injectant `max_scis`/`max_biens` dans la ligne DB — précisément ce que C1 neutralise | quotas alignés sur `PLAN_CATALOG` ; le cas `upgrade_required` patche le catalogue |

**Trois régressions de production trouvées dans le correctif lui-même :**

- `demo.py` seed/cleanup écrivait avec le JWT utilisateur → la policy
  `associes_member_insert` de la 043 rejette l'insertion du gérant sur une SCI
  neuve : **tout le parcours demo-first aurait cassé** dès l'application de la
  migration. Bascule en service_role + test `test_demo_rls_identity.py`.
- `gdpr.py` supprimait la ligne associé des SCI partagées avec le JWT
  utilisateur → suppression silencieusement ignorée pour un non-gérant
  (non-conformité RGPD). Bascule sur `erase_client`.
- `subscription_service` : `resolve_plan_key_from_price_id` renvoie `FREE` (et
  non `None`) pour un `price_id` inconnu. Placé avant le fallback `plan_key`,
  tout client payant portant un prix historique était rétrogradé à chaque
  lecture. Ce `FREE` est désormais traité comme non concluant.

Reste non vérifié en conditions réelles : la 043 elle-même (aucune base de test
avec RLS). Les invariants ci-dessus reposent sur la lecture des policies.

---

## 📅 Cette semaine

- [ ] **C9** — sortir le cron des workers uvicorn (emails en double chez les clients)
- [ ] **C5** — fiscalité : le `GET` ne doit plus écrire (déficit foncier corrompu à chaque affichage)
- [ ] **C6** — filtrer les charges récupérables (réclamations illégales aux locataires)
- [ ] **HIGH-11** — corriger le gate de readiness (`curl -sf` avale le 503) + ordre des migrations (`0045`/`0046`/`035`)
- [ ] **HIGH-12** — jouer les migrations dans le déploiement
- [ ] **MED-14** — import CSV cassé (`NameError` → 500 systématique, correctif = 1 ligne)

## 📅 Ce mois

- [ ] **C4** — Fondateur 990 € inachetable (24 750 € bloqués)
- [ ] **C7** — désactiver ou corriger la 2065 (IS surévalué, pas d'amortissement)
- [ ] **H3→H10** — chaîne de paiement : rattrapage webhook, garantie 30 j, résiliation 3 clics, `past_due`
- [ ] **HIGH-15** — filtre `deleted_at` sur ~20 requêtes
- [ ] **HIGH-16** — CI : activer `test:unit`, ruff, mypy

## 🔐 À trancher

- [ ] `.env` a été tracké avant le commit `8ad430d7` et contient des secrets réels
      dans l'historique. Le dépôt a-t-il été public/partagé ?
      Si oui → rotation de `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`,
      `STRIPE_SECRET_KEY`, `RESEND_API_KEY`.
