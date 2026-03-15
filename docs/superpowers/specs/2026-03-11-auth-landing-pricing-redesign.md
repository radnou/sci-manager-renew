# Design Spec: Auth Flow + Landing Page + Pricing Restructure + SEO

**Date**: 2026-03-11
**Status**: Draft
**Scope**: Authentication, registration, landing page, pricing, email templates, SEO technique

---

## 1. Executive Summary

Refonte complète du parcours utilisateur : discovery → paiement → compte → onboarding. Le flow actuel (magic link uniquement, pricing séparé, pas de mot de passe, pas de free tier) est remplacé par un flow pay-first optimisé pour la conversion, validé par 3 panels d'experts (UX/CRO, solopreneurs, Big4).

**Changements majeurs** :
- Auth : pay-first via Stripe → auto-create account → set password dans onboarding
- Login : email/mdp (principal) + magic link (fallback)
- Landing : one-page avec pricing intégré, copy pain-driven, SEO
- Pricing : Free (Essentiel) + Gestion €19/mo + Fiscal €39/mo (kill Lifetime)
- Emails : 5 templates brandés Resend (remplace inline Jinja2)
- SEO : robots.txt, sitemap, Schema.org, OG tags, prerendering

---

## 2. Phasing Strategy

Le déploiement suit 4 phases alignées avec le conseil des experts solopreneurs :

| Phase | Quand | Focus |
|-------|-------|-------|
| **Phase 0** | Immédiat | Kill Lifetime + billing annuel + fix bugs core |
| **Phase 1** | Mois 1-2 | Fix 14 features partielles + content SEO |
| **Phase 2** | Mois 3-4 | Auth flow + landing + pricing + SEO technique |
| **Phase 3** | Mois 5-8 | CERFA 2072, simulateur fiscal, comptable collab |

**Ce spec couvre Phase 0 + Phase 2.** Phase 1 (fixes features) et Phase 3 (nouvelles features) feront l'objet de specs séparés.

---

## 3. Authentication Flow

### 3.1 Inscription (nouveau user) — Pay-First

```
/pricing (ou landing /#pricing)
  → User clique "Commencer" sur un plan payant
  → Stripe Checkout (page hébergée : email + paiement)
  → Stripe webhook checkout.session.completed
    → Backend auto-crée le compte Supabase Auth
    → Backend crée la subscription
    → Stripe redirige vers /welcome?session_id=XXX
  → /welcome : auto-login via token + formulaire "Créer votre mot de passe"
  → Redirect /onboarding (wizard existant)
```

**Pour le tier gratuit :**
```
/pricing → "Commencer gratuitement"
  → /register (formulaire email + mot de passe)
  → Supabase auth.signUp({email, password})
  → Email de bienvenue (Resend)
  → Auto-login → /onboarding
```

### 3.2 Connexion (user existant)

```
/login
  ├── Email + mot de passe (principal)
  │   → supabase.auth.signInWithPassword({email, password})
  │   → /dashboard
  │
  ├── "Connexion sans mot de passe" (fallback)
  │   → supabase.auth.signInWithOtp({email})
  │   → Email magic link (Resend template)
  │   → /auth/callback → /dashboard
  │
  └── "Mot de passe oublié ?"
      → /forgot-password
```

### 3.3 Mot de passe oublié

```
/forgot-password
  → Saisie email
  → supabase.auth.resetPasswordForEmail(email, {redirectTo: /reset-password})
  → Email reset (Resend template)
  → /reset-password (token dans URL)
  → Nouveau mot de passe + confirmation
  → supabase.auth.updateUser({password})
  → Redirect /login + toast "Mot de passe modifié"
```

### 3.4 Backend — Nouvel endpoint /activate

