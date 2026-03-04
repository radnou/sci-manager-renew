# Frontend SCI Manager

Interface SvelteKit orientée exécution métier pour la gestion SCI:

- landing orientée conversion,
- cockpit dashboard,
- gestion `biens` / `loyers`,
- génération de quittances.

## 1) Objectifs produit frontend

- Rendre visibles les KPI clés sans retraitement manuel.
- Réduire la friction de saisie pour les opérations quotidiennes.
- Uniformiser la qualité UX via un design system documenté (Storybook).

## 2) Scripts principaux

```bash
pnpm run dev                # développement local
pnpm run check              # typecheck + diagnostics Svelte
pnpm run build              # build production
pnpm run storybook          # Storybook local
pnpm run build-storybook    # build Storybook statique
pnpm run test:high-value    # couverture >= 90% sur logique métier critique
```

## 3) Couverture haute valeur

`test:high-value` cible les modules à impact business direct:

- `src/lib/api.ts`
- `src/lib/high-value/biens.ts`
- `src/lib/high-value/loyers.ts`
- `src/lib/high-value/formatters.ts`

Seuils minimum imposés:

- lines >= 90%
- branches >= 90%
- functions >= 90%
- statements >= 90%

## 4) Structure fonctionnelle

- `src/routes/+page.svelte`: landing et proposition de valeur.
- `src/routes/dashboard/+page.svelte`: synthèse portefeuille.
- `src/routes/biens/+page.svelte`: gestion des actifs.
- `src/routes/loyers/+page.svelte`: suivi encaissements.
- `src/lib/components/`: composants métier réutilisables.
- `src/lib/high-value/`: logique métier pure testable.
- `src/stories/`: documentation design system et compositions d'écran.

## 5) Règles d'implémentation

- TypeScript strict et gestion d'erreurs explicite.
- États UI systématiques: `loading`, `empty`, `error`.
- Composants orientés réutilisation et testabilité.
- Aucune logique critique cachée exclusivement dans les composants visuels.
