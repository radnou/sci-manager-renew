# Design System Light-First — GererSCI

**Date** : 2026-03-09
**Statut** : Validé
**Orchestration** : CCPM (Critical Chain) + Kanban Pull

## Contexte

Audit visuel complet (Chrome DevTools + Lighthouse) révélant :
- Landing : Accessibility 92, Best Practices 100, SEO 100
- Dashboard : Accessibility 89, Best Practices 100, SEO 60
- Problèmes : contraste insuffisant, heading order cassé, pas de `<main>` landmark, pas de `<title>`/`<meta>`, 8 KPIs trop denses, empty states inconsistants, dark-only sans light theme

## Décisions de design

### 1. Tokens Tailwind — Light-first

| Décision | Choix |
|----------|-------|
| Thème par défaut | **Light** (palette Slate Tailwind) |
| Dark mode | `prefers-color-scheme: dark` + toggle Settings |
| Accent | **Indigo** (pro, finance, confiance) |
| Fonctionnelles | Success vert, Warning ambre, Error rouge, Info bleu |

```css
:root {
  --ds-bg: #ffffff;
  --ds-surface: #f8fafc;
  --ds-surface-raised: #ffffff;
  --ds-surface-sunken: #f1f5f9;
  --ds-text-primary: #0f172a;
  --ds-text-secondary: #475569;
  --ds-text-muted: #94a3b8;
  --ds-border: #e2e8f0;
  --ds-border-strong: #cbd5e1;
  --ds-accent: #4f46e5;
  --ds-accent-hover: #4338ca;
  --ds-accent-soft: #eef2ff;
  --ds-success: #16a34a;
  --ds-warning: #d97706;
  --ds-error: #dc2626;
  --ds-info: #2563eb;
}

@media (prefers-color-scheme: dark) {
  :root { /* inversions dark */ }
}
[data-theme="dark"] { /* toggle override */ }
```

Structure : `frontend/src/lib/design-system/tokens.css`

### 2. Composants partagés (5)

| Composant | Props clés | Remplace |
|-----------|-----------|----------|
| `EmptyState` | icon, title, description, actions[] | 8 implémentations ad hoc |
| `WorkspaceHeader` | category, title, description, quickActions[] | markup différent /page |
| `KPICard` | value, label, badge?, trend? | styles inconsistants |
| `StatusBadge` | text, variant, size | couleurs/tailles variables |
| `TabBar` | tabs[], activeTab, onTabChange | 3 systèmes d'onglets |

Emplacement : `frontend/src/lib/design-system/components/`
Contraintes : Svelte 5 runes, tokens CSS, Storybook story chacun

### 3. Refactoring pages

#### Dashboard UX — simplification

| Avant | Après |
|-------|-------|
| 8 KPIs empilées | 4 KPIs essentielles (SCI suivies, Patrimoine, Loyer cible, Recouvrement) |
| 4 KPIs secondaires visibles | Déplacées dans onglet Analytique |
| StatusBadge dans chaque KPI | Supprimés (bruit visuel) |
| 5 onglets compressés mobile | TabBar scrollable horizontal |

#### Pages par groupe d'agents

| Agent | Pages |
|-------|-------|
| dashboard | /dashboard |
| workspaces-core | /biens, /locataires, /loyers |
| workspaces-finance | /charges, /fiscalite |
| workspaces-gov | /associes, /documents |
| pricing-landing | /pricing (cas d'usage concrets), / (light theme) |
| compte | /settings, /account |

#### Pricing cleanup

Remplacer "Ils nous font confiance" (étoiles sans vrais témoignages) par 3 cas d'usage concrets et pertinents (gérant solo, cabinet comptable, opérateur patrimonial).

### 4. Accessibilité & SEO

| Problème | Fix | Agent |
|----------|-----|-------|
| color-contrast | Résolu par light-first | Phase 1 |
| link-in-text-block | Underline/font-weight liens | a11y-links |
| document-title | `<svelte:head><title>` par page | a11y-layout |
| meta-description | `<meta name="description">` par page | a11y-layout |
| heading-order | Corriger hiérarchie h1→h2→h3 | a11y-headings |
| landmark-one-main | `<main>` dans +layout.svelte | a11y-layout |

## Orchestration CCPM + Kanban Pull

### Chaîne critique

```
Tokens → [Buffer] → KPICard + TabBar → [Buffer] → Dashboard → [Buffer] → Re-audit Lighthouse
```

### Feeding chains

| Chain | Tâches | Débloquée par |
|-------|--------|---------------|
| FC1 | EmptyState, WorkspaceHeader, StatusBadge | Tokens |
| FC2 | 7 workspaces refactor | Composants |
| FC3 | Pricing + Landing (light) | Tokens |
| FC4 | Settings + Account | Tokens |
| FC5 | A11y layout (main, title, meta) | Tokens |

### Contraintes d'exécution

| Règle | Valeur |
|-------|--------|
| WIP limit | 6 agents max simultanés |
| Pull | Agent libre tire prochaine tâche (critique > feeding > indépendant) |
| Buffers | Vérification gate entre phases (compile, Storybook, E2E) |

### Timeline

```
T0  │ [CRITIQUE] Tokens (1 agent)
    │ [BUFFER 1] tokens compilent + Tailwind consomme
T1  │ [CRITIQUE] KPICard + TabBar
    │ [FC1] EmptyState + WorkspaceHeader + StatusBadge
    │ [FC5] A11y-layout
    │ [BUFFER 2] Storybook check
T2  │ [CRITIQUE] Dashboard
    │ [FC2] Workspaces-core (biens/locataires/loyers)
    │ [FC2] Workspaces-finance (charges/fiscalite)
    │ [FC2] Workspaces-gov (associes/documents)
    │ [FC3] Pricing-landing
    │ [FC4] Compte (settings/account)
    │ [BUFFER 3] E2E pass
T3  │ [FC5] A11y-headings + Lighthouse re-audit
```

## Audit screenshots

Capturés dans `frontend/audit-screenshots/` (14 screenshots + 2 rapports Lighthouse).
