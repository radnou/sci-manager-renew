---
name: business-functional-docs
description: Structurer et mettre à jour la documentation business et fonctionnelle d'un produit SaaS. Utiliser ce skill quand il faut réécrire README/docs produit, clarifier proposition de valeur, personas, parcours fonctionnels, backlog et KPI, ou aligner des documents business avec l'état réel du code et de la roadmap.
---

# Business Functional Docs

Mettre à jour les documents business/fonctionnels d'un projet en gardant un niveau exécutable pour produit, engineering et go-to-market.

## Workflow

1. Cartographier les sources de vérité.
- Lire en priorité: `README.md`, docs existantes, audit, et fichiers applicatifs clés (`routes`, `api`, `schemas`).
- Lister ce qui est factuel aujourd'hui vs ce qui est objectif cible.

2. Définir le pack documentaire minimal.
- Toujours inclure un README orienté valeur business.
- Ajouter/mettre à jour des docs séparées pour: périmètre fonctionnel, GTM/KPI, roadmap.
- Limiter les redondances: chaque document doit avoir un rôle explicite.

3. Rédiger en mode actionnable.
- Préférer sections courtes, listes et critères mesurables.
- Spécifier les indicateurs clés (activation, rétention, conversion, churn).
- Marquer clairement les hypothèses (pricing, cible, roadmap) quand elles ne sont pas encore validées.

4. Aligner documentation et code.
- Vérifier que routes, endpoints, scripts et commandes mentionnés existent réellement.
- Éviter les promesses produit non implémentées sans les qualifier comme "cible".

5. Finaliser et contrôler cohérence.
- Vérifier liens relatifs entre docs.
- Vérifier langue, terminologie et priorités constantes sur tous les fichiers.

## Règles éditoriales

- Écrire pour 3 audiences: fondateur, product/ops, engineering.
- Exprimer d'abord le problème business, puis la capacité fonctionnelle, puis la mise en oeuvre.
- Utiliser des KPI définis de façon opérationnelle (formule + fréquence de suivi).
- Préférer une roadmap 30/60/90 jours à une liste de souhaits non priorisée.

## Références

- Structure documentaire recommandée: `references/doc-map.md`
- Catalogue KPI SaaS immobilier: `references/metric-catalog.md`
