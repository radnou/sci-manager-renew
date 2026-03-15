# Admin Dashboard v2 — Design Spec

**Date**: 2026-03-15
**Status**: Draft
**Author**: Business Panel (Drucker, Christensen, Godin, Meadows) + Fondateur

## Context

GérerSCI admin dashboard redesign. Current state: 4 static KPIs (total_users, total_scis, total_biens, active_subscriptions) + paginated user list. No business metrics, no funnel, no actionable alerts.

**User**: Solo founder, new to SaaS metrics. Needs a cockpit that educates while it reports.

**North Star Metric**: Active SCIs with ≥1 rent recorded in 30 days.

## Decisions

- Solo founder cockpit — no moderation tools, no team features
- 4 sections: Hero KPIs, Business Alerts, Activation Funnel, Enriched Users
- Educational UX: short subtitle + detailed tooltip on every KPI
- Follow existing design system (sci-page-shell, KPI cards, dark mode, lucide icons)
- YAGNI: no cohorts, no real-time, no moderation/ban, no admin export

## Architecture

### Backend — New Endpoints

All endpoints require `get_current_admin` dependency. All use `get_supabase_service_client()` (bypass RLS).

#### `GET /api/v1/admin/metrics`

Returns hero KPIs with trend comparison (current vs previous period).

```json
{
  "north_star": {
    "value": 23,
    "previous": 19,
    "trend": "up"
  },
  "mrr": {
    "value": 1470.0,
    "previous": 1260.0,
    "trend": "up"
  },
  "activation_rate": {
    "value": 29.1,
    "previous": 25.0,
    "trend": "up"
  },
  "churn_30d": {
    "value": 3.2,
    "previous": 4.1,
    "trend": "down"
  },
  "conversion_rate": {
    "value": 8.4,
    "previous": 7.1,
    "trend": "up"
  }
}
```

**Calculation logic**:

| KPI | Current period | Previous period | Formula |
|-----|---------------|-----------------|---------|
| North Star | SCIs with ≥1 loyer (statut=paye) where date_loyer > now()-30d | Same for days -60 to -30 | COUNT DISTINCT id_sci via biens → loyers join (column is `id_sci`, not `sci_id`) |
| MRR (estimated) | SUM of plan monthly prices for active subscriptions | Same calculation 30d ago (snapshot approximation) | Map plan_key → monthly price. Annual subscribers normalized: annual_price / 12 |
| Activation rate | Users with ≥1 loyer / total users × 100 | Same 30d ago | associes (distinct user_id) + loyers join |
| Churn 30d | Users active M-1 but not active M / active M-1 × 100 | M-2 vs M-1 | Active = ≥1 loyer in period. Guard: if active M-1 == 0, churn = 0 |
| Conversion | Paid users / total users × 100 | Same 30d ago | subscriptions (status in active,trialing,paid) / total. Guard: if total == 0, rate = 0 |

**Price map for MRR** (from entitlements, monthly equivalent):
- free: 0 EUR
- starter: 9.90 EUR/month (annual: Stripe price / 12)
- pro: 19.90 EUR/month (annual: Stripe price / 12)
- lifetime: 0 EUR/month (one-time, excluded from MRR)
- cabinet: 49.90 EUR/month (annual: Stripe price / 12)

> **Note**: MRR is labeled "estimated" because annual subscription prices are not stored in entitlements — they must be hardcoded or fetched from Stripe. At early stage this approximation is acceptable.

#### `GET /api/v1/admin/alerts`

Returns business alerts based on threshold analysis.

```json
{
  "alerts": [
    {
      "type": "mrr_declining",
      "severity": "high",
      "message": "MRR en baisse depuis 2 semaines consécutives",
      "detail": "1470 EUR → 1380 EUR → 1290 EUR",
      "tooltip": "Vérifie si des utilisateurs ont downgrade ou churné récemment."
    }
  ]
}
```

**Alert rules**:

| Alert | Condition | Severity |
|-------|-----------|----------|
| `mrr_declining` | MRR decreased 2 consecutive weeks | high |
| `low_activation` | Activation rate < 30% | medium |
| `high_churn` | Churn > 5%/month | medium |
| `no_signups` | 0 new users in last 7 days | medium |


When no alert rules trigger, the backend returns `alerts: []` (empty list). The frontend handles this state.

#### `GET /api/v1/admin/funnel`

Returns activation funnel counts.

```json
{
  "steps": [
    {"label": "Inscrits", "count": 142, "rate": 100.0},
    {"label": "Onboarding complété", "count": 89, "rate": 62.7},
    {"label": "1er bien créé", "count": 67, "rate": 47.2},
    {"label": "1er loyer enregistré", "count": 41, "rate": 28.9},
    {"label": "Passé en paid", "count": 12, "rate": 8.5}
  ],
  "bottleneck_index": 2
}
```

**Step calculations**:
1. **Inscrits**: COUNT DISTINCT user_id from associes
2. **Onboarding complété**: COUNT where subscriptions.onboarding_completed = true. Note: only counts users with a subscriptions row. Users without a subscription row are excluded — this is an acceptable approximation since the onboarding wizard creates/updates the subscription row.
3. **1er bien créé**: COUNT DISTINCT user_id from associes WHERE id_sci IN (SELECT id_sci FROM biens)
4. **1er loyer enregistré**: COUNT DISTINCT user_id from associes WHERE id_sci IN (SELECT DISTINCT b.id_sci FROM loyers l JOIN biens b ON l.id_bien = b.id)
5. **Passé en paid**: COUNT where subscriptions.status IN (active, trialing, paid) AND plan_key != 'free'

**Bottleneck**: 0-based index of the step with the largest absolute drop-off percentage (rate[i] - rate[i+1]). Tie-breaking: first step wins (earlier in funnel = higher leverage).

#### `GET /api/v1/admin/users` (enhanced — replaces current)

**Data source strategy**: Fetch all auth users via `client.auth.admin.list_users()`, then enrich each user in-memory by querying `associes`, `biens`, `loyers`, and `subscriptions` tables. Filtering (`search`, `status`, `plan`) and sorting (`sort`) are applied in-memory after enrichment. Pagination is applied last on the filtered/sorted result. This approach is acceptable at early stage (<1000 users). At scale, consider a materialized view.

New query params: `?search=email&status=power_user|prospect|at_risk|new&plan=free|starter|pro|lifetime&sort=last_activity|created_at&page=1&per_page=50`

Returns enriched user objects:

```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "created_at": "2026-01-15T...",
      "plan_key": "free",
      "is_active": true,
      "sci_count": 1,
      "biens_count": 4,
      "loyers_30d": 2,
      "last_activity": "2026-03-14T...",
      "status": "prospect",
      "stripe_customer_id": "cus_..."
    }
  ],
  "total": 142,
  "page": 1,
  "per_page": 50
}
```

**Status auto-calculation**:
- `power_user`: ≥3 loyers recorded in last 30 days
- `prospect`: free plan AND biens_count ≥ 4 (at or approaching the 5-bien limit — 1 slot left or blocked)
- `at_risk`: no activity (no loyer) in last 30 days AND account age > 7 days. `last_activity` is `MAX(loyers.created_at)` for the user's SCIs → biens → loyers. If None (no loyer ever), display "Jamais" in frontend.
- `new`: account created < 7 days ago
- `active`: none of the above (normal active user)

Priority: power_user > prospect > at_risk > new > active (first match wins).

### Backend — Service Layer

#### `backend/app/services/admin_metrics_service.py` (new)

Single service file with functions:

```python
async def get_hero_metrics(client) -> dict
async def get_business_alerts(client) -> dict
async def get_activation_funnel(client) -> dict
async def get_enriched_users(client, search, status, plan, sort, page, per_page) -> dict
```

All functions use the service client (bypass RLS) since admin has global visibility.

### Backend — Schemas

#### `backend/app/schemas/admin.py` (new)

Pydantic models for type safety and documentation:

```python
class TrendDirection(str, Enum):
    up = "up"
    down = "down"
    stable = "stable"

class MetricValue(BaseModel):
    value: float
    previous: float
    trend: TrendDirection
    change_pct: float | None  # None when previous == 0 (no prior data)

class HeroMetrics(BaseModel):
    north_star: MetricValue
    mrr: MetricValue
    activation_rate: MetricValue
    churn_30d: MetricValue
    conversion_rate: MetricValue

class BusinessAlert(BaseModel):
    type: str
    severity: Literal["high", "medium", "info"]
    message: str
    detail: str
    tooltip: str

class BusinessAlerts(BaseModel):
    alerts: list[BusinessAlert]

class FunnelStep(BaseModel):
    label: str
    count: int
    rate: float

class ActivationFunnel(BaseModel):
    steps: list[FunnelStep]
    bottleneck_index: int

class UserStatus(str, Enum):
    power_user = "power_user"
    prospect = "prospect"
    at_risk = "at_risk"
    new = "new"
    active = "active"

class EnrichedUser(BaseModel):
    id: str
    email: str
    created_at: str
    plan_key: str
    is_active: bool
    sci_count: int
    biens_count: int
    loyers_30d: int
    last_activity: str | None  # MAX(loyers.created_at) for user's SCIs. None = no loyer ever. Frontend renders None as "Jamais"
    status: UserStatus
    stripe_customer_id: str | None

class EnrichedUserList(BaseModel):
    users: list[EnrichedUser]
    total: int
    page: int
    per_page: int
```

### Frontend — Page Structure

#### Admin Dashboard (`frontend/src/routes/(app)/admin/+page.svelte`)

Replace current page. Follows sci-page-shell pattern.

```
sci-page-shell
├── sci-page-header ("Admin — Cockpit Business")
├── Loading state (sci-loading spinner)
├── Error state (rose alert)
├── sci-stagger
│   ├── AdminHeroKpis (5 KPI cards, grid 2→3→5)
│   ├── AdminAlerts (business alerts, reuse DashboardAlerts pattern)
│   ├── AdminFunnel (horizontal bar chart)
│   └── (link to /admin/users for full table)
```

#### Admin Users (`frontend/src/routes/(app)/admin/users/+page.svelte`)

Enhance current page with filters and enriched data.

```
sci-page-shell
├── sci-page-header ("Utilisateurs")
├── Filters bar (search input + status dropdown + plan dropdown)
├── Table (enriched columns)
│   ├── Email
│   ├── Plan (colored badge)
│   ├── SCIs (count)
│   ├── Biens (count)
│   ├── Dernière activité (relative time)
│   └── Statut (colored badge: power_user=emerald, prospect=amber, at_risk=rose, new=sky)
├── Pagination (previous/next + page number)
```

### Frontend — Components

#### `AdminHeroKpis.svelte` (new)

5 KPI cards following DashboardKpis pattern with additions:
- **Subtitle**: `text-xs text-slate-500` below the label
- **Trend indicator**: Arrow icon (TrendingUp/TrendingDown from lucide) + colored text (emerald for positive, rose for negative)
- **Info tooltip**: `(i)` icon button, shows tooltip on hover via title attribute or custom tooltip div
- **Grid**: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-5`

Card structure:
```
┌─────────────────────────┐
│ 🎯 North Star      (i) │
│ 23                  ↑21%│
│ SCIs actives sur 30j    │
└─────────────────────────┘
```

Trend display: if `change_pct` is null (no prior data), show "—" instead of a percentage. If `change_pct` is 0, show "stable" with a grey Minus icon.

KPI config (icon, color, formatting):

| KPI | Icon | Color | Format | Positive direction |
|-----|------|-------|--------|-------------------|
| North Star | Target | indigo | integer | up |
| MRR | Euro | emerald | currency EUR | up |
| Activation | Zap | sky | percentage | up |
| Churn | UserMinus | rose | percentage | down (lower is better) |
| Conversion | ArrowUpRight | amber | percentage | up |

Tooltip content (hardcoded in component — educational, not dynamic):

| KPI | Tooltip text |
|-----|-------------|
| North Star | « Combien de SCI ont enregistré ≥1 loyer payé ces 30 derniers jours. C'est ta métrique #1 — si elle monte, ton produit crée de la valeur. Si elle stagne, concentre-toi sur l'activation. » |
| MRR | « Somme des abonnements actifs ce mois (hors lifetime). C'est ce qui paie tes serveurs. Surveille la tendance : 2 semaines de baisse = signal d'alerte. » |
| Activation | « % d'utilisateurs inscrits qui ont enregistré au moins 1 loyer. En dessous de 30%, ton onboarding a un problème — simplifie le parcours. » |
| Churn | « % d'utilisateurs actifs le mois dernier qui ne le sont plus ce mois-ci. Au-dessus de 5%/mois, il y a une fuite à colmater — contacte les users perdus. » |
| Conversion | « % d'utilisateurs gratuits passés à un plan payant. Bon indicateur de la valeur perçue et du positionnement de ton paywall. » |

#### `AdminAlerts.svelte` (new)

New component visually modeled after DashboardAlerts but with its own `BusinessAlert[]` prop (different data shape — no `entity_id`, `sci_nom`, `bien_adresse`). Does NOT reuse or wrap DashboardAlerts.
- Severity mapping: high → rose, medium → amber, info → emerald
- Each alert shows `tooltip` field as a subtle italic helper below the main message
- Backend returns empty `alerts: []` when all clear. Frontend handles the empty case by showing an emerald banner "Tout va bien — aucune alerte business"

#### `AdminFunnel.svelte` (new)

Horizontal funnel bars:
- Each step: label (left) + count + percentage badge + horizontal bar
- Bar width proportional to rate (100% = full width)
- Bottleneck step highlighted: amber background + "Goulot" badge
- Colors: bars in sky-500, bottleneck bar in amber-500
- Subtitle explaining the funnel: « Parcours des utilisateurs de l'inscription au paiement »

#### `AdminUserStatusBadge.svelte` (new)

Small component for user status badges:
- power_user: emerald badge "Power user"
- prospect: amber badge "Prospect chaud"
- at_risk: rose badge "À risque"
- new: sky badge "Nouveau"
- active: slate badge "Actif"

### Frontend — API Client

Add to `frontend/src/lib/api.ts`:

```typescript
// Admin metrics
export async function fetchAdminMetrics(): Promise<HeroMetrics>
export async function fetchAdminAlerts(): Promise<BusinessAlerts>
export async function fetchAdminFunnel(): Promise<ActivationFunnel>
export async function fetchAdminUsers(params: {
  search?: string;
  status?: string;
  plan?: string;
  sort?: string;
  page?: number;
  per_page?: number;
}): Promise<EnrichedUserList>
```

These replace the current `fetchAdminStats` and `fetchAdminUsers` calls.

### Database Changes

**None required.** All metrics are computed from existing tables (loyers, biens, associes, subscriptions, sci). No new tables or migrations needed.

### Tooltip Implementation

Use a lightweight custom approach (no library dependency):

```svelte
<!-- Tooltip pattern -->
<button class="group relative ml-1 inline-flex">
  <Info class="h-3.5 w-3.5 text-slate-400" />
  <div class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2
              rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-600
              opacity-0 shadow-lg transition-opacity group-hover:opacity-100
              dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
    {tooltipText}
  </div>
