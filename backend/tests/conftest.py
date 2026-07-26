from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
import jwt

from app.core.config import settings

# Override settings for tests
settings.cors_origins = ["http://testserver"]
settings.allowed_hosts = ["testserver", "localhost", "*.gerersci.fr"]

from app.core.rate_limit import limiter
from app.main import app

# Disable rate limiting in tests to avoid 429 errors
limiter.enabled = False

# ── Seed data (deep-copied into every fresh FakeSupabaseClient) ──────────

_INITIAL_STORE: dict[str, list[dict]] = {
    "sci": [
        {
            "id": "sci-1",
            "nom": "SCI Mosa Belleville",
            "siren": "123456789",
            "regime_fiscal": "IR",
            "adresse_siege": "12 rue de Belleville, 75020 Paris",
            "capital_social": 10000,
            "nom_gerant": "Test User",
        },
        {
            "id": "sci-2",
            "nom": "SCI Horizon Lyon",
            "siren": "987654321",
            "regime_fiscal": "IS",
            "adresse_siege": None,
            "capital_social": None,
            "nom_gerant": None,
        },
    ],
    "biens": [
        {
            "id": "bien-1",
            "id_sci": "sci-1",
            "adresse": "1 rue de la Paix",
            "ville": "Paris",
            "code_postal": "75001",
            "type_bien": "appartement",
            "surface_m2": 50,
            "nb_pieces": 2,
            "loyer_cc": 1200,
            "statut": "loue",
            "tmi": 30,
            "is_demo": False,
        },
        {
            "id": "bien-9",
            "id_sci": "sci-2",
            "adresse": "42 avenue QA",
            "ville": "Lyon",
            "code_postal": "69001",
            "type_bien": "appartement",
            "surface_m2": 35,
            "nb_pieces": 1,
            "loyer_cc": 980,
            "statut": "loue",
            "tmi": 30,
            "is_demo": False,
        },
        {
            "id": "bien-free",
            "id_sci": "sci-1",
            "adresse": "5 rue Gratuite",
            "ville": "Lyon",
            "code_postal": "69002",
            "type_bien": "studio",
            "surface_m2": 20,
            "nb_pieces": 1,
            "loyer_cc": 800,
            "statut": "loue",
            "tmi": 30,
            "is_demo": False,
        },
    ],
    "loyers": [
        {
            "id": "loyer-1",
            "id_bien": "bien-1",
            "date_loyer": "2026-03-01",
            "montant": 1200.0,
            "statut": "paye",
        },
        {
            "id": "loyer-2",
            "id_bien": "bien-9",
            "date_loyer": "2026-04-01",
            "montant": 980.0,
            "statut": "paye",
        },
        {
            "id": "loyer-free",
            "id_bien": "bien-free",
            "date_loyer": "2026-01-01",
            "montant": 800.0,
            "statut": "paye",
        },
    ],
    "baux": [
        {
            "id": "bail-1",
            "id_bien": "bien-1",
            "date_debut": "2025-01-01",
            "date_fin": "2027-12-31",
            "loyer_hc": 1000.0,
            "charges_locatives": 200.0,
            "statut": "en_cours",
            "is_demo": False,
        },
        {
            "id": "bail-9",
            "id_bien": "bien-9",
            "date_debut": "2025-06-01",
            "date_fin": None,
            "loyer_hc": 800.0,
            "charges_locatives": 180.0,
            "statut": "en_cours",
            "is_demo": False,
        },
    ],
    "bail_locataires": [
        {"id": "bl-1", "id_bail": "bail-1", "id_locataire": "loc-1"},
    ],
    "locataires": [
        {
            "id": "loc-1",
            "id_bien": "bien-1",
            "nom": "Dupont",
            "prenom": "Jean",
            "email": "jean@test.fr",
            "date_debut": "2025-01-01",
            "date_fin": None,
        },
    ],
    "quittance_compteur": [],
    "charges": [],
    "fiscalite": [],
    "admins": [
        {"user_id": "user-123"},
    ],
    "subscriptions": [
        {
            "id": "sub-1",
            "user_id": "user-123",
            "status": "active",
            "plan_key": "pro",
            "is_active": True,
            "onboarding_completed": True,
        },
    ],
    "associes": [
        {
            "id": "associe-1",
            "id_sci": "sci-1",
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test.user@sci.local",
            "part": 60,
            "role": "gerant",
            "is_demo": False,
        },
        {
            "id": "associe-1b",
            "id_sci": "sci-1",
            "user_id": "user-456",
            "nom": "Camille Bernard",
            "email": "camille.bernard@sci.local",
            "part": 40,
            "role": "associe",
            "is_demo": False,
        },
        # role=associe VOLONTAIRE : user-123 est gérant de sci-1 mais simple
        # associé de sci-2. C'est le seul fixture « membre non habilité » du
        # projet — il sert de base négative aux gates de gouvernance
        # (test_scis::test_*_requires_gerant, test_associes_security).
        # Un test qui a besoin des droits de gestion sur sci-2 promeut la ligne
        # localement ; ne pas la passer à `gerant` ici, cela rendrait le défaut
        # permissif et désactiverait silencieusement ces tests négatifs.
        {
            "id": "associe-2",
            "id_sci": "sci-2",
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test.user@sci.local",
            "part": 100,
            "role": "associe",
            "is_demo": False,
        },
    ],
    "deficit_reportable": [],
    "assurances_pno": [
        {
            "id": "pno-1",
            "id_bien": "bien-1",
            "compagnie": "MAIF",
            "date_echeance": "2026-06-01",
            "montant_annuel": 280,
        },
    ],
    "evenements_bien": [],
    "calendrier_fiscal": [],
    "assemblees_generales": [
        {
            "id": "ag-1",
            "id_sci": "sci-1",
            "date_ag": "2026-06-15",
            "type_ag": "ordinaire",
            "exercice_annee": 2025,
            "quorum_atteint": False,
        },
    ],
    "notifications": [],
}


