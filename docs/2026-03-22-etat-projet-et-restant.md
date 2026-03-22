# GérerSCI — État du projet & Restant à faire
**Date** : 22 mars 2026 (mis à jour 14h)

---

## Session du 22 mars 2026 — Résumé

### Changements majeurs
- **Pricing** : Payment-first (no trial, no freemium) + garantie 30 jours satisfait ou remboursé
- **Backend** : Trial supprimé (`_create_trial_subscription`, `is_trial_active`, etc.), 1346 tests passants
- **Frontend** : Paywall sécurisé (fallback → redirect /pricing), 0 errors/warnings
- **Lead capture** : Table `lead_captures`, endpoint `/api/v1/leads/capture`, composant `EmailCapture.svelte`
- **Lead magnets SEO** : 3 outils publics (simulateur CERFA, générateur quittance, calendrier fiscal)
- **Email nurture** : 3 templates (bienvenue, valeur, urgence) + service + cron intégré
- **Lifecycle UI** : 5 boutons ajoutés (dissolution SCI, changement gérant, capital, cession bien, sinistre PNO)
- **Légal** : CGV garantie 30j + case L221-28 + médiation mentions légales + CGU plans mis à jour
- **Accessibilité** : lang=fr, dropdown clavier, aria-label, case consentement CGU inscription
- **Audit Big4** : 82.8% conformité (64 points audités)

### Métriques
- Backend : 1346 tests, 1 skipped, 0 failed
- Frontend : 0 errors, 0 warnings (svelte-check)
- 11/11 lifecycle features (API + tests + UI)
- Migration 020 prête (lead_captures + guarantee_expires_at)

---

## À faire AVANT deploy production

| # | Tâche | Effort | Bloquant |
|---|-------|--------|----------|
| 1 | Vérification locale par le fondateur | Variable | Oui |
| 2 | SIRET/TVA dans mentions légales + CGV | Admin | Oui si facturation |
| 3 | Appliquer migration 020 sur Supabase prod | 2 min | Oui |
| 4 | Mettre en mode beta/maintenance le VPS | 15 min | Recommandé |

---

## Mode maintenance / Beta

Le backend intègre un middleware de maintenance activable via env vars :

```bash
# Dans .env.production sur le VPS :
MAINTENANCE_MODE=true        # Active le mode 503 pour tous les visiteurs
BETA_PASSWORD=monsecret      # Permet l'accès beta via header ou cookie

# Redémarrer :
docker compose restart backend

# Accès beta (toi) :
# Header: curl -H "X-Admin-Key: monsecret" https://gerersci.fr/...
# Cookie: beta_access=monsecret dans le navigateur (DevTools > Application > Cookies)

# Toujours actif en maintenance :
# - /api/v1/health (monitoring)
# - /api/v1/stripe/webhooks (paiements)
```

Scripts disponibles : `scripts/maintenance-on.sh` et `scripts/maintenance-off.sh`

---

## Audit VPS sécurité — Résumé

**Score** : 22 SECURE · 16 WARNING · 3 VULNERABILITY (sur 41 points)

### Vulnérabilités corrigées cette session
| # | Finding | Correction |
|---|---------|-----------|
| 1 | Containers Docker root | USER app ajouté aux 2 Dockerfiles |
| 2 | Admin secret dans URL query | X-Admin-Key header + hmac.compare_digest() |
| 3 | server_tokens exposé | server_tokens off ajouté |
| 4 | Headers manquants sur API block | X-Frame-Options, X-Content-Type-Options ajoutés |
| 5 | Supabase proxy sans rate limit | limit_req zone=api ajouté sur /auth/, /rest/, /storage/ |
| 6 | Pas de log rotation Docker | json-file max-size 10m, max-file 3 |
| 7 | OCSP stapling désactivé | Activé avec resolver Cloudflare+Google |

### Restant (à faire sur le VPS)
| # | Finding | Sévérité | Action |
|---|---------|----------|--------|
| 1 | SSH password auth | HIGH | `PasswordAuthentication no` dans sshd_config |
| 2 | Rollback auto CI/CD | MEDIUM | Ajouter step rollback on failure dans deploy.yml |
| 3 | Grafana server block manquant | MEDIUM | Ajouter ou passer à Caddy |
| 4 | Brotli compression | LOW | Passer à Caddy (natif) ou nginx-brotli |

---

## Findings audit — Sous 30 jours

### RGPD
| # | Finding | Sévérité | Effort |
|---|---------|----------|--------|
| 1 | Procédure breach notification (Art. 33-34) | MAJEUR | 1h (doc interne) |
| 2 | Bouton "Gérer cookies" dans le footer | MINEUR | 30 min |
| 3 | Purge auto logs > 12 mois (cron) | MINEUR | 1h |
| 4 | DPA documentés pour sous-traitants | MINEUR | Admin |

### Accessibilité (WCAG 2.1 AA)
| # | Finding | Sévérité | Effort |
|---|---------|----------|--------|
| 5 | Résiliation 3 clics in-app (loi 2022) | MAJEUR | 2h |
| 6 | Lien désinscription dans emails Resend | MAJEUR | 1h |
| 7 | Focus trap lightbox + cookie banner | MAJEUR | 1h |
| 8 | Sidebar aria-hidden fix desktop | MAJEUR | 30 min |
| 9 | Arrow-key navigation tabs fiche bien | MAJEUR | 1h |
| 10 | prefers-reduced-motion CSS global | MINEUR | 10 min |
| 11 | Checkout error role="alert" | MAJEUR | 5 min |
| 12 | Register aria-describedby validation | MAJEUR | 15 min |

### Légal
| # | Finding | Sévérité | Effort |
|---|---------|----------|--------|
| 13 | Nommer le médiateur dans CGU/CGV | MAJEUR | Admin |
| 14 | SIRET + TVA intracommunautaire | CRITIQUE | Admin |

---

## Backlog produit

### P1 — Priorité haute
| Tâche | Impact | Effort estimé |
|-------|--------|---------------|
| Google Ads "déclaration 2044 SCI" | Acquisition pré-saison fiscale mai | Setup |
| SEO articles (5-10 longue traîne) | Organique long terme | Contenu |
| Contact 10 expert-comptables | Canal distribution B2B2C | Outreach |
| Comptabilité simplifiée (grand livre) | Feature gap vs Ownily | 2-3 jours |
| Déclaration 2072 (SCI IS) | Marché élargi | 2-3 jours |

### P2 — Backlog
| Tâche | Impact | Effort estimé |
|-------|--------|---------------|
| Export FEC | Obligation comptable | 1-2 jours |
| Intégration bancaire (Powens) | Différenciateur | 1-2 semaines |
| Mobile responsive audit | UX mobile | 1 jour |
| Remotion vidéos marketing | Conversion landing | 2-3 jours |

---

## Analyse concurrentielle — Ownily

| Critère | GérerSCI | Ownily |
|---------|----------|--------|
| Prix entrée | 19€/mois | 8,25€/mois |
| Free tier | Non (payment-first) | Non (trial 14j) |
| Simulateur gratuit | 3 outils SEO | Aucun |
| Comptabilité | Basique | Complète (bilan, IS) |
| Synchro bancaire | Non | Oui (Powens) |
| SCI IS | Non | Oui |
| LMNP | Non | Oui |
| Adossement | Indépendant | Crédit Mutuel Arkéa |
