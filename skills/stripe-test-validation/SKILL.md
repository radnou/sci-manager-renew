---
name: stripe-test-validation
description: Valider le parcours de paiement Stripe de GererSCI en mode test uniquement — checkout, webhook signé, idempotence, abonnement, annulation, échec. S'appuie sur backend/scripts/stripe_test_workflow.py. Refuse de s'exécuter si une clé de production est détectée.
---

## Pré-vol bloquant — mode test obligatoire

Vérifier le mode test sans jamais afficher de valeur complète :
```bash
printenv STRIPE_SECRET_KEY | cut -c1-8
printenv STRIPE_PUBLISHABLE_KEY | cut -c1-8
```
Résultat attendu : `sk_test_` et `pk_test_`. Tout autre préfixe, notamment `sk_live_` ou
`pk_live_`, arrête immédiatement la skill. Ne jamais afficher plus des 8 premiers caractères.
Ne jamais écrire une clé dans un rapport, un log, un commentaire d'issue ou un message.

Vérifications complémentaires :
```bash
stripe config --list
printenv STRIPE_WEBHOOK_SECRET >/dev/null && echo présent || echo absent
```

## Ce qui existe déjà et qu'il ne faut pas réécrire

**Scripts backend (tous nécessitent un venv Python) :**
- `backend/scripts/stripe_test_workflow.py` (279 lignes) : crée une session de checkout pour
  le plan Gestion mensuel, simule le webhook `checkout.session.completed` avec une signature
  HMAC réelle, vérifie l'état en base, puis rejoue le cycle en mode lifetime (`mode=payment`).
  C'est la seule preuve de bout en bout du dépôt sur la signature webhook.
  Lancement : `cd backend && python scripts/stripe_test_workflow.py`
- `backend/scripts/setup_stripe_products.py` : création et gestion des produits et prix.
- `backend/scripts/seed_billing_audit.py` : crée `free@audit.test`, `starter@audit.test`,
  `pro@audit.test` (mot de passe `<mot de passe du seed, cf. backend/scripts/seed_billing_audit.py>`).
- `backend/scripts/stripe_e2e_test.py` : NE JAMAIS L'EXÉCUTER EN LOCAL. Cible
  `https://api.gerersci.fr` et nécessite le `.env` de production du VPS.

**Specs frontend :**
- `frontend/e2e/production/stripe-full-flow.spec.ts`
- `frontend/e2e/validation/billing-audit.spec.ts`
- `frontend/e2e/validation/paywall.spec.ts`

## Ce que pytest ne prouve pas

`backend/tests/test_api/test_stripe.py` (806 lignes) monkeypatche
`stripe.Webhook.construct_event` et construit les événements en dictionnaires Python inline.
Il n'existe aucune fixture JSON d'événement webhook dans le dépôt. La vraie signature HMAC
n'est donc jamais vérifiée par pytest. Un pytest vert ne permet pas de conclure que le
paiement fonctionne. Porter cette information dans chaque rapport de validation Stripe.

## Surface Stripe

**Endpoints (préfixe `/api/v1/stripe`, fichier `backend/app/api/v1/stripe.py`) :**

| Méthode | Chemin | Ligne |
|---------|--------|-------|
| GET | `/subscription` | :285 |
| POST | `/create-checkout-session` | :309 |
| POST | `/create-guest-checkout` | :395 |
| POST | `/cancel-subscription` | :478 |
| POST | `/customer-portal` | :507 |
| POST | `/webhook` | :538 (limite 30/min) |
| POST | `/refund` | :588 (limite 2/jour) |

Le préfixe `/api/v1/stripe/` est exempté du `write_protection_middleware` (`main.py:508`).
Si `settings.feature_stripe_payments` est faux, le webhook renvoie `ignored` (`:543-545`).

**Événements gérés dans `_handle_event` (`:166-283`) :**
- `checkout.session.completed` (`:174`)
- `customer.subscription.deleted` (`:223`)
- `customer.subscription.updated` (`:227`)
- `invoice.payment_failed` (`:263`)