```python
# GET /api/v1/auth/activate?session_id=XXX
# Rate limit: 5/minute
# Auth: aucune (endpoint public, post-paiement)
#
# Sécurité anti-replay:
# - Chaque session_id ne peut être activé qu'UNE SEULE FOIS
# - On stocke les session_id activés dans une table `activated_sessions`
#   (colonnes: session_id PK, user_id, activated_at)
# - Si session_id déjà activé → 409 Conflict + redirect /login
# - Les entrées sont purgées après 24h (cron)
#
# Flow:
# 1. Valide session_id auprès de Stripe (stripe.checkout.Session.retrieve)
# 2. Vérifie session.payment_status == "paid"
# 3. Extrait email depuis session.customer_details.email + plan_key depuis metadata
# 4. Vérifie que le user Supabase existe (créé par webhook)
#    → Si webhook delayed: retry 3x avec 2s intervalle, sinon 503
# 5. Anti-replay ATOMIQUE via INSERT ... ON CONFLICT:
#    result = INSERT INTO activated_sessions (session_id, user_id)
#            VALUES ($1, $2)
#            ON CONFLICT (session_id) DO NOTHING
#    Si result.rowcount == 0 → session_id déjà activé → retourner 409 Conflict
#    (Pas de SELECT + INSERT séparé : évite la race condition double-tap)
# 6. Génère un magic link via supabase.auth.admin.generate_link(
#      type="magiclink", email=email, options={"redirect_to": "/onboarding"}
#    )
#    → Retourne un objet contenant { properties.hashed_token, properties.action_link }
#    → On extrait le token_hash et le type depuis l'action_link
# 7. Insère session_id dans activated_sessions
# 8. Retourne { token_hash, type: "magiclink", plan_key }
#    → Le frontend /welcome appelle supabase.auth.verifyOtp({
#        token_hash, type: "magiclink"
#      }) pour obtenir la session (access_token + refresh_token)
#    → Ensuite le user crée son mot de passe via supabase.auth.updateUser({password})
```

### 3.5 Backend — Nouvel endpoint POST /create-guest-checkout

L'endpoint existant `POST /stripe/create-checkout-session` exige `get_current_user` (JWT). Pour le flow pay-first, un nouvel endpoint **public** est nécessaire :

```python
# POST /api/v1/stripe/create-guest-checkout
# Auth: aucune (endpoint public)
# Rate limit: 5/minute par IP
# Body: { plan_key: "starter"|"pro", billing_period: "month"|"year" }
#
# Validation:
# - Rejeter avec 400 si plan_key == "free" ou plan_key ∉ ["starter", "pro"]
# - Rejeter avec 400 si billing_period ∉ ["month", "year"]
#
# Différences avec create-checkout-session existant:
# - Pas de Depends(get_current_user)
# - Pas de client_reference_id (user n'existe pas encore)
# - Stripe collecte l'email via checkout page
# - metadata: { plan_key, billing_period } (pas de user_id)
# - success_url: /welcome?session_id={CHECKOUT_SESSION_ID}
# - cancel_url: /#pricing
#
# L'endpoint existant create-checkout-session est CONSERVÉ pour les upgrades
# de plan (user déjà connecté qui change de plan).
```

### 3.6 Backend — Webhook modifié

Ajouter dans le handler `checkout.session.completed` :

```python
# ORDRE CRITIQUE: création user AVANT upsert subscription (car subscription a besoin de user_id)
#
# ⚠️ IMPORTANT: _sync_subscription() existant fait un early-return si client_reference_id
# est absent. Pour les guest-checkout sessions, client_reference_id est None.
# → Le webhook doit passer le user_id directement à _sync_subscription (nouveau paramètre)
#   OU utiliser un code path séparé pour le guest flow.
#
# Flow guest-checkout:
# 1. Détecter si c'est un guest-checkout: client_reference_id est None
# 2. Extraire email depuis session.customer_details.email
# 3. Vérifier si user Supabase existe déjà (supabase.auth.admin.list_users())
# 4. Si non : user = supabase.auth.admin.create_user({
#      email: email,
#      password: generate_random_password(32),
#      email_confirm: True
#    })
# 5. Extraire user_id du user créé/existant
# 6. Upsert subscription en passant user_id directement (bypass client_reference_id guard)
# 7. Écrire user_id dans la metadata de la Stripe Subscription pour les futurs webhooks:
#    try:
#        stripe.Subscription.modify(sub_id, metadata={"user_id": str(user_id), "plan_key": plan_key})
#    except stripe.error.StripeError:
#        logger.error("stripe_subscription_metadata_update_failed", sub_id=sub_id, user_id=user_id)
#        # Ne pas bloquer le flow — le user est créé, la subscription est en DB
#        # Fallback: _sync_subscription doit aussi pouvoir résoudre user_id
#        # via stripe_customer_id → subscriptions table lookup (voir 7b)
#
# 7b. FALLBACK dans _sync_subscription pour customer.subscription.updated:
#     Si metadata.user_id est absent, résoudre via:
#     stripe_customer_id = event.data.object.customer
#     → SELECT user_id FROM subscriptions WHERE stripe_customer_id = $1
#     Ceci couvre le cas où Subscription.modify a échoué au step 7
#
# 8. Envoyer email bienvenue async (Resend)
#
# Flow authentifié (upgrade, existant):
# → client_reference_id est présent → flow existant _sync_subscription() inchangé
```

### 3.8 Edge Cases

