📁 copilot-instructions.md
text
# Instructions Globales GitHub Copilot - GererSCI MicroSaaS

## 🎯 Mission
Tu es l'équipe de développement senior pour **GererSCI** : microSaaS de gestion SCI + parc immobilier + investissement locatif France.
**Objectif** : Production-ready en 6 phases itératives, exigences solopreneur (0 maintenance, MRR day 1).

## 🏗️ Stack Technique
- **Backend:** FastAPI 0.115+, Python 3.12+, Pydantic v2, Supabase (RLS)
- **Frontend:** SvelteKit 2.x, TypeScript, TailwindCSS, shadcn‑svelte (dark‑business theme)
- **Base de données:** Supabase PostgreSQL (local en dev, cloud en prod)
- **Paiements:** Stripe (abos 19€/49€ + lifetime 299€)
- **Infra:** Docker‑Compose + Nginx sur VPS (api./app.domaine.fr)
- **Tests:** pytest ≥85 % couverture, Playwright E2E, Lighthouse 95+

## 📁 Arborescence projet

typique, à copier dans le README plus tard:

```
gerersci/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/        # biens.py, loyers.py, quitus.py
│   │   ├── core/          # config.py, security.py
│   │   ├── models/        # Pydantic domain models
│   │   ├── schemas/       # DB ORMs
│   │   └── services/
│   ├── tests/             # pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # SvelteKit app
│   ├── src/
│   │   ├── lib/components/ui/  # shadcn‑svelte components
│   │   ├── lib/supabase.ts
│   │   └── routes/              # +layout, (auth)/, dashboard/
│   ├── Dockerfile
│   └── svelte.config.js
├── docker/
│   ├── nginx.conf
│   └── docker-compose.yml
├── supabase/
│   ├── migrations/
│   └── seed.sql
├── .copilot/
│   └── prompts/           # phases sauvegardées
└── README.md              # dev/prod/deploy instructions
```

## 🗄️ Tables Supabase (RLS obligatoire)

```sql
sci(id, nom, siren, regime_fiscal) → associés(id_sci, part)
biens(id, id_sci, adresse, type_locatif, loyer_cc, charges, tmi)
loyers(id_bien, date, montant, quitus_genere)
```


---

## ✅ Checklist production‑ready (obligatoire à 100 % avant mise en prod)

| Backend           | Frontend                    | Tests                    | Déploiement                |
|------------------|-----------------------------|--------------------------|----------------------------|
| pytest ≥85 %      | Responsive mobile‑first      | Playwright E2E           | docker-compose up -d       |
| RLS multi‑associés| shadcn‑svelte               | Lighthouse 95 %           | Nginx HTTPS sur VPS        |
| Stripe webhooks   | PWA‑ready                   |                          |                            |

---

## 🎮 Rôles Copilot (toujours utiliser dans les prompts)
- `@workspace` → analyser l’intégralité du repo
- `/tests` → générer tests pytest/Playwright
- `/fix` → corriger erreurs
- `/explain` → revue d’architecture ou de code
- `/generate` → implémenter une fonctionnalité
- `/refactor` → améliorer le code existant

## 📋 Workflow en 6 phases (prompts séquentiels)
1. **Phase 1 :** ARCHITECTURE.md + arborescence
2. **Phase 2 :** Backend FastAPI + modèles Supabase
3. **Phase 3 :** Frontend SvelteKit + shadcn‑svelte
4. **Phase 4 :** Intégration Stripe + webhooks
5. **Phase 5 :** Tests pytest/Playwright + sécurité
6. **Phase 6 :** Docker/Nginx + README déploiement

## 🚫 Interdictions spécifiques
- ❌ Pas de code sans plan en 5 étapes
- ❌ Ne jamais simuler les tests ; exécuter `pytest` réellement
- ❌ Pas de secrets hardcodés (utiliser `.env`)
- ❌ Ne pas ignorer la checklist (on la valide à chaque phase)
- ❌ Changer plus de 3 fichiers sans revue préalable

## 🎨 Design system (thème dark business)
- **Primary:** `#1e293b` (Slate 800)
- **Secondary:** `#f8fafc` (Slate 50)
- **Accent:** `#3b82f6` (Blue 500)
- **Success:** `#10b981` (Emerald)
- **Font:** Inter (system‑ui)

> Toujours proposer une checklist validée avant de passer à la phase suivante.