class FakeResult:
    def __init__(
        self, data: list[dict], error: str | None = None, count: int | None = None
    ):
        self.data = data
        self.error = error
        self.count = len(data) if count is None else count


class _FakeNotProxy:
    """Proxy for `.not_.is_(...)` negation filter on FakeQuery."""

    def __init__(self, query: "FakeQuery"):
        self._query = query

    def is_(self, key: str, value: str) -> "FakeQuery":
        self._query._not_is_filters.append((key, value))
        return self._query


class FakeQuery:
    def __init__(self, store: dict[str, list[dict]], table_name: str):
        self._store = store
        self._table_name = table_name
        self._filters: list[tuple[str, str]] = []
        self._in_filters: list[tuple[str, set[str]]] = []
        self._gt_filters: list[tuple[str, str]] = []
        self._gte_filters: list[tuple[str, str]] = []
        self._lte_filters: list[tuple[str, str]] = []
        self._lt_filters: list[tuple[str, str]] = []
        self._is_filters: list[tuple[str, str]] = []
        self._not_is_filters: list[tuple[str, str]] = []
        self._neq_filters: list[tuple[str, str]] = []
        self._operation = "select"
        self._payload: list[dict] = []
        self._update_payload: dict = {}
        self._order_key: str | None = None
        self._order_desc: bool = False
        self._limit: int | None = None
        self._range_start: int | None = None
        self._range_end: int | None = None
        self.not_ = _FakeNotProxy(self)

    def select(self, *_args, **_kwargs) -> "FakeQuery":
        self._operation = "select"
        return self

    def insert(self, payload: dict | list[dict]) -> "FakeQuery":
        self._operation = "insert"
        if isinstance(payload, list):
            self._payload = [deepcopy(item) for item in payload]
        else:
            self._payload = [deepcopy(payload)]
        return self

    def upsert(self, payload: dict | list[dict], **_kwargs) -> "FakeQuery":
        self._operation = "insert"
        if isinstance(payload, list):
            self._payload = [deepcopy(item) for item in payload]
        else:
            self._payload = [deepcopy(payload)]
        return self

    def update(self, payload: dict) -> "FakeQuery":
        self._operation = "update"
        self._update_payload = deepcopy(payload)
        return self

    def delete(self) -> "FakeQuery":
        self._operation = "delete"
        return self

    def eq(self, key: str, value: object) -> "FakeQuery":
        self._filters.append((key, str(value)))
        return self

    def neq(self, key: str, value: object) -> "FakeQuery":
        self._neq_filters.append((key, str(value)))
        return self

    def in_(self, key: str, values: list[object]) -> "FakeQuery":
        self._in_filters.append((key, {str(value) for value in values}))
        return self

    def gt(self, key: str, value: object) -> "FakeQuery":
        self._gt_filters.append((key, str(value)))
        return self

    def gte(self, key: str, value: object) -> "FakeQuery":
        self._gte_filters.append((key, str(value)))
        return self

    def lte(self, key: str, value: object) -> "FakeQuery":
        self._lte_filters.append((key, str(value)))
        return self

    def lt(self, key: str, value: object) -> "FakeQuery":
        self._lt_filters.append((key, str(value)))
        return self

    def is_(self, key: str, value: str) -> "FakeQuery":
        self._is_filters.append((key, value))
        return self

    def order(self, key: str, *, desc: bool = False) -> "FakeQuery":
        self._order_key = key
        self._order_desc = desc
        return self

    def range(self, start: int, end: int) -> "FakeQuery":
        self._range_start = start
        self._range_end = end
        return self

    def limit(self, count: int) -> "FakeQuery":
        self._limit = count
        return self

    def maybe_single(self) -> "FakeQuery":
        self._limit = 1
        return self

    def _matches(self, row: dict) -> bool:
        for key, value in self._filters:
            if str(row.get(key)) != value:
                return False
        for key, value in self._neq_filters:
            if str(row.get(key)) == value:
                return False
        for key, values in self._in_filters:
            if str(row.get(key)) not in values:
                return False
        for key, value in self._gt_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) <= value:
                return False
        for key, value in self._gte_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) < value:
                return False
        for key, value in self._lte_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) > value:
                return False
        for key, value in self._lt_filters:
            candidate = row.get(key)
            if candidate is None or str(candidate) >= value:
                return False
        for key, value in self._not_is_filters:
            if value == "null":
                if row.get(key) is None:
                    return False
            else:
                if row.get(key) is not None:
                    return False
        for key, value in self._is_filters:
            if value == "null":
                if row.get(key) is not None:
                    return False
            else:
                if row.get(key) is None:
                    return False
        return True

    def execute(self) -> FakeResult:
        rows = self._store.setdefault(self._table_name, [])

        if self._operation == "select":
            data = [deepcopy(row) for row in rows if self._matches(row)]
            if self._order_key:
                data.sort(
                    key=lambda r: r.get(self._order_key, ""),
                    reverse=self._order_desc,
                )
            if self._range_start is not None and self._range_end is not None:
                data = data[self._range_start : self._range_end + 1]
            if self._limit is not None:
                data = data[: self._limit]
            return FakeResult(data=data)

        if self._operation == "insert":
            inserted: list[dict] = []
            for payload in self._payload:
                payload.setdefault("id", str(uuid4()))
                rows.append(deepcopy(payload))
                inserted.append(deepcopy(payload))
            return FakeResult(data=inserted)

        if self._operation == "update":
            updated: list[dict] = []
            for row in rows:
                if self._matches(row):
                    row.update(deepcopy(self._update_payload))
                    updated.append(deepcopy(row))
            return FakeResult(data=updated)

        if self._operation == "delete":
            kept: list[dict] = []
            deleted: list[dict] = []
            for row in rows:
                if self._matches(row):
                    deleted.append(deepcopy(row))
                else:
                    kept.append(row)
            self._store[self._table_name] = kept
            return FakeResult(data=deleted)

        return FakeResult(data=[], error="unsupported operation")


class FakeAuthAdmin:
    def list_users(self, page=1, per_page=50):
        return [
            type(
                "User",
                (),
                {
                    "id": "user-123",
                    "email": "test@sci.local",
                    "created_at": "2026-01-01T00:00:00",
                },
            )()
        ]

    def get_user_by_id(self, user_id):
        return type(
            "UserResponse",
            (),
            {
                "user": type(
                    "User",
                    (),
                    {
                        "id": user_id,
                        "email": "test@sci.local",
                        "created_at": "2026-01-01T00:00:00",
                    },
                )()
            },
        )()


class FakeAuth:
    def __init__(self):
        self.admin = FakeAuthAdmin()


class _FakeBucket:
    """Minimal fake for ``client.storage.from_(<bucket>)``."""

    def __init__(self):
        self.removed: list[list[str]] = []
        self.uploaded: list[tuple[str, bytes]] = []

    def upload(self, path: str, content: bytes, **_kwargs):
        self.uploaded.append((path, content))

    def get_public_url(self, path: str) -> str:
        return f"https://storage.local/storage/v1/object/public/documents/{path}"

    def create_signed_url(self, path: str, expires_in: int = 3600) -> dict:
        return {
            "signedURL": f"https://storage.local/storage/v1/object/sign/documents/{path}?token=fake&expires_in={expires_in}"
        }

    def remove(self, paths: list[str]):
        self.removed.append(paths)