| Cas | Handling |
|-----|---------|
| User existe déjà (re-souscription) | Skip create_user, update subscription seulement |
| Webhook delayed (user sur /welcome mais compte pas créé) | Polling côté frontend (3 tentatives, 2s intervalle) + fallback message |
| User ferme browser avant redirect | Email bienvenue contient magic link d'accès |
| Stripe session expired | /welcome affiche erreur + lien vers /login + lien vers /#pricing |
| Activate replay attack | session_id déjà utilisé → 409 Conflict + redirect /login |
| Double-click sur checkout | Stripe gère l'idempotence nativement |

---

## 4. Frontend Pages — Modifications

### 4.1 Pages modifiées

| Page | Action |
|------|--------|
| `routes/+page.svelte` | Réécriture complète (landing one-page + pricing intégré) |
| `routes/login/+page.svelte` | Redesign : email/mdp + magic link fallback |
| `routes/+layout.svelte` | Nav simplifiée guests : Logo + Tarifs + Connexion |
| `routes/(app)/account/+page.svelte` | Enrichir : section sécurité (changer mdp) |

### 4.2 Nouvelles pages

| Page | Rôle |
|------|------|
| `routes/register/+page.svelte` | Formulaire inscription (free tier uniquement) |
| `routes/welcome/+page.svelte` | Auto-login post-paiement + création mdp |
| `routes/forgot-password/+page.svelte` | Saisie email pour reset |
| `routes/reset-password/+page.svelte` | Formulaire nouveau mdp |

### 4.3 Pages supprimées