</button>
```

Pure CSS tooltip via group-hover — no JS, no library, works with dark mode.

## File Changes Summary

### New files
| File | Purpose |
|------|---------|
| `backend/app/schemas/admin.py` | Pydantic schemas for admin endpoints |
| `backend/app/services/admin_metrics_service.py` | Business metrics calculation logic |
| `frontend/src/lib/components/admin/AdminHeroKpis.svelte` | 5 KPI cards with tooltips |
| `frontend/src/lib/components/admin/AdminAlerts.svelte` | Business alerts section |
| `frontend/src/lib/components/admin/AdminFunnel.svelte` | Activation funnel bars |
| `frontend/src/lib/components/admin/AdminUserStatusBadge.svelte` | User status badge |

### Modified files
| File | Changes |
|------|---------|
| `backend/app/api/v1/admin.py` | Replace endpoints: metrics, alerts, funnel, enhanced users |
| `frontend/src/routes/(app)/admin/+page.svelte` | Rewrite with 3 sections (KPIs, alerts, funnel) |
| `frontend/src/routes/(app)/admin/users/+page.svelte` | Add filters, enriched columns, status badges |
| `frontend/src/routes/(app)/admin/+layout.svelte` | Update auth check to use `/admin/metrics` instead of `/admin/stats` (which is removed). Update nav labels. |
| `frontend/src/lib/api.ts` | Add 4 admin API functions, remove old ones |

### Unchanged
- Database schema (no migrations)
- Security (get_current_admin stays as-is)
- Other frontend/backend files

## Testing Strategy

### Backend
- Unit tests for each calculation in admin_metrics_service.py
- Test edge cases: 0 users, 0 loyers, division by zero guards
- Test alert threshold logic
- Test user status classification priority

### Frontend
- Component tests for AdminHeroKpis (renders values, tooltips, trends)
- Component tests for AdminFunnel (bottleneck highlight)
- Component tests for AdminUserStatusBadge (correct colors)
- E2E: admin login → dashboard loads → KPIs visible → navigate to users → filters work

## Out of Scope (YAGNI)

- Cohort analysis
- Real-time WebSocket updates
- User moderation (ban/suspend)
- Admin export CSV
- Multi-admin roles/permissions
- Custom alert thresholds UI
- Revenue forecasting
- Feature usage analytics (per-feature breakdown)
