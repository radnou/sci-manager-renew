# Audit Hormozi Full Funnel — GérerSCI

**Date**: 2026-03-27
**Scope**: Full funnel + UX features (Approche B — Hormozi Chirurgical)
**Cible**: Gérants SCI indépendants, arrivant via SEO ou bouche-à-oreille
**Principe**: Maximiser `(Rêve × Preuve) / (Délai × Effort)` adapté mentalité française

---

## Vue d'ensemble des changements

```
AVANT:  Landing (features) → /pricing (brutal) → checkout → onboarding (formulaires) → app (muette)
APRÈS:  Landing (rêve+preuve) → aperçu (valeur démontrée) → pricing (intégré) → onboarding (wow) → app (célébrations)
```

### Fichiers impactés (estimation)

| Zone | Fichiers | Type de changement |
|------|----------|-------------------|
| Hero + CTAs | `routes/+page.svelte` | Réécriture copy + restructuration hero |
| Flow pricing | `routes/+page.svelte`, `routes/pricing/+page.svelte` | Nouveau parcours, suppression redirect brutal |
| Aperçu interactif | `routes/+page.svelte` (nouvelle section) | Nouvelle section "comment ça marche" |
| Lead magnet bridge | `routes/simulateur-cerfa/+page.svelte`, nouveau composant | CTA renforcé post-simulation |
| Onboarding wow | `routes/(app)/onboarding/+page.svelte` | Restructurer pour montrer valeur avant formulaires |
| Célébrations | Nouveau `lib/components/Celebration.svelte` + intégrations | 3 points d'injection |
| Quittance UX | `lib/components/fiche-bien/FicheBienLoyers.svelte` | Améliorer le flow de génération |
| Notification prefs | Nouveau `routes/(app)/settings/notifications/+page.svelte` | Nouvelle page |
| Fiche bien guidance | `lib/components/fiche-bien/FicheBienIdentite.svelte` | Ajout hints contextuels |

---

## Section 1 : Hero + CTAs — Vendre le rêve

### État actuel
```
Badge:    "Pour les gérants de SCI en France"
H1:       "Votre SCI mérite mieux qu'un tableur Excel."
Sub:      "Gérez vos biens, locataires et fiscalité depuis un seul tableau de bord"
CTA:      "Démarrer à partir de 19€/mois" → /pricing
Trust:    EU hosting, RGPD, 30j garantie, annulation
```

### Problèmes
- Headline = ce qu'on quitte (Excel), pas ce qu'on gagne
- Sub = features, pas résultats
- CTA = prix AVANT valeur → le cerveau calcule coût, pas bénéfice
- Badge générique, pas de preuve sociale

### Design cible
```
Badge:    "Utilisé par des gérants de SCI partout en France"
H1:       "Vos loyers encaissés. Votre fiscalité claire. Votre SCI sous contrôle."
Sub:      "Tout ce qu'il faut pour piloter votre SCI en 10 minutes par mois —
           biens, baux, quittances, CERFA 2044, le tout au même endroit."
CTA 1:    "Voir comment ça marche" → scroll #comment-ca-marche (primaire, gradient)
CTA 2:    "Comparer les plans" → scroll #pricing (secondaire, outline)
Trust:    🇫🇷 Hébergé en France · 🔒 Conforme RGPD · 💶 Satisfait ou remboursé 30j
```

### Règles
- Pas de superlatif marketing ("révolutionnaire", "le meilleur")
- Ton factuel et compétent — le Français achète la maîtrise
- Le prix n'apparaît JAMAIS avant que la valeur soit démontrée
- "Hébergé en France" avec drapeau 🇫🇷 (plus fort que 🇪🇺 pour la cible)

---

## Section 2 : Parcours Pricing — Supprimer la redirection brutale

### Problème actuel
Le CTA hero envoie directement sur `/pricing` — page dédiée, froide, avec checkbox légale avant même de voir les plans. Le visiteur SEO froid arrive sur une page de vente pure sans contexte de valeur.

### Design cible : Pricing intégré dans le parcours naturel

**Changement 1 — La landing page CONTIENT le pricing**
La section `#pricing` existe déjà dans la landing (lignes ~600-800). Elle est fonctionnelle. Le problème est que le CTA hero BYPASSE tout le contenu pour aller sur `/pricing`.