| Page | Raison |
|------|--------|
| `routes/pricing/+page.svelte` | Fusionné dans landing (section #pricing) |

### 4.4 Login Page Layout

```
┌─────────────────────────────────────────┐
│  Connexion à GererSCI                   │
│                                         │
│  [Email]                                │
│  [Mot de passe]                         │
│                                         │
│  [Se connecter]        Mdp oublié ?     │
│                                         │
│  ─── ou ───                             │
│  [Recevoir un lien de connexion]        │
│                                         │
│  Pas encore de compte ?                 │
│  Voir les tarifs →                      │
└─────────────────────────────────────────┘
```

### 4.5 Welcome Page Layout

```
┌─────────────────────────────────────────┐
│  ✓ Paiement confirmé — Plan {plan}      │
│                                         │
│  Créez votre mot de passe               │
│  [Mot de passe]                         │
│  [Confirmer]                            │
│  Règles: 8+ chars, 1 maj, 1 chiffre    │
│                                         │
│  [Continuer →]                          │
└─────────────────────────────────────────┘
```

**États d'erreur de `/welcome`** :

| État | Comportement frontend |
|------|----------------------|
| `/activate` retourne 409 (replay) | Afficher : "Ce lien a déjà été utilisé." + bouton "Accéder à mon compte" → `/login` |
| `/activate` retourne 503 (webhook delayed) | Afficher : "Votre compte est en cours de création..." + auto-retry 3x (2s) + fallback "Vérifiez votre email" |
| `/activate` retourne 400/404 (session invalide) | Afficher : "Lien invalide ou expiré." + bouton "Voir les tarifs" → `/#pricing` |
| User déjà authentifié (session Supabase active) | **Redirect immédiat vers `/dashboard`** — ne pas appeler `/activate`, ne pas afficher le formulaire mdp |
| Pas de `session_id` en query param | Redirect vers `/#pricing` |

### 4.6 Account Page — Section Sécurité (ajout)

```
Section "Sécurité"
├── Changer mot de passe
│   ├── [Mot de passe actuel]
│   ├── [Nouveau mot de passe]
│   ├── [Confirmer]
│   └── [Enregistrer]
│       → supabase.auth.updateUser({password})
└── (Future: sessions actives, 2FA)
```

---

## 5. Landing Page Refonte

### 5.1 Structure des sections

```
1. HERO (above fold)
   ├── H1: "Votre SCI mérite mieux qu'un tableur Excel"
   ├── Sous-titre: bénéfice concret orienté résultat
   ├── Screenshot produit (dashboard réel)
   ├── CTA: "Démarrer à 19€/mois" (prix dans le bouton)
   ├── CTA secondaire: "Essayer gratuitement"
   └── Trust bar: "X SCI gérées · Hébergé en UE · RGPD"

2. PROBLÈME (avant/après)
   ├── 3 colonnes : douleur → solution → résultat
   └── Ancrage émotionnel sur les pain points

3. DÉMO PRODUIT
   ├── Vidéo 90s OU GIFs animés du produit réel
   └── CTA secondaire

4. FONCTIONNALITÉS (4 max, orientées résultat)
   ├── "Quittances en 2 clics"
   ├── "CERFA 2044 pré-rempli"
   ├── "Retards visibles en temps réel"
   └── "Multi-SCI en un clic"

5. AUDIENCES (3 onglets/cards)
   ├── Gérant SCI indépendant
   ├── Cabinet comptable
   └── Opérateur patrimonial

6. PRICING (section #pricing, ancre depuis CTA hero)
   ├── 3 tiers : Essentiel (gratuit) · Gestion (€19) · Fiscal (€39)
   ├── Toggle mensuel/annuel
   ├── TVA HT/TTC affichée
   ├── Feature comparison (checkmarks)
   ├── "Sans engagement · Satisfait ou remboursé 30j"
   └── CTA par plan

7. TÉMOIGNAGES (2-3 concrets)

8. FAQ (Schema.org FAQPage)
   └── Format objection → réponse

9. CTA FINAL (repeat hero)
   └── Micro-copy: "Sans engagement. Annulez quand vous voulez."
```

### 5.2 Principes de copy (Wiebe/Laja)

- **Pain-driven** : mener avec le problème, pas le produit
- **Prix dans le CTA** : "Démarrer à 19€/mois" réduit la friction
- **Spécificité SCI** : vocabulaire métier (quittance, CERFA, loyer, bail)
- **Attention ratio 1:1** : une page, un objectif, un CTA répété
- **Nav minimale** pour guests : Logo + ancre #pricing + Connexion

### 5.3 Responsive & Mobile

- Sticky CTA bar en bas sur mobile
- FAQ en accordéon
- Screenshots produit lisibles (focus sur une vue, pas le dashboard complet)
- Cards pricing en stack vertical

---

## 6. Pricing Restructure

### 6.1 Nouvelle grille tarifaire

| | Essentiel | Gestion | Fiscal |
|---|-----------|---------|--------|
| **Prix mensuel** | Gratuit | €19/mo | €39/mo |
| **Prix annuel** | — | €15/mo (€180/an) | €29/mo (€348/an) |
| **SCI** | 1 | 3 | Illimité |
| **Biens** | 2 | 10 | Illimité |
| **Suivi loyers** | ✅ | ✅ | ✅ |
| **Quittance PDF** | ✅ (brandée) | ✅ | ✅ |
| **Dashboard** | Basique | Complet + KPIs | Complet + KPIs |
| **Charges** | ❌ | ✅ | ✅ |
| **Documents GED** | ❌ | ✅ | ✅ |
| **Notifications** | ❌ | ✅ | ✅ |
| **CERFA 2044** | ❌ | ❌ | ✅ |
| **Fiscalité** | ❌ | ❌ | ✅ |
| **Associés + parts** | ❌ | ❌ | ✅ |
| **PNO + frais agence** | ❌ | ❌ | ✅ |
| **Rentabilité** | ❌ | ❌ | ✅ |
| **Support prioritaire** | ❌ | ❌ | ✅ |

### 6.2 Changements backend (entitlements.py)

#### 6.2.1 Nouveaux champs PlanEntitlements

Ajouter les feature gates manquants au dataclass :

```python
@dataclass(frozen=True)
class PlanEntitlements:
    # ... champs existants ...
    # Nouveaux champs:
    documents_enabled: bool = False     # GED documents
    notifications_enabled: bool = False  # Alertes loyer impayé, bail expirant
    associes_enabled: bool = False       # Gestion associés + parts
    pno_frais_enabled: bool = False      # Assurance PNO + frais agence
    rentabilite_enabled: bool = False    # Calculs rentabilité brute/nette/cashflow
    dashboard_complet: bool = False      # Dashboard complet avec KPIs vs basique
```

**Note sur dashboard**: Le "Dashboard Basique vs Complet" est géré via `dashboard_complet` boolean. Le frontend affiche/masque les widgets KPIs en fonction de ce flag. Pas de distinction backend — les APIs dashboard retournent toutes les données, le gating est frontend-only.

**IMPORTANT** : Mettre à jour `features_payload()` pour inclure les 6 nouveaux champs :

```python
def features_payload(self) -> dict[str, bool]:
    return {
        "multi_sci_enabled": self.multi_sci_enabled,
        "charges_enabled": self.charges_enabled,
        "fiscalite_enabled": self.fiscalite_enabled,
        "quitus_enabled": self.quitus_enabled,
        "cerfa_enabled": self.cerfa_enabled,
        "priority_support": self.priority_support,
        # Nouveaux champs:
        "documents_enabled": self.documents_enabled,
        "notifications_enabled": self.notifications_enabled,
        "associes_enabled": self.associes_enabled,
        "pno_frais_enabled": self.pno_frais_enabled,
        "rentabilite_enabled": self.rentabilite_enabled,
        "dashboard_complet": self.dashboard_complet,
    }
```

Sans cette mise à jour, `metadata_payload()` et le frontend subscription check ne verront jamais les nouveaux gates.

#### 6.2.2 Nouveau PLAN_CATALOG

```python
PLAN_CATALOG = {
    PlanKey.FREE: PlanEntitlements(
        plan_key=PlanKey.FREE,
        display_name="Essentiel",
        billing_period="none",
        max_scis=1,
        max_biens=2,
        is_public=True,  # était False
        multi_sci_enabled=False,
        charges_enabled=False,
        fiscalite_enabled=False,
        quitus_enabled=True,  # quittance brandée
        cerfa_enabled=False,
        priority_support=False,
        checkout_mode="subscription",
        documents_enabled=False,
        notifications_enabled=False,
        dashboard_complet=False,
    ),
    PlanKey.STARTER: PlanEntitlements(
        plan_key=PlanKey.STARTER,
        display_name="Gestion",  # renommé
        billing_period="month",
        max_scis=3,   # était 1
        max_biens=10,  # était 5
        multi_sci_enabled=True,  # était False
        charges_enabled=True,
        fiscalite_enabled=False,
        quitus_enabled=True,
        cerfa_enabled=False,
        priority_support=False,
        checkout_mode="subscription",
        is_public=True,
        documents_enabled=True,
        notifications_enabled=True,
        dashboard_complet=True,
    ),
    PlanKey.PRO: PlanEntitlements(
        plan_key=PlanKey.PRO,
        display_name="Fiscal",  # renommé
        billing_period="month",
        max_scis=None,  # illimité (était 10)
        max_biens=None,  # illimité (était 20)
        multi_sci_enabled=True,
        charges_enabled=True,
        fiscalite_enabled=True,
        quitus_enabled=True,
        cerfa_enabled=True,
        priority_support=True,
        checkout_mode="subscription",
        is_public=True,
        documents_enabled=True,
        notifications_enabled=True,
        associes_enabled=True,
        pno_frais_enabled=True,
        rentabilite_enabled=True,
        dashboard_complet=True,
    ),
    # PlanKey.LIFETIME → SUPPRIMÉ (mais conservé en code pour grandfathered users)
    # Les users lifetime existants sont mappés vers PRO (Fiscal)
}
```

#### 6.2.3 Billing annuel — resolve_price_id_for_plan

La signature change pour supporter le billing annuel :

```python
def resolve_price_id_for_plan(plan_key: PlanKey | str, billing_period: str = "month") -> str | None:
    normalized = plan_key if isinstance(plan_key, PlanKey) else PlanKey(str(plan_key))
    if normalized == PlanKey.STARTER:
        if billing_period == "year":
            return settings.stripe_starter_annual_price_id
        return settings.stripe_starter_price_id
    if normalized == PlanKey.PRO:
        if billing_period == "year":
            return settings.stripe_pro_annual_price_id
        return settings.stripe_pro_price_id
    return None
```

#### 6.2.4 Mapping inverse — resolve_plan_key_from_price_id

Mettre à jour pour supporter les prix annuels :

```python
def resolve_plan_key_from_price_id(price_id: str | None) -> PlanKey | None:
    if not price_id:
        return None
    price_mapping = {
        settings.stripe_starter_price_id: PlanKey.STARTER,
        settings.stripe_starter_annual_price_id: PlanKey.STARTER,
        settings.stripe_pro_price_id: PlanKey.PRO,
        settings.stripe_pro_annual_price_id: PlanKey.PRO,
    }
    return price_mapping.get(price_id)
```

#### 6.2.5 Mapping lifetime → pro (grandfathered users)

Modifier `get_plan()` pour éviter un `KeyError` quand un user lifetime existant déclenche un check :

```python
def get_plan(plan_key: PlanKey | str) -> PlanEntitlements:
    normalized = plan_key if isinstance(plan_key, PlanKey) else PlanKey(str(plan_key))
    # Grandfathered: lifetime users mappés vers Fiscal (PRO)
    if normalized == PlanKey.LIFETIME:
        normalized = PlanKey.PRO
    return PLAN_CATALOG[normalized]
```

`PlanKey.LIFETIME` reste dans l'enum pour la désérialisation, mais n'a plus d'entrée dans `PLAN_CATALOG`.

#### 6.2.6 Stockage billing_period pour abonnés annuels

Le `billing_period` dans `PLAN_CATALOG` est fixé à `"month"` (valeur par défaut pour les entrées catalogue). Pour les abonnés annuels, le `billing_period` réel est **dérivé à runtime** depuis l'objet Stripe Subscription :

```python
# Dans subscription_service.py, lors du build_plan_snapshot:
# 1. Récupérer la subscription Stripe si active
# 2. Extraire subscription.items.data[0].price.recurring.interval → "month" ou "year"
# 3. Overrider le billing_period du PlanEntitlements dans le snapshot retourné au frontend
```

Le `metadata_payload()` inclut toujours `billing_period` du catalogue (mois), mais le frontend utilise le snapshot enrichi par `subscription_service` qui contient la vraie période. Pas de stockage additionnel en DB — Stripe est la source de vérité.

### 6.3 Stripe

- Supprimer STRIPE_LIFETIME_PRICE_ID
- Ajouter prix annuels : STRIPE_STARTER_ANNUAL_PRICE_ID, STRIPE_PRO_ANNUAL_PRICE_ID
- Modifier checkout pour supporter le toggle mensuel/annuel
- Le free tier ne passe pas par Stripe (inscription directe)
- **URLs à corriger dans stripe.py** :
  - `success_url`: `/success?session_id=` → `/welcome?session_id=` (guest-checkout) ou `/dashboard` (upgrade)
  - `cancel_url`: `/pricing` → `/#pricing`

### 6.4 TVA (obligation légale FR)

Afficher sur la page pricing :
- "19€ HT/mois (22,80€ TTC)"
- "39€ HT/mois (46,80€ TTC)"

---

## 7. Email Templates

### 7.1 Architecture

Remplacer les templates inline dans `email_service.py` par des fichiers Jinja2 :

```
backend/templates/emails/
├── base.html           # Layout commun (header, footer, styles)
├── welcome.html        # Bienvenue post-paiement
├── magic_link.html     # Lien de connexion
├── reset_password.html # Réinitialisation mdp
├── quittance.html      # Quittance générée
└── subscription.html   # Confirmation abonnement
```

### 7.2 Design commun

```html
┌─────────────────────────────────────────┐
│  [Logo GererSCI]                        │
│                                         │
│  Bonjour,                               │
│  [Contenu spécifique]                   │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │    [CTA Button — bleu #2563eb]  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Si le bouton ne fonctionne pas,        │
│  copiez ce lien : {url}                 │
│                                         │
│  ─────────────────────────────────────  │
│  GererSCI · gerersci.fr                 │
│  Se désabonner · Confidentialité        │
└─────────────────────────────────────────┘
```

### 7.3 Templates spécifiques

| Template | Sujet | CTA | Envoyé quand |
|----------|-------|-----|-------------|
| welcome | "Bienvenue sur GererSCI — Plan {plan}" | "Accéder à mon espace" | Webhook checkout.session.completed |
| magic_link | "Votre lien de connexion GererSCI" | "Se connecter" | POST /auth/magic-link/send |
| reset_password | "Réinitialisez votre mot de passe" | "Réinitialiser" | POST /auth/forgot-password |
| quittance | "Quittance générée — {bien} {mois}" | "Télécharger" | POST quitus generation |
| subscription | "Abonnement {plan} activé" | "Accéder au dashboard" | Webhook (confirmation) |

### 7.4 Brancher les fonctions mortes

`email_service.py` a 4 méthodes non appelées → les brancher :
- `send_welcome()` → webhook Stripe
- `send_quitus_generated()` → endpoint quitus
- `send_subscription_confirmation()` → webhook Stripe
- Implémenter `send_notification_email()` (actuellement dead code dans notification_service.py)

---

## 8. SEO Technique

### 8.1 Fichiers à créer

| Fichier | Contenu |
|---------|---------|
| `frontend/static/robots.txt` | Allow /, Disallow app routes |
| `frontend/src/routes/sitemap.xml/+server.ts` | Sitemap dynamique |
| `frontend/src/app.html` | Ajouter `lang="fr-FR"` sur `<html>` |

### 8.2 robots.txt

```
User-agent: *
Allow: /
Disallow: /dashboard
Disallow: /scis
Disallow: /onboarding
Disallow: /admin
Disallow: /settings
Disallow: /account
Disallow: /welcome
Disallow: /register
Disallow: /forgot-password
Disallow: /reset-password
Disallow: /auth
Sitemap: https://gerersci.fr/sitemap.xml
```

### 8.3 Sitemap

Pages incluses : `/`, `/login`, `/cgu`, `/mentions-legales`, `/confidentialite`

**Note** : `/register`, `/forgot-password`, `/reset-password` sont exclus du sitemap (pages de formulaire, thin content, pas de valeur SEO). Elles sont accessibles mais non indexées.

### 8.4 Meta tags (chaque page publique)

```svelte
<svelte:head>
  <title>{title} | GererSCI</title>
  <meta name="description" content="{description}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:image" content="/og-image.png" />
  <meta property="og:type" content="website" />
  <meta property="og:locale" content="fr_FR" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="https://gerersci.fr{path}" />
</svelte:head>
```

### 8.5 Schema.org (landing page)

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "GererSCI",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "description": "Plateforme de gestion et d'intelligence fiscale pour SCI",
  "offers": [
    {"@type": "Offer", "name": "Essentiel", "price": "0", "priceCurrency": "EUR"},
    {"@type": "Offer", "name": "Gestion", "price": "19", "priceCurrency": "EUR"},
    {"@type": "Offer", "name": "Fiscal", "price": "39", "priceCurrency": "EUR"}
  ]
}
```

FAQ → `FAQPage` schema pour rich snippets Google.

### 8.6 Prerendering (pages publiques)

Ajouter dans chaque page publique :
```typescript
// +page.ts
export const prerender = true;
```

Pages : `/`, `/login`, `/cgu`, `/mentions-legales`, `/confidentialite`

**Pages NON prerendues** (dépendent de params URL ou session) : `/register`, `/forgot-password`, `/reset-password`, `/welcome`

**Note sur `/reset-password`** : Supabase envoie l'utilisateur vers `/auth/callback?type=recovery&...` qui échange le token pour une session, puis redirige vers `/reset-password`. La route existante `/auth/callback` (dans `+layout.svelte` via `onAuthStateChange`) gère déjà ce flow. La page `/reset-password` utilise `export const prerender = false` et `export const ssr = false` (car elle nécessite le client Supabase côté browser pour `updateUser`).

---

## 9. Backend Changes Summary

### 9.1 Fichiers modifiés

| Fichier | Changement |
|---------|-----------|
| `app/api/v1/auth.py` | +endpoint GET /activate (public, anti-replay), +endpoint POST /forgot-password |
| `app/api/v1/stripe.py` | +endpoint POST /create-guest-checkout (public, sans auth), webhook: auto-create user, envoyer emails |
| `app/core/entitlements.py` | Restructurer PLAN_CATALOG (free public, renommer, limites) |
| `app/core/config.py` | +`stripe_starter_annual_price_id: str = ""`, +`stripe_pro_annual_price_id: str = ""`. **Conserver** `stripe_lifetime_price_id` (ne pas supprimer) — les webhooks Stripe pour les lifetime users existants enverront encore ce price ID. Le supprimer causerait des `AttributeError`. Marquer comme deprecated avec un commentaire |
| `app/services/email_service.py` | Refactor: templates Jinja2 externes, brancher méthodes mortes |
| `app/services/subscription_service.py` | Adapter pour nouveaux plans |
| `app/services/notification_service.py` | Implémenter send_notification_email() |

### 9.2 Nouveaux fichiers

| Fichier | Rôle |
|---------|------|
| `supabase/migrations/009_auth_activated_sessions.sql` | Table anti-replay pour /activate |
| `templates/emails/base.html` | Layout email commun |
| `templates/emails/welcome.html` | Template bienvenue |
| `templates/emails/magic_link.html` | Template magic link |
| `templates/emails/reset_password.html` | Template reset mdp |
| `templates/emails/quittance.html` | Template quittance |
| `templates/emails/subscription.html` | Template confirmation abo |

### 9.3 Fichiers supprimés

Aucun fichier supprimé. Les templates inline dans `email_service.py` sont remplacés par des appels aux fichiers templates.

---

## 10. Frontend Changes Summary

### 10.1 Fichiers modifiés

| Fichier | Changement |
|---------|-----------|
| `routes/+page.svelte` | Réécriture landing (572→~400 lignes) |
| `routes/login/+page.svelte` | Email/mdp + magic link fallback |
| `routes/+layout.svelte` | Nav guests simplifiée |
| `routes/(app)/account/+page.svelte` | +section sécurité (changer mdp) |
| `routes/(app)/+layout.ts` | Adapter pour free tier (pas de redirect /pricing si free). **Changer le redirect paywall** de `'/pricing'` vers `'/#pricing'` (l'ancienne route `/pricing` sera supprimée) |
| `src/lib/api.ts` | +activateSession(), +forgotPassword() |
| `src/lib/auth/route-guard.ts` | (1) Ajouter aux routes publiques: /register, /forgot-password. (2) Ajouter /reset-password aux routes publiques (pas guest-only, car un user connecté peut aussi reset son mdp). (3) Ajouter /welcome comme route "semi-protégée" (route guard ne bloque pas, la page valide session_id). (4) **Supprimer** `/success` de `PROTECTED_ROUTE_PREFIXES` (route supprimée) |
| `src/app.html` | +lang="fr-FR" |

### 10.2 Nouveaux fichiers

| Fichier | Rôle |
|---------|------|
| `routes/register/+page.svelte` | Inscription free tier (email+mdp) |
| `routes/welcome/+page.svelte` | Auto-login + création mdp |
| `routes/welcome/+page.ts` | Load: extraire session_id |
| `routes/forgot-password/+page.svelte` | Saisie email reset |
| `routes/reset-password/+page.svelte` | Formulaire nouveau mdp |
| `static/robots.txt` | SEO |
| `routes/sitemap.xml/+server.ts` | SEO sitemap dynamique |

### 10.3 Fichiers supprimés

| Fichier | Raison |
|---------|--------|
| `routes/pricing/+page.svelte` | Remplacé par redirect 301 → `/#pricing` (via `+page.server.ts`) pour préserver les backlinks |
| `routes/pricing/+page.ts` (si existe) | Supprimé |
| `routes/success/+page.svelte` (si existe) | Supprimé — remplacé par `/welcome`. L'endpoint upgrade authentifié (`create-checkout-session`) utilise désormais aussi `success_url: /dashboard` (pas /welcome, car l'user est déjà connecté) |

