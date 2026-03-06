# Go-Live Blockers - 2026-03-06

## Blocking
- Appliquer les migrations Supabase jusqu'à `004_subscription_entitlements.sql`.
- Renseigner les `price_id` live Stripe et vérifier les metadata des produits/prix.
- Valider `GET /api/v1/stripe/subscription` sur un vrai compte `starter`, `pro` et `lifetime`.
- Exécuter un smoke test de dépassement de quota:
  - création SCI au-delà du plafond
  - création bien au-delà du plafond
- Vérifier que les webhooks Stripe mettent bien à jour `plan_key`, `features`, `is_active`.

## Important Before Scale
- Brancher les logs JSON sur un agrégateur avec requête par `request_id`.
- Ajouter une alerte sur `/health/ready` quand le statut devient `degraded`.
- Vérifier les timeouts/réessais sur les services externes avec un test de panne contrôlée.
- Rejouer le parcours PDF sur un backend réel avec storage et permissions cibles.
- Vérifier la cohérence commerciale entre la page `pricing`, les entitlements backend et le catalogue Stripe.

## Post-Launch Acceptable
- Étendre l'enforcement à d'autres entités si de nouveaux plafonds métier apparaissent.
- Ajouter des dashboards d'observabilité dédiés aux quotas et aux upgrades.
- Raffiner la granularité des feature flags par segment ou cohorte.
