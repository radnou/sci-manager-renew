# AGENT Instructions

Ce fichier expose les règles spécifiques à l'agent IA travaillant sur ce repo :

* Utiliser les prompts sauvegardés dans `.copilot/prompts/` pour chaque phase.
* Tous les commits doivent être faits au fur et à mesure des étapes (voir README).
* Ne pas modifier plus de 3 fichiers dans un seul patch sans alerter l'utilisateur.
* Les tests (`pytest` en backend, Playwright en frontend) doivent être exécutés réellement, jamais simulés.
* La base Supabase locale se lance via `docker-compose up -d`; vérifier connexion avant de continuer.
* Respecter les interdictions listées dans `.github/copilot-instructions.md`.

Référez-vous à `.github/copilot-instructions.md` pour les guides détaillés de phases et conventions.