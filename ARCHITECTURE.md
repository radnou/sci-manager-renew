# SCI-Manager Architecture (Phase 1)

## 1. Vision Globale

SCI-Manager suit une architecture web modulaire:

- Frontend `SvelteKit` (UX, SSR, dashboard, parcours utilisateur)
- Backend `FastAPI` (API metier, validation, orchestration)
- Donnees `Supabase PostgreSQL` (RLS multi-utilisateurs)
- Paiement `Stripe` (abonnements + lifetime)
- Infra `Docker Compose` (reverse proxy + services applicatifs)

## 2. Modele de Donnees Supabase

```mermaid
erDiagram
    SCI ||--o{ ASSOCIES : has
    SCI ||--o{ BIENS : owns
    BIENS ||--o{ LOCATAIRES : hosts
    BIENS ||--o{ LOYERS : bills
    BIENS ||--o{ CHARGES : incurs
    SCI ||--o{ FISCALITE : computes
    LOCATAIRES ||--o{ LOYERS : pays

    SCI {
        uuid id PK
        text nom
        text siren
        text regime_fiscal
        timestamptz created_at
        timestamptz updated_at
    }

    ASSOCIES {
        uuid id PK
        uuid id_sci FK
        uuid user_id
        text nom
        text email
        numeric part
        text role
        timestamptz created_at
        timestamptz updated_at
    }

    BIENS {
        uuid id PK
        uuid id_sci FK
        text adresse
        text ville
        text code_postal
        text type_locatif
        numeric loyer_cc
        numeric charges
        numeric tmi
        date acquisition_date
        timestamptz created_at
        timestamptz updated_at
    }

    LOCATAIRES {
        uuid id PK
        uuid id_bien FK
        text nom
        text email
        date date_debut
        date date_fin
        timestamptz created_at
        timestamptz updated_at
    }

    LOYERS {
        uuid id PK
        uuid id_bien FK
        uuid id_locataire FK
        date date_loyer
        numeric montant
        text statut
        bool quitus_genere
        timestamptz created_at
        timestamptz updated_at
    }

    CHARGES {
        uuid id PK
        uuid id_bien FK
        text type_charge
        numeric montant
        date date_paiement
        timestamptz created_at
        timestamptz updated_at
    }

    FISCALITE {
        uuid id PK
        uuid id_sci FK
        int annee
        numeric total_revenus
        numeric total_charges
        numeric resultat_fiscal
        timestamptz created_at
        timestamptz updated_at
    }
```

## 3. Auth Flow: Supabase Auth -> JWT -> RLS

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend (SvelteKit)
    participant SA as Supabase Auth
    participant BE as Backend (FastAPI)
    participant DB as Supabase PostgreSQL (RLS)

    U->>FE: Login
    FE->>SA: signIn(email, password)
    SA-->>FE: access_token (JWT)
    FE->>BE: API call + Bearer JWT
    BE->>BE: Verify JWT (claims: sub, exp)
    BE->>DB: Query with user context
    DB->>DB: Apply RLS policies
    DB-->>BE: Filtered rows only
    BE-->>FE: JSON response
```

## 4. Endpoints Backend FastAPI

- `GET /health`
- `POST /api/v1/auth/*` (placeholder integration Supabase Auth)
- `GET|POST|PUT|DELETE /api/v1/sci`
- `GET|POST|PUT|DELETE /api/v1/biens`
- `GET|POST|PUT|DELETE /api/v1/loyers`
- `POST /api/v1/quitus/generate`
- `POST /api/v1/cerfa/2044`
- `POST /api/v1/fiscalite/simulate`
- `POST /api/v1/stripe/webhook`

## 5. Pages Frontend SvelteKit

- `/` landing
- `/(auth)/login`
- `/(auth)/register`
- `/dashboard`
- `/biens`
- `/loyers`
- `/pricing`

## 6. User Flow Produit

```mermaid
flowchart LR
    A[Onboarding] --> B[Create SCI]
    B --> C[Add Bien]
    C --> D[Add Locataire]
    D --> E[Track Loyers]
    E --> F[Generate Quitus PDF]
    E --> G[Fiscal Simulation IR/IS]
    F --> H[Dashboard KPI]
    G --> H
```

## 7. Docker Runtime Architecture

```mermaid
flowchart TB
    N[Nginx Reverse Proxy] --> FE[Frontend SvelteKit]
    N --> BE[Backend FastAPI]
    BE --> DB[(Supabase PostgreSQL)]
    BE --> ST[Stripe API]
    FE --> SA[Supabase Auth]
    SA --> DB
```

## 8. Notes Phase 1

- Schema SQL initialise toutes les tables metier + indexes + triggers `updated_at`.
- RLS est activee sur toutes les tables metier et filtre selon appartenance `associes.user_id`.
- Les routers backend sont prets pour la Phase 2 (impl detaillee ensuite).
