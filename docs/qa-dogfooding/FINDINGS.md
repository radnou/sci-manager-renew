# QA Dogfooding — Findings Log

> Chaque session de dogfooding documente ses findings ici.
> Utiliser le template ci-dessous pour chaque bug/friction trouvé.

## Session Template

```markdown
## Session YYYY-MM-DD

**Testeur** : [Nom]
**Level** : 1 (smoke) / 2 (auto) / 3 (manuel)
**Persona** : Jean-Pierre / Marie / Thomas / Admin / Mobile
**Durée** : XX minutes
**Résultat global** : ✅ OK / ⚠️ Findings / ❌ Bloquant
```

## Finding Template

```markdown
### [DF-XXX] Titre court

**Sévérité** : 🔴 P0 | 🟡 P1 | 🟢 P2
**Persona** : Jean-Pierre / Marie / Thomas / Admin / Mobile
**Parcours** : DF-XX étape Y / Persona Z étape W
**Page** : /chemin/de/la/page
**Attendu** : Ce qui devrait se passer
**Observé** : Ce qui se passe réellement
**Screenshot** : `e2e-artifacts/dogfooding/xxx.png`
**Console** : (erreurs JS si applicable)
**Reproductible** : Toujours / Intermittent / Une fois
**Fix suggéré** : (optionnel)
**Status** : 🆕 Nouveau | 🔄 En cours | ✅ Fixé | ⏭️ Reporté
```

---

## Findings

<!-- Ajouter les findings ci-dessous, les plus récents en premier -->

## Session 2026-04-11

**Testeur** : Murat (TEA automatisé)
**Level** : 2 (auto)
**Durée** : 8.5 secondes (tests publics uniquement)
**Résultat global** : ⚠️ Findings

### [DF-001] Health endpoint renvoie 503

**Sévérité** : 🟡 P1
**Parcours** : DF-10 API Latency
**Page** : `GET https://api.gerersci.fr/health/ready`
**Attendu** : HTTP 200 avec `{"status": "ready", "summary": {"ready_for_traffic": true}}`
**Observé** : HTTP 503 en 132ms — backend up mais pas "ready"
**Console** : N/A (API directe)
**Reproductible** : Toujours (au moment du test)
**Fix suggéré** : Vérifier les checks internes du health endpoint (DB connection, Supabase reachability). Possiblement un timeout trop strict sur un check interne.
**Status** : 🆕 Nouveau

### [DF-002] Pricing CTA buttons labellés "Démarrer pour X€/mois" (pas "Choisir")

**Sévérité** : 🟢 P2 (cosmétique / test calibration)
**Parcours** : DF-12 Pricing Integrity
**Page** : `/pricing`
**Attendu** : Le test cherchait "Choisir Gestion" (ancien wording du smoke existant)
**Observé** : Buttons sont "Démarrer pour 19€/mois", "Démarrer pour 39€/mois", "Devenir Fondateur"
**Fix suggéré** : Test corrigé. Vérifier aussi `smoke-public.spec.ts:27` qui cherche encore "Choisir Gestion".
**Status** : ✅ Fixé (dans dogfooding.spec.ts)