→ **Fix** : Le CTA hero scrolle vers `#comment-ca-marche` (nouvelle section), puis le visiteur découvre naturellement features → aperçu → pricing dans le scroll.

**Changement 2 — La page /pricing reste mais change de rôle**
- `/pricing` n'est plus la destination du CTA hero
- Elle sert pour : liens directs partagés, retour depuis l'app, deep links
- On y ajoute un résumé de valeur en haut (3 bullets des résultats clés) avant les plans
- La checkbox L221-28 passe APRÈS le choix du plan, pas avant

**Changement 3 — Consent flow repensé**
```
AVANT:  Checkbox consent → voir plans → cliquer plan → Stripe
APRÈS:  Voir plans → cliquer plan → modal confirmation (consent + récap) → Stripe
```
La checkbox légale est obligatoire (article L221-28) mais ne doit pas être un mur AVANT le choix. Elle apparaît dans une modal de confirmation après le clic sur "Choisir ce plan", avec :
- Récapitulatif du plan choisi (nom, prix, features clés)
- Checkbox L221-28
- Bouton "Confirmer et payer"

**Composant** : `CheckoutConfirmModal.svelte` dans `lib/components/`
- Props : `plan` (name, price, features[]), `billingPeriod`, `onConfirm`, `onCancel`
- Réutilisé sur landing (#pricing) ET page /pricing
- Le bouton "Confirmer" est disabled tant que la checkbox n'est pas cochée

### Page /pricing — Header de valeur ajouté
```
Avant les plans:
┌─────────────────────────────────────────────────┐
│  Ce que GérerSCI remplace :                     │
│  ✅ Suivi des loyers et alertes impayés         │
│  ✅ Génération quittances PDF en 1 clic         │
│  ✅ Pré-remplissage CERFA 2044 automatique      │
│  ✅ Vue financière consolidée multi-SCI          │
│                                                  │
│  → En moyenne, ça remplace 150€/mois de          │
│    tableurs, erreurs et temps perdu.             │
└─────────────────────────────────────────────────┘
```

---

## Section 3 : Aperçu Interactif — Le pont entre intérêt et paiement

### Problème
Entre "je suis intéressé" et "voici le prix", il n'y a RIEN qui montre concrètement l'outil. Les screenshots existent mais sont statiques et noyés dans les features.

### Design : Section "Comment ça marche" (id="comment-ca-marche")

Position : APRÈS le hero, AVANT les features détaillées.

```
H2: "Comment ça marche — en 3 étapes"

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  ① Créez votre   │  │  ② Ajoutez vos   │  │  ③ Pilotez en    │
│     SCI           │  │     biens et      │  │     10 min/mois  │
│                   │  │     locataires    │  │                   │
│  2 minutes.       │  │                   │  │  Quittances,     │
│  Nom, régime      │  │  Adresse, loyer,  │  │  alertes, CERFA, │
│  fiscal, c'est    │  │  bail — on vous   │  │  tout est là.    │
│  tout.            │  │  guide.           │  │                   │
│                   │  │                   │  │                   │
│  [screenshot      │  │  [screenshot      │  │  [screenshot     │
│   onboarding]     │  │   fiche bien]     │  │   dashboard]     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### Règles
- Screenshots RÉELLES de l'app (pas de maquettes)
- Chaque étape = résultat + temps requis (réduit le dénominateur Hormozi)
- Cliquables pour ouvrir le lightbox existant
- Mobile : stack vertical, même contenu

### Optionnel futur (pas dans ce scope)
- Vidéo démo 90 secondes (narration sobre, pas de musique corporate)
- Sandbox interactive (faux dashboard pré-rempli consultable sans compte)

---

## Section 4 : Lead Magnet → Produit Bridge

### Problème actuel
Le simulateur CERFA capture l'email mais le CTA vers le produit payant est faible. Le générateur de quittance public n'existe pas encore.

### Design : Pont post-simulation renforcé

**Simulateur CERFA — après le résultat :**
```
┌─────────────────────────────────────────────────────────┐
│  ✅ Votre estimation CERFA 2044 : -3 240 € (déficit)   │
│                                                          │
│  📊 Ce calcul est une estimation simplifiée.             │
│                                                          │
│  Avec GérerSCI, le CERFA 2044 se pré-remplit             │
│  automatiquement à partir de vos loyers et charges       │
│  réels — pas besoin de ressaisir.                        │
│                                                          │
│  [Voir comment ça marche →]  (lien vers landing #ccm)   │
│                                                          │
│  Déjà convaincu ?                                        │
│  [Démarrer maintenant →]  (lien vers landing #pricing)   │
└─────────────────────────────────────────────────────────┘
```

### Principes
- Le CTA n'est PAS "Acheter" — c'est "Voir comment" (engagement faible)
- On montre le DELTA entre le simulateur limité et l'outil complet
- Deux niveaux d'intention : curieux ("voir") et convaincu ("démarrer")
- Pas d'agressivité — le Français déteste se sentir "vendu"

### Générateur de quittance public (futur, hors scope immédiat)
- Lead magnet SEO à fort volume (30-50K recherches/mois)
- Même pattern : résultat gratuit → pont vers fonctionnalité complète
- À traiter dans un spec séparé

---

## Section 5 : Onboarding — Injecter le "Wow Moment"

### Problème actuel
L'onboarding est un wizard de 4 étapes de formulaires. L'utilisateur remplit, remplit, remplit... et arrive sur un dashboard vide. Pas de moment "ah, ça y est, je vois la valeur".

### Design : "Show value BEFORE asking for input"

**Restructuration du wizard :**

```
AVANT:  Étape 1 (formulaire SCI) → 2 (formulaire bien) → 3 (formulaire bail) → 4 (bienvenue) → dashboard vide
APRÈS:  Étape 1 (formulaire SCI) → 2 (formulaire bien) → 3 (formulaire bail) → 4 (PREVIEW de la valeur) → dashboard pré-rempli
```

**Nouvelle étape 4 — "Votre SCI est prête" (remplace le simple écran de bienvenue)**

```
┌──────────────────────────────────────────────────────────┐
│  🎉 Votre SCI "{nom}" est configurée !                  │
│                                                           │
│  Voici ce que GérerSCI a préparé pour vous :             │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ 1 bien   │  │ 1 bail   │  │ Prochain │               │
│  │ actif    │  │ en cours │  │ loyer :  │               │
│  │          │  │          │  │ 1er avril│               │
│  └──────────┘  └──────────┘  └──────────┘               │
│                                                           │
│  💡 Prochaines actions suggérées :                       │
│  → Enregistrer votre premier loyer (2 clics)             │
│  → Générer votre première quittance PDF                  │
│  → Configurer les alertes de retard                      │
│                                                           │
│  [Aller au tableau de bord →]                            │
└──────────────────────────────────────────────────────────┘
```

### Principes
- Montrer le RÉSULTAT de ce que l'utilisateur vient de saisir
- Les 3 cartes KPI = preview du dashboard → crée anticipation
- Les "prochaines actions" = guidance, pas obligation
- L'utilisateur arrive sur le dashboard en sachant QUOI FAIRE ensuite

### Animation
- Les 3 cartes apparaissent avec un léger stagger (100ms chacune)
- Confetti subtil (pas excessif — 15-20 particules, couleurs de la marque, 2 secondes)
- Ton : célébration sobre, pas infantilisant

---

## Section 6 : Célébrations In-App — 3 Milestones

### Problème
L'app est muette. L'utilisateur fait des actions importantes et ne reçoit aucun feedback émotionnel. C'est comme remplir un formulaire des impôts — correct mais sans joie.

### Design : 3 moments de célébration

**Composant réutilisable : `Celebration.svelte`**

```svelte
Props:
  - type: 'confetti' | 'checkmark' | 'badge'
  - title: string
  - subtitle: string
  - duration: number (ms, default 3000)
  - onDismiss: () => void
```

Overlay léger (pas de modal bloquant), disparaît automatiquement ou au clic.

**Milestone 1 — Premier loyer enregistré**
```
Trigger:  POST /loyers réussi ET localStorage.getItem('milestone_first_loyer') === null
          → après succès, set localStorage 'milestone_first_loyer' = true
Note:     Pas besoin de compter côté backend — localStorage suffit (one-shot, même device)
Affichage:
  ✅ "Premier loyer enregistré !"
  "Votre suivi de trésorerie commence. GérerSCI calcule maintenant
   votre taux de recouvrement automatiquement."
Type: checkmark animé (cercle vert qui se dessine)
```

**Milestone 2 — Première quittance PDF générée**
```
Trigger:  POST /quitus réussi ET c'est la première quittance
Affichage:
  📄 "Quittance générée !"
  "Vos locataires reçoivent un document professionnel conforme.
   Fini les modèles Word."
Type: badge avec animation slide-in
```

**Milestone 3 — Tableau de bord complet (≥1 SCI, ≥1 bien, ≥1 loyer, ≥1 quittance)**
```
Trigger:  Chargement dashboard ET toutes conditions remplies ET !localStorage.seen_complete
Affichage:
  🎯 "Votre SCI est 100% opérationnelle"
  "Loyers, quittances, fiscalité — tout est en place.
   GérerSCI travaille pour vous."
Type: confetti subtil (15 particules, 2s)
Persiste: localStorage flag pour ne montrer qu'une fois
```

### Adaptation française
- Pas de "You're awesome!" ou "Amazing!" — les Français trouvent ça cringe
- Ton : factuel + encourageant. "C'est fait." > "Bravo, vous êtes incroyable !"
- Animations subtiles, pas de confettis arc-en-ciel façon Duolingo
- Chaque célébration rappelle la VALEUR concrète de l'action

---

## Section 7 : Quittance — De formulaire à moment magique

### Problème actuel
`FicheBienLoyers.svelte` : bouton "Générer quittance" → appel API → PDF s'ouvre dans un nouvel onglet. Fonctionnel mais invisible émotionnellement.

### Design : Flow amélioré

**Changement 1 — Feedback visuel inline**
Après le clic "Générer quittance" :
```
AVANT:  Loading spinner → nouvel onglet (l'utilisateur ne sait pas si ça a marché)
APRÈS:  Loading spinner → toast de succès avec lien
        "✅ Quittance mars 2026 générée — Ouvrir le PDF · Envoyer par email"
```

**Changement 2 — Action "Envoyer par email" (one-click)**
Ajouter un bouton à côté de "Ouvrir le PDF" :
```
[📄 Ouvrir le PDF]  [📧 Envoyer au locataire]
```
Si le locataire a un email renseigné dans le bail → envoi direct via Resend.
Sinon → tooltip "Ajoutez l'email du locataire dans l'onglet Bail".

**Backend requis** : Nouveau endpoint `POST /api/v1/quitus/{quitus_id}/send-email`
- Récupère le PDF depuis Supabase Storage
- Envoie via Resend au locataire du bail associé
- Retourne 200 + toast frontend "Quittance envoyée à {email}"

**Changement 3 — Statut de quittance dans la liste des loyers**
Ajouter une colonne/icône dans le tableau des loyers :
```
| Période  | Montant  | Statut | Quittance |
|----------|----------|--------|-----------|
| Mars 26  | 1 200 €  | ✅ Payé | 📄        |  ← icône cliquable si quittance existe
| Fév 26   | 1 200 €  | ✅ Payé | —         |  ← pas encore générée
| Jan 26   | 1 200 €  | 🔴 Retard | —       |
```

---

## Section 8 : Notifications — UI Préférences

### Problème
Le `NotificationCenter.svelte` affiche les notifications mais il n'y a AUCUNE UI pour configurer les préférences (quels types recevoir, fréquence, email vs in-app). Le backend a les endpoints (`notification_preferences.py`) mais le frontend n'a pas la page.

### Design : Page `/settings/notifications`

```
H2: "Préférences de notifications"

┌──────────────────────────────────────────────────────────┐
│  Type de notification          │  In-app  │  Email       │
│───────────────────────────────│──────────│──────────────│
│  🔴 Loyer en retard            │  [✅]    │  [✅]        │
│  📅 Bail arrivant à échéance   │  [✅]    │  [✅]        │
│  🛡️ Assurance PNO expirante   │  [✅]    │  [ ]         │
│  📄 Document prêt              │  [✅]    │  [ ]         │
│  💰 Loyer enregistré           │  [✅]    │  [ ]         │
│  📊 Résumé mensuel             │  —       │  [✅]        │
└──────────────────────────────────────────────────────────┘

[Enregistrer les préférences]
```

### Règles
- Toggle switches (pas checkboxes) pour le côté moderne
- Grouper par priorité : les alertes critiques en haut
- "Loyer en retard" et "Bail échéance" = activés par défaut, non désactivables pour l'email (obligation de gestion)
- Sauvegarde optimiste avec toast de confirmation
- Accessible depuis `/settings` (onglet ou lien dans le menu compte)

---

## Section 9 : Fiche Bien — Guidance contextuelle

### Problème
Le mode édition de `FicheBienIdentite.svelte` est un formulaire CRUD nu : labels + inputs, pas de contexte. Un gérant de SCI non-tech ne sait pas pourquoi remplir certains champs (DPE, surface Carrez, etc.).

### Design : Help hints contextuels

**Implémentation : Tooltip/popover sur les labels**

```
Surface habitable (m²)  ⓘ
                         ┌─────────────────────────────────┐
                         │ Obligatoire pour le bail et le   │
                         │ calcul de la taxe foncière.      │
                         │ Loi Boutin pour les locations.   │
                         └─────────────────────────────────┘

Classement DPE  ⓘ
                 ┌─────────────────────────────────────────┐
                 │ Obligatoire dans toute annonce et bail   │
                 │ depuis 2023. Les logements F et G sont   │
                 │ progressivement interdits à la location. │
                 └─────────────────────────────────────────┘

Prix d'acquisition (€)  ⓘ
                          ┌───────────────────────────────────┐
                          │ Nécessaire pour calculer votre     │
                          │ rentabilité et la plus-value en    │
                          │ cas de revente. Frais de notaire   │
                          │ inclus.                            │
                          └───────────────────────────────────┘
```

### Règles
- Icône ⓘ discrète à côté du label (gris clair, pas intrusif)
- Popover au hover (desktop) / tap (mobile)
- Contenu : 1-2 phrases max, toujours mentionner POURQUOI c'est utile
- Pas de hints sur les champs évidents (adresse, ville, code postal)
- Hints uniquement sur : surface, DPE, prix acquisition, type de location, régime fiscal
- Composant réutilisable `FieldHint.svelte` avec prop `text`

### Complétude du profil bien
Ajouter un indicateur de complétude en haut de la fiche :
```
Profil du bien : 7/10 champs renseignés  [████████░░] 70%
💡 Complétez le DPE et le prix d'acquisition pour débloquer le calcul de rentabilité.
```

- Barre de progression avec couleur (rouge <50%, orange 50-80%, vert >80%)
- Message contextuel indiquant ce que le remplissage DÉBLOQUE (valeur, pas obligation)
- Disparaît à 100%

---

## Récapitulatif des livrables

| # | Section | Livrable | Complexité |
|---|---------|----------|-----------|
| 1 | Hero | Réécriture copy + restructuration CTAs | Faible |
| 2 | Flow pricing | Scroll naturel + modal consent + header valeur /pricing | Moyenne |
| 3 | Aperçu interactif | Nouvelle section "Comment ça marche" 3 étapes | Faible |
| 4 | Lead magnet bridge | Renforcement CTA post-simulation CERFA | Faible |
| 5 | Onboarding wow | Nouvelle étape 4 "preview valeur" + confetti | Moyenne |
| 6 | Célébrations | Composant Celebration.svelte + 3 intégrations | Moyenne |
| 7 | Quittance UX | Toast + envoi email + indicateur dans tableau | Moyenne |
| 8 | Notification prefs | Nouvelle page settings/notifications | Moyenne |
| 9 | Fiche bien guidance | FieldHint.svelte + barre complétude | Faible |

**Estimation totale** : ~1-1.5 semaine de dev

---

## Hors scope (futur)

- Générateur de quittance public (lead magnet SEO) → spec séparé
- Calculateur rentabilité public → spec séparé
- Vidéo démo 90s → production externe
- Sandbox interactive (dashboard de démo sans compte) → spec séparé
- Email nurture sequence post-capture → spec séparé
- A/B testing landing page → après premiers 1000 visiteurs