**Idempotence :** table `stripe_webhook_events` (`supabase/migrations/021_stripe_webhook_events.sql`),
colonne `event_id TEXT NOT NULL UNIQUE`, RLS avec policy `service_role_full_access` uniquement.
Mécanisme : `_is_event_already_processed` (`:130-150`) fait un SELECT et renvoie `False` en cas
d'exception ; le marquage a lieu APRES traitement via `_mark_event_processed` (`:153-163`) qui
avale toute exception. Point de fragilité : un événement traité dont le marquage échoue sera
retraité.

**URL de retour :**
- Checkout authentifié : `success_url = {frontend_url}/dashboard?upgraded=true` (`:363`),
  `cancel_url = {frontend_url}/#pricing` (`:364`).
- Checkout invité : `success_url = {frontend_url}/welcome?session_id={CHECKOUT_SESSION_ID}` (`:445`).

## Stripe CLI en local

La version disponible est 1.40.9. Écoute des webhooks :
```bash
stripe listen --forward-to localhost:8001/api/v1/stripe/webhook
```
Déclenchement d'événements :
```bash
stripe trigger checkout.session.completed
stripe trigger customer.subscription.deleted
stripe trigger customer.subscription.updated
stripe trigger invoice.payment_failed
```
Ne pas ajouter Stripe CLI au `docker-compose.yml`. Si cela paraît nécessaire, proposer une
modification séparée et réversible dans un fichier `docker-compose.override.yml` (déjà présent
dans `.gitignore`, donc local), et attendre l'accord.

## Scénarios

Cartes de test Stripe : paiement réussi `4242 4242 4242 4242`, refusé `4000 0000 0000 0002`,
fonds insuffisants `4000 0000 0000 9995`, 3DS requis `4000 0025 0000 3155`. Date future
quelconque, CVC quelconque.

| # | Scénario | Comment | Attendu |
|---|----------|---------|---------|
| 1 | Paiement réussi | Carte `4242...`, `stripe_test_workflow.py` | Abonnement actif en base, `is_active=true` |
| 2 | Paiement refusé | Carte `4000...0002` | Pas d'abonnement créé, message d'erreur Stripe |
| 3 | Checkout annulé | Clic « Annuler » | Redirection vers `/#pricing` (ancre, pas `/pricing`) |
| 4 | Webhook reçu deux fois | Rejouer le même `event_id` | Réponse `already_processed`, 1 seule ligne en base |
| 5 | Événements dans le désordre | `subscription.updated` avant `session.completed` | Pas de crash, état cohérent en base |
| 6 | Abonnement annulé | `stripe trigger customer.subscription.deleted` | `is_active=false` en base |
| 7 | Session expirée | Attendre expiration Stripe ou simuler | Redirection correcte, pas d'erreur 5xx |
| 8 | Rafraîchissement après paiement | Recharger `/dashboard?upgraded=true` | Pas de double traitement, état persisté |
| 9 | Course webhook / redirection | `success_url` atteinte avant traitement webhook | Redirection possible vers `/welcome` ou `/pricing` ; à documenter, ne pas corriger |
| 10 | Absence de double traitement | `select count(*) from stripe_webhook_events where event_id = '<id>'` | Résultat = 1 |

## Contrôles en base

```bash
psql "postgresql://<user>:<password>@127.0.0.1:54322/postgres" \
  -c "select event_id, event_type, processed_at from stripe_webhook_events order by processed_at desc limit 10;"
```

## Format de sortie

Tableau de résultats pour chaque scénario :

| Scénario | Statut (PASS/FAIL/BLOCKED/NOT_TESTED) | Preuve | Note |
|----------|---------------------------------------|--------|------|

Ajouter une ligne de verdict global : `ACCEPT`, `ACCEPT_WITH_RESERVES` ou `REJECT`.
Ne remplir le statut que pour les scénarios réellement exécutés.

## Garde-fous

- Jamais de paiement réel : clé `sk_test_` obligatoire, contrôlée en pré-vol.
- Jamais de clé de production. Jamais de valeur de clé affichée, écrite ou journalisée.
- Jamais de donnée réelle de client dans les rapports ou logs.
- Jamais de webhook de production redirigé vers l'environnement local.
- Ne jamais exécuter `backend/scripts/stripe_e2e_test.py` en local.
- Ne jamais modifier `docker-compose.yml` pour y ajouter Stripe CLI sans accord préalable.
- Ne jamais conclure sans preuve d'un scénario réellement exécuté.
- Pytest vert ne prouve pas que le paiement fonctionne (cf. section dédiée).
