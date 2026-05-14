"""Direct unit tests for nested biens API error handling paths.

Tests the DatabaseError raise paths that are unreachable through HTTP integration
because FakeSupabaseClient never produces errors.

Note: The legacy scis_biens.py monolith was split into the app.api.v1.biens
package (biens_core, biens_baux, biens_loyers, biens_charges, biens_pno,
biens_frais, biens_documents, biens_evenements). Each sub-module owns its own
_get_client/_get_write_client helpers, so patches must target the sub-module.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from app.core.exceptions import DatabaseError
from app.core.paywall import AssocieMembership
from tests.conftest import FakeResult


# ---------------------------------------------------------------------------
# Error-producing helpers
# ---------------------------------------------------------------------------

class ErrorQuery:
    """Query that always returns an error."""
    def select(self, *a, **k): return self
    def eq(self, *a, **k): return self
    def in_(self, *a, **k): return self
    def insert(self, *a, **k): return self
    def update(self, *a, **k): return self
    def delete(self, *a, **k): return self
    def order(self, *a, **k): return self
    def range(self, *a, **k): return self
    def gte(self, *a, **k): return self
    def lte(self, *a, **k): return self
    def limit(self, *a, **k): return self
    def execute(self):
        return FakeResult(data=[], error="db_error")


class ErrorClient:
    def table(self, name):
        return ErrorQuery()


MEMBERSHIP = AssocieMembership(user_id="u1", sci_id="s1", role="gerant", associe_id="a1")
SCI_UUID = UUID("00000000-0000-0000-0000-000000000001")
BIEN_UUID = UUID("00000000-0000-0000-0000-000000000002")


def _bien_ok_then_error():
    """Client that succeeds for biens lookup but errors on other tables."""
    class BienOkQuery:
        def select(self, *a, **k): return self
        def eq(self, *a, **k): return self
        def execute(self):
            return FakeResult(data=[{"id": "b1", "id_sci": str(SCI_UUID)}])

    class Client:
        def __init__(self):
            self._first = True

        def table(self, name):
            if name == "biens" and self._first:
                self._first = False
                return BienOkQuery()
            return ErrorQuery()

    return Client()


def _mock_request():
    r = MagicMock()
    r.state = MagicMock()
    return r


# ---------------------------------------------------------------------------
# list_sci_biens error path (biens_core)
# ---------------------------------------------------------------------------

class TestListSciBiensError:
    @pytest.mark.asyncio
    async def test_raises_database_error_on_query_error(self):
        from app.api.v1.biens.biens_core import list_sci_biens
        request = _mock_request()
        with patch("app.api.v1.biens.biens_core._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await list_sci_biens(SCI_UUID, request, MEMBERSHIP, page=1, page_size=50)


# ---------------------------------------------------------------------------
# create_sci_bien error paths (biens_core)
# ---------------------------------------------------------------------------

class TestCreateSciBienError:
    @pytest.mark.asyncio
    async def test_raises_on_insert_error(self):
        from app.api.v1.biens.biens_core import create_sci_bien
        from app.models.biens import BienCreate
        request = _mock_request()
        payload = BienCreate(
            id_sci="sci-1", adresse="Test", ville="Paris", code_postal="75001",
            type_locatif="nu", loyer_cc=500, charges=50, tmi=30,
        )
        with patch("app.api.v1.biens.biens_core._get_client", return_value=ErrorClient()), \
             patch("app.api.v1.biens.biens_core._get_write_client", return_value=ErrorClient()), \
             patch("app.api.v1.biens.biens_core.SubscriptionService.enforce_limit", return_value={}):
            with pytest.raises(DatabaseError):
                await create_sci_bien(SCI_UUID, payload, request, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_raises_on_empty_insert_result(self):
        from app.api.v1.biens.biens_core import create_sci_bien
        from app.models.biens import BienCreate

        class EmptyInsertClient:
            def table(self, name):
                class Q:
                    def select(self, *a, **k): return self
                    def eq(self, *a, **k): return self
                    def insert(self, *a, **k): return self
                    def execute(self): return FakeResult(data=[])
                return Q()

        request = _mock_request()
        payload = BienCreate(
            id_sci="sci-1", adresse="Test", ville="Paris", code_postal="75001",
            type_locatif="nu", loyer_cc=500, charges=50, tmi=30,
        )
        with patch("app.api.v1.biens.biens_core._get_client", return_value=EmptyInsertClient()), \
             patch("app.api.v1.biens.biens_core._get_write_client", return_value=EmptyInsertClient()), \
             patch("app.api.v1.biens.biens_core.SubscriptionService.enforce_limit", return_value={}):
            with pytest.raises(DatabaseError, match="Unable to create bien"):
                await create_sci_bien(SCI_UUID, payload, request, MEMBERSHIP)


# ---------------------------------------------------------------------------
# List endpoints — split across sub-modules after refactor.
# ---------------------------------------------------------------------------

_LIST_FUNCS = [
    ("app.api.v1.biens.biens_baux", "list_bien_baux"),
    ("app.api.v1.biens.biens_loyers", "list_bien_loyers"),
    ("app.api.v1.biens.biens_charges", "list_bien_charges"),
    ("app.api.v1.biens.biens_documents", "list_bien_documents"),
    ("app.api.v1.biens.biens_pno", "list_bien_assurance_pno"),
    ("app.api.v1.biens.biens_frais", "list_bien_frais_agence"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("module_path,func_name", _LIST_FUNCS, ids=[f[1] for f in _LIST_FUNCS])
async def test_list_endpoint_raises_on_db_error(module_path, func_name):
    """Each list endpoint raises DatabaseError when the DB query fails."""
    import importlib
    mod = importlib.import_module(module_path)
    func = getattr(mod, func_name)
    request = _mock_request()

    paginated_funcs = {"list_bien_loyers", "list_bien_documents"}
    kwargs = {"page": 1, "page_size": 50} if func_name in paginated_funcs else {}

    with patch(f"{module_path}._get_client", return_value=_bien_ok_then_error()):
        with pytest.raises(DatabaseError):
            await func(SCI_UUID, BIEN_UUID, request, MEMBERSHIP, **kwargs)


# ---------------------------------------------------------------------------
# Create endpoints — bail, loyer, charge live in their respective sub-modules.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_bail_error():
    from app.api.v1.biens.biens_baux import create_bien_bail
    from app.schemas.baux import BailCreate
    request = _mock_request()
    payload = BailCreate(date_debut="2026-01-01", loyer_hc=800, charges_provisions=100, type_bail="nu")
    with patch("app.api.v1.biens.biens_baux._get_client", return_value=_bien_ok_then_error()), \
         patch("app.api.v1.biens.biens_baux._get_write_client", return_value=ErrorClient()), \
         patch("app.api.v1.biens.biens_baux.SubscriptionService.enforce_limit", return_value={}):
        with pytest.raises(DatabaseError):
            await create_bien_bail(SCI_UUID, str(BIEN_UUID), payload, request, MEMBERSHIP)


@pytest.mark.asyncio
async def test_create_loyer_error():
    from app.api.v1.biens.biens_loyers import create_bien_loyer
    from app.models.loyers import LoyerCreate
    request = _mock_request()
    payload = LoyerCreate(id_bien="b1", id_sci="s1", date_loyer="2026-01-01", montant=800, statut="en_attente")
    with patch("app.api.v1.biens.biens_loyers._get_client", return_value=_bien_ok_then_error()), \
         patch("app.api.v1.biens.biens_loyers._get_write_client", return_value=ErrorClient()), \
         patch("app.api.v1.biens.biens_loyers.SubscriptionService.enforce_limit", return_value={}):
        with pytest.raises(DatabaseError):
            await create_bien_loyer(SCI_UUID, str(BIEN_UUID), payload, request, MEMBERSHIP)


@pytest.mark.asyncio
async def test_create_charge_error():
    from app.api.v1.biens.biens_charges import create_bien_charge
    from app.models.charges import ChargeCreate
    request = _mock_request()
    payload = ChargeCreate(id_bien="b1", type_charge="copropriete", montant=200, date_paiement="2026-01-01")
    with patch("app.api.v1.biens.biens_charges._get_client", return_value=_bien_ok_then_error()), \
         patch("app.api.v1.biens.biens_charges._get_write_client", return_value=ErrorClient()):
        with pytest.raises(DatabaseError):
            await create_bien_charge(SCI_UUID, BIEN_UUID, payload, request, MEMBERSHIP)
