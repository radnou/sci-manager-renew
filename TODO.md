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

## ⚠️ Avant de déployer — à lancer en local

Les tests **n'ont pas pu être exécutés** pendant l'audit (sandbox en Python 3.10,
le projet exige 3.12 pour `datetime.UTC`). Les fichiers compilent et passent
pyflakes, mais la suite doit être verte avant mise en production :

```bash
cd backend
PYTHONPATH=. pytest tests/test_api/test_associes.py tests/test_api/test_associes_security.py -v
PYTHONPATH=. pytest   # suite complète
```

Deux fixtures ont été ajustées (elles encodaient le comportement permissif) :
`tests/conftest.py` (`associe-2` → `gerant`) et
`test_associes.py::test_delete_self_row` (`extra-sci2` → `gerant`).

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