---

## 11. Testing Strategy

### 11.1 Backend (maintenir ≥82% coverage)

Nouveaux tests à écrire :

| Test file | Tests |
|-----------|-------|
| `tests/test_auth.py` | test_activate_valid_session, test_activate_invalid_session, test_activate_expired, test_activate_rate_limit, test_activate_replay_attack_blocked |
| `tests/test_auth.py` | test_forgot_password_valid, test_forgot_password_unknown_email |
| `tests/test_stripe.py` | test_webhook_creates_user, test_webhook_existing_user_skips_create, test_guest_checkout_creates_session, test_guest_checkout_rejects_free_plan |
| `tests/test_entitlements.py` | test_free_plan_public, test_new_plan_limits, test_lifetime_removed |
| `tests/test_email_service.py` | test_welcome_template, test_magic_link_template, test_reset_template |

### 11.2 Frontend (maintenir ≥98% high-value coverage)

| Test file | Tests |
|-----------|-------|
| `tests/login.test.ts` | test_password_login, test_magic_link_fallback, test_forgot_link |
| `tests/register.test.ts` | test_free_registration, test_validation |
| `tests/welcome.test.ts` | test_auto_login, test_password_creation, test_invalid_session |
| `tests/pricing.test.ts` | test_plan_display, test_annual_toggle, test_checkout_redirect |