class _FakeStorageProxy:
    """Minimal fake for ``client.storage``."""

    def __init__(self):
        self._buckets: dict[str, _FakeBucket] = {}

    def from_(self, bucket_name: str) -> _FakeBucket:
        return self._buckets.setdefault(bucket_name, _FakeBucket())


class FakeRpcQuery:
    def __init__(self, store: dict[str, list[dict]], fn_name: str, params: dict):
        self.store = store
        self.fn_name = fn_name
        self.params = params

    def execute(self) -> FakeResult:
        if self.fn_name == "increment_quittance_counter":
            sci_id = self.params.get("p_sci_id")
            annee_mois = self.params.get("p_annee_mois")
            compteurs = self.store.setdefault("quittance_compteur", [])

            # Find or create counter
            counter = None
            for c in compteurs:
                if (
                    str(c.get("sci_id")) == str(sci_id)
                    and c.get("annee_mois") == annee_mois
                ):
                    counter = c
                    break

            if counter:
                counter["dernier_numero"] += 1
            else:
                counter = {
                    "sci_id": sci_id,
                    "annee_mois": annee_mois,
                    "dernier_numero": 1,
                }
                compteurs.append(counter)

            return FakeResult(data=counter["dernier_numero"])
        return FakeResult(data=None)


class FakeSupabaseClient:
    def __init__(self):
        self.auth = FakeAuth()
        self.storage = _FakeStorageProxy()
        self.store: dict[str, list[dict]] = deepcopy(_INITIAL_STORE)
        import app.core.supabase_client as s_client

        s_client._test_client = self

    def reset_store(self):
        """Reset store to initial seed data (called between tests)."""
        self.store = deepcopy(_INITIAL_STORE)
        self.storage = _FakeStorageProxy()

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self.store, name)

    def rpc(self, fn_name: str, params: dict) -> FakeRpcQuery:
        return FakeRpcQuery(self.store, fn_name, params)


# ── Session-scoped fixtures (boot app + monkeypatch once per worker) ─────


@pytest.fixture(scope="session")
def _fake_storage_session():
    class FakeStorageService:
        def __init__(self):
            self.files: dict[str, bytes] = {}

        def reset(self):
            self.files.clear()

        async def create_bucket_if_not_exists(self) -> bool:
            return True

        async def upload_file(
            self,
            file_path: str,
            file_content: bytes,
            content_type: str = "application/pdf",
        ) -> str:
            self.files[file_path] = bytes(file_content)
            return f"https://storage.local/{file_path}"

        async def download_file(self, file_path: str) -> bytes:
            content = self.files.get(file_path)
            if content is None:
                raise Exception("file not found")
            return content

        async def delete_file(self, file_path: str) -> bool:
            self.files.pop(file_path, None)
            return True

        async def create_signed_url(self, file_path: str, expires_in: int = 300) -> str:
            if file_path not in self.files:
                raise Exception("file not found")
            return f"https://storage.local/signed/{file_path}?expires_in={expires_in}"

    return FakeStorageService()


@pytest.fixture(scope="session")
def _fake_supabase_session() -> FakeSupabaseClient:
    return FakeSupabaseClient()


@pytest.fixture(scope="session")
def _session_client(_fake_supabase_session, _fake_storage_session) -> TestClient:
    """Boot TestClient + monkeypatch once per xdist worker."""
    from app.api.v1 import (
        associes,
        biens,
        biens_flat,
        charges,
        export,
        fiscalite,
        locataires,
        loyers,
        notifications,
        quitus,
        scis,
        declarations,
    )
    from app.services import declaration_2065_service
    from app.api.v1 import dashboard, notification_preferences
    from app.api.v1 import (
        assemblees_generales,
        mouvements_parts,
        import_csv,
        echeances,
        sci_lifecycle,
        calendrier_fiscal,
        leads,
    )
    from app.api.v1.biens import (
        biens_core,
        biens_loyers,
        biens_baux,
        biens_charges,
        biens_pno,
        biens_frais,
        biens_documents,
        biens_evenements,
    )
    from app import main
    from app.api.v1 import (
        auth,
        files,
        gdpr,
        stripe,
        onboarding,
        finances,
        admin,
        declarations,
    )
    from app.services import subscription_service, declaration_2065_service
    from app.core import supabase_client as supabase_client_mod, paywall as paywall_mod

    fake_supabase = _fake_supabase_session
    fake_storage = _fake_storage_session

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(quitus, "storage_service", fake_storage)

        def fake_service():
            return fake_supabase

        fake_service.cache_clear = lambda: None

        for mod in [
            associes,
            biens_flat,
            charges,
            export,
            fiscalite,
            loyers,
            locataires,
            scis,
            notifications,
            dashboard,
            notification_preferences,
            quitus,
            assemblees_generales,
            mouvements_parts,
            import_csv,
            echeances,
            sci_lifecycle,
            calendrier_fiscal,
            leads,
            declarations,
            biens_core,
            biens_loyers,
            biens_baux,
            biens_charges,
            biens_pno,
            biens_frais,
            biens_documents,
            biens_evenements,
            declarations,
            declaration_2065_service,
        ]:
            mp.setattr(mod, "get_supabase_service_client", fake_service, raising=False)
            mp.setattr(
                mod,
                "get_supabase_user_client",
                lambda request=None: fake_supabase,
                raising=False,
            )

        def fake_anon():
            return fake_supabase

        fake_anon.cache_clear = lambda: None

        def fake_user_client(request=None):
            return fake_supabase

        for _mod in [
            auth,
            files,
            gdpr,
            stripe,
            subscription_service,
            onboarding,
            finances,
            declaration_2065_service,
        ]:
            mp.setattr(_mod, "get_supabase_service_client", fake_service, raising=False)
            mp.setattr(
                _mod,
                "get_supabase_user_client",
                lambda request=None: fake_supabase,
                raising=False,
            )
        mp.setattr(admin, "get_service_client", fake_service, raising=False)
        mp.setattr(supabase_client_mod, "get_supabase_service_client", fake_service)
        mp.setattr(supabase_client_mod, "get_supabase_anon_client", fake_anon)
        mp.setattr(supabase_client_mod, "get_supabase_user_client", fake_user_client)
        mp.setattr(paywall_mod, "get_supabase_service_client", fake_service)

        mp.setattr(main, "shutdown_event", __import__("asyncio").Event())

        settings.allowed_hosts = ["testserver", "localhost", "*.gerersci.fr"]

        # Pre-fill JWKS cache to prevent real network calls in CI.
        # This must happen before any request that triggers JWT verification.
        # The _jwks_cache dict is module-level in security.py; mutating it
        # in-place ensures all references see the update.
        import app.core.security as _sec_mod

        _sec_mod._jwks_cache["keys"] = []
        _sec_mod._jwks_cache["expires_at"] = 1e15  # ~year 33658, never expires

        with TestClient(app, base_url="http://testserver") as test_client:
            yield test_client


# ── Function-scoped fixtures (exposed to tests, reset store each time) ───


@pytest.fixture(autouse=True)
def _reset_store(_fake_supabase_session, _fake_storage_session):
    """Reset the in-memory store before each test for isolation."""
    _fake_supabase_session.reset_store()
    _fake_storage_session.reset()


@pytest.fixture
def client(_session_client) -> TestClient:
    return _session_client


@pytest.fixture
def fake_supabase(_fake_supabase_session) -> FakeSupabaseClient:
    return _fake_supabase_session


@pytest.fixture
def fake_storage(_fake_storage_session):
    return _fake_storage_session


@pytest.fixture
def free_plan(fake_supabase: FakeSupabaseClient):
    """Set a non-subscriber state so user-123 gets blocked (no access).

    Payment-first model: no trial, no freemium. Users without a paid
    subscription get max 0 biens/scis and all features disabled.
    """
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "free",
            "status": "no_subscription",
            "is_active": False,
            "stripe_price_id": None,
            "current_period_end": None,
            "max_scis": 0,
            "max_biens": 0,
            "features": {
                "multi_sci_enabled": False,
                "charges_enabled": False,
                "fiscalite_enabled": False,
                "quitus_enabled": False,
                "cerfa_enabled": False,
                "priority_support": False,
                "documents_enabled": False,
                "notifications_enabled": False,
                "associes_enabled": False,
                "pno_frais_enabled": False,
                "rentabilite_enabled": False,
                "dashboard_complet": False,
                "multi_user": False,
                "api_access": False,
            },
        }
    ]


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "user-123", "role": "authenticated", "aud": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
