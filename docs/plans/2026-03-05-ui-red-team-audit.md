# Audit UI Red Team - 5 mars 2026

## Portée

- Audit visuel et produit réalisé sur l'interface `GererSCI` avec Chrome local.
- Relecture croisée à partir des captures fournies par le porteur du projet et d'un passage desktop `1440x1100` / mobile `390x844`.
- Pages rejouées dans l'espace connecté: `dashboard`, `scis`, `biens`, `loyers`.
- Shell global inspecté: navigation, fil d'Ariane, footer, états d'erreur, cohérence des libellés.

## Synthèse

- Le socle visuel est déjà plus premium qu'au démarrage: typographie, cartes, hiérarchie globale et espace connecté distinct fonctionnent.
- Les écarts les plus critiques étaient moins des bugs d'affichage "pixel perfect" que des défauts de narration produit: KPI financiers trompeurs, libellés backend encore visibles, messages d'erreur bruts, shell connecté trop chargé et footer non contextualisé.
- La page `SCI` reste la zone la plus dense. Elle raconte bien le portefeuille multi-SCI, mais elle empile encore trop d'information sur mobile.
- Le module PDF a un meilleur cadre UX, mais il reste à revalider bout en bout contre un backend réel pour confirmer la génération et la prévisualisation.

## Findings détaillés

### 1. Shell global

État observé:

- La top navigation connectée exposait trop d'entrées simultanément: `Cockpit`, `SCI`, `Biens`, `Loyers`, `Tarifs`, `Compte`, `Paramètres`, `Confidentialité`, email et `Déconnexion`.
- Le footer restait en logique publique même pour un utilisateur connecté, avec `Connexion` et `Inscription` visibles en bas d'un écran authentifié.
- Le fil d'Ariane est présent et lisible, mais la perception d'ensemble restait "chargée" sur desktop.

Correction appliquée:

- Regroupement des entrées `Compte`, `Paramètres`, `Confidentialité` et `Déconnexion` dans un menu compte desktop plus compact et plus lisible.
- Fermeture automatique du menu compte sur changement de route et fermeture manuelle possible via `Escape`.
- Footer contextualisé: un utilisateur connecté voit désormais des raccourcis de pilotage et de compte, plus les liens publics de connexion.

Impact produit:

- La barre haute redevient un outil d'orientation, pas une liste plate de destinations.
- La cohérence entre état connecté et chrome applicatif est nettement meilleure.

### 2. Dashboard

État observé:

- Le cockpit montrait un indicateur `Flux encaissés` calculé sur la somme de toutes les lignes de loyers, y compris les loyers en attente.
- Le badge `Recouvrement` pouvait afficher `50%` tout en marquant la situation comme `conforme`, ce qui est trompeur pour un usage de pilotage.
- Les priorités ne prenaient pas en compte le cas `encaissements en attente sans retard`.

Correction appliquée:

- Refactor des métriques loyers: distinction entre `total enregistré`, `total payé`, `reste à encaisser` et `taux de recouvrement`.
- Le cockpit affiche maintenant les `flux réellement encaissés`.
- Les badges et priorités reflètent désormais trois cas:
  - retard avéré,
  - encaissements à sécuriser,
  - situation réellement sous contrôle.

Impact produit:

- Le dashboard devient défendable devant un utilisateur métier.
- Les KPI n'enjolivent plus la trésorerie.

### 3. Portefeuille SCI

État observé:

- La page `SCI` avait une bonne structure macro, mais laissait passer plusieurs libellés techniques ou semi-techniques: `gerant`, `associe`, `paye`, `en_attente`, types de biens non humanisés.
- Un message JSON brut du type `{"detail":"Invalid bearer token"}` pouvait remonter directement à l'écran.
- La page reste très longue sur mobile, avec une accumulation de blocs de même poids visuel.

Correction appliquée:

- Humanisation des rôles associés, statuts loyers, types de biens et types de charges.
- Transformation des erreurs API connues en messages produit lisibles.

Risque restant:

- La densité mobile de `SCI` reste élevée.
- Pour une deuxième passe UX, il faudra probablement:
  - introduire des sections repliables sur mobile,
  - remonter les 2 ou 3 panneaux décisifs au-dessus du pli,
  - réduire la hauteur des blocs secondaires (`Fiscalité`, `Charges récentes`, `Activité locative récente`).

### 4. Biens

État observé:

- Le formulaire est clair, métier, et n'expose plus d'identifiants.
- La lecture portefeuille > formulaire > tableau fonctionne bien.
- Le tableau reste propre sur desktop, mais son ergonomie mobile dépend encore du scroll horizontal.

Constat produit:

- Le manque principal n'est plus l'ajout, mais l'absence d'actions de maintenance directement dans la table.

Backlog:

- Ajouter `Modifier` et `Supprimer` dans la table.
- Prévoir une variante mobile "cartes" ou un tableau responsive plus narratif.

### 5. Loyers

État observé:

- Les statuts sont maintenant métiers et compréhensibles.
- Le formulaire est plus lisible que la version brute précédente.
- La KPI principale reflète désormais les flux réellement encaissés.

Constat produit:

- Comme pour les biens, le point faible restant est l'absence d'actions de correction dans le journal.
- Le tableau est propre, mais encore un peu utilitaire visuellement sur petit écran.

Backlog:

- Ajouter édition / suppression.
- Ajouter filtres simples par période et statut.

### 6. PDF / quittance

État observé:

- Le module de génération a maintenant un meilleur cadrage UX: sélection d'un loyer lisible, informations de contexte, téléchargement et ouverture dédiée.
- Un fallback navigateur est prévu si la prévisualisation intégrée échoue.

Risque restant:

- La robustesse réelle du PDF dépend encore du backend local ou distant.
- Une validation complète doit être refaite avec un backend actif, un token valide et une réponse PDF réelle.

### 7. Responsiveness

Desktop:

- Bonne lisibilité générale.
- Le shell est désormais plus calme après regroupement du compte.
- Les cartes KPI restent cohérentes et crédibles.

Mobile:

- Le menu mobile connecté est lisible, correctement segmenté et utilisable.
- `SCI` reste trop longue et trop homogène visuellement.
- `Biens` et `Loyers` sont correctes, mais gagneraient à adopter un mode "cards" en dessous de `md`.

## Correctifs exécutés pendant cette passe

- Menu compte desktop accessible et footer connecté contextualisé.
- Messages d'erreur API humanisés dans le shell applicatif et les principaux écrans.
- KPI loyers refactorés pour distinguer encaissé vs enregistré.
- Humanisation des libellés métier sur la page `SCI`.
- Cohérence de narration améliorée dans le cockpit.

## Recommandations pour la phase suivante

1. Passer `SCI` en véritable fiche d'identité pilotable avec sections repliables mobile-first.
2. Ajouter CRUD complet sur `biens`, `loyers`, `associés`, `charges`.
3. Introduire un mode responsive "cartes métier" pour les tables sur mobile.
4. Rejouer la génération de PDF contre un backend réel et verrouiller ce parcours par test E2E dédié.
5. Ajouter un audit accessibilité complémentaire Lighthouse sur `dashboard` et `scis` après stabilisation UI.