---

## 12. Migration Plan

### 12.1 Database

Nouvelle migration Supabase (`009_auth_activated_sessions.sql`) :

```sql
-- Table anti-replay pour /activate endpoint
CREATE TABLE IF NOT EXISTS activated_sessions (
    session_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour purge cron (supprimer les entrées > 24h)
CREATE INDEX idx_activated_sessions_activated_at ON activated_sessions(activated_at);

-- RLS: seul le service_role peut lire/écrire cette table
ALTER TABLE activated_sessions ENABLE ROW LEVEL SECURITY;
-- Pas de policies user — uniquement accessible via service_role

-- Les plans sont gérés dans entitlements.py (code, pas DB)
-- Les subscriptions existantes continuent de fonctionner
-- Les users Lifetime existants gardent leur accès (grandfathered)
```

### 12.2 Stripe

1. Créer 2 nouveaux prix annuels dans Stripe Dashboard
2. Archiver le prix Lifetime (ne pas supprimer — users existants)
3. Mettre à jour les env vars avec les nouveaux price IDs

### 12.3 Users existants

| Cas | Action |
|-----|--------|
| User Lifetime existant | Grandfathered — accès maintenu, plan mappé à Fiscal |
| User Starter existant | Automatiquement mappé à Gestion (même price ID) |
| User Pro existant | Automatiquement mappé à Fiscal (même price ID) |
| User sans mdp (magic link only) | Peut continuer à se connecter via magic link, encouragé à créer un mdp via /account |

---

## 13. Success Metrics

| Métrique | Avant | Cible 3 mois |
|----------|-------|-------------|
| Visitor → signup conversion | ~0% (pas mesuré) | 8-12% |
| Free → paid conversion | N/A | 15-25% |
| Login friction (étapes) | 7 (avec magic link) | 2 (email/mdp) |
| Bounce rate landing | Non mesuré | <50% |
| SEO : pages indexées | 1-2 | 8+ |
| Time to first value | >5 min (magic link attente) | <2 min |

---

## 14. Out of Scope

Explicitement exclus de ce spec (Phase 3+) :
- CERFA 2072 (SCI à l'IS)
- Simulateur fiscal (scénarios what-if)
- SCI Health Score
- Collaboration expert-comptable
- Synchronisation bancaire
- PWA mobile
- Blog/content hub
- A/B testing
- Analytics (Matomo config)
- 2FA / sessions actives
