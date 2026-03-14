"""Direct tests for assemblees_generales.py and mouvements_parts.py error paths."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.paywall import AssocieMembership
from tests.conftest import FakeResult


class ErrorQuery:
    def select(self, *a, **k): return self
    def eq(self, *a, **k): return self
    def in_(self, *a, **k): return self
    def insert(self, *a, **k): return self
    def update(self, *a, **k): return self
    def delete(self, *a, **k): return self
    def order(self, *a, **k): return self
    def execute(self):
        return FakeResult(data=[], error="db_error")


class ErrorClient:
    def table(self, name):
        return ErrorQuery()


class EmptyInsertClient:
    def table(self, name):
        class Q:
            def select(self, *a, **k): return self
            def eq(self, *a, **k): return self
            def insert(self, *a, **k): return self
            def execute(self): return FakeResult(data=[])
        return Q()


MEMBERSHIP = AssocieMembership(user_id="u1", sci_id="s1", role="gerant", associe_id="a1")
SCI_UUID = UUID("00000000-0000-0000-0000-000000000001")
AG_UUID = UUID("00000000-0000-0000-0000-0000000000a1")
MP_UUID = UUID("00000000-0000-0000-0000-0000000000b1")

def _mock_request():
    r = MagicMock()
    r.state = MagicMock()
    return r


# ---------------------------------------------------------------------------
# assemblees_generales error paths
# ---------------------------------------------------------------------------

class TestAGListError:
    @pytest.mark.asyncio
    async def test_list_ag_error(self):
        from app.api.v1.assemblees_generales import list_assemblees_generales
        with patch("app.api.v1.assemblees_generales._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await list_assemblees_generales(_mock_request(), SCI_UUID, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_list_ag_unexpected_exception(self):
        """Generic exception caught by the except block (line 87-89)."""
        from app.api.v1.assemblees_generales import list_assemblees_generales

        class CrashClient:
            def table(self, name):
                raise RuntimeError("unexpected crash")

        with patch("app.api.v1.assemblees_generales._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to list"):
                await list_assemblees_generales(_mock_request(), SCI_UUID, MEMBERSHIP)


class TestAGCreateError:
    @pytest.mark.asyncio
    async def test_create_ag_error(self):
        from app.api.v1.assemblees_generales import create_assemblee_generale, AGCreate
        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await create_assemblee_generale(_mock_request(), SCI_UUID, payload, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_create_ag_empty_result(self):
        from app.api.v1.assemblees_generales import create_assemblee_generale, AGCreate
        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=EmptyInsertClient()):
            with pytest.raises(DatabaseError, match="Unable to create"):
                await create_assemblee_generale(_mock_request(), SCI_UUID, payload, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_create_ag_unexpected_exception(self):
        from app.api.v1.assemblees_generales import create_assemblee_generale, AGCreate

        class CrashClient:
            def table(self, name):
                raise RuntimeError("crash")

        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to create"):
                await create_assemblee_generale(_mock_request(), SCI_UUID, payload, MEMBERSHIP)


class TestAGUpdateError:
    @pytest.mark.asyncio
    async def test_update_ag_error_on_check(self):
        from app.api.v1.assemblees_generales import update_assemblee_generale, AGCreate
        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await update_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, payload, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_update_ag_not_found(self):
        from app.api.v1.assemblees_generales import update_assemblee_generale, AGCreate

        class EmptyCheckClient:
            def table(self, name):
                class Q:
                    def select(self, *a, **k): return self
                    def eq(self, *a, **k): return self
                    def update(self, *a, **k): return self
                    def execute(self): return FakeResult(data=[])
                return Q()

        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=EmptyCheckClient()):
            with pytest.raises(ResourceNotFoundError):
                await update_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, payload, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_update_ag_update_error(self):
        """Check passes but update fails."""
        from app.api.v1.assemblees_generales import update_assemblee_generale, AGCreate

        class CheckOkUpdateErrorClient:
            def __init__(self):
                self._check_done = False

            def table(self, name):
                client_ref = self

                class Q:
                    def select(self, *a, **k): return self
                    def eq(self, *a, **k): return self
                    def update(self, *a, **k): return self
                    def execute(self_q):
                        if not client_ref._check_done:
                            client_ref._check_done = True
                            return FakeResult(data=[{"id": str(AG_UUID)}])
                        return FakeResult(data=[], error="update failed")
                return Q()

        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=CheckOkUpdateErrorClient()):
            with pytest.raises(DatabaseError):
                await update_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, payload, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_update_ag_unexpected_exception(self):
        from app.api.v1.assemblees_generales import update_assemblee_generale, AGCreate

        class CrashClient:
            def table(self, name):
                raise RuntimeError("crash")

        payload = AGCreate(date_ag="2026-01-01", type_ag="ordinaire", exercice_annee=2025)
        with patch("app.api.v1.assemblees_generales._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to update"):
                await update_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, payload, MEMBERSHIP)


class TestAGDeleteError:
    @pytest.mark.asyncio
    async def test_delete_ag_error_on_check(self):
        from app.api.v1.assemblees_generales import delete_assemblee_generale
        with patch("app.api.v1.assemblees_generales._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await delete_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_delete_ag_not_found(self):
        from app.api.v1.assemblees_generales import delete_assemblee_generale

        class EmptyClient:
            def table(self, name):
                class Q:
                    def select(self, *a, **k): return self
                    def eq(self, *a, **k): return self
                    def delete(self, *a, **k): return self
                    def execute(self): return FakeResult(data=[])
                return Q()

        with patch("app.api.v1.assemblees_generales._get_client", return_value=EmptyClient()):
            with pytest.raises(ResourceNotFoundError):
                await delete_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_delete_ag_unexpected_exception(self):
        from app.api.v1.assemblees_generales import delete_assemblee_generale

        class CrashClient:
            def table(self, name):
                raise RuntimeError("crash")

        with patch("app.api.v1.assemblees_generales._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to delete"):
                await delete_assemblee_generale(_mock_request(), SCI_UUID, AG_UUID, MEMBERSHIP)


# ---------------------------------------------------------------------------
# mouvements_parts error paths
# ---------------------------------------------------------------------------

class TestMPListError:
    @pytest.mark.asyncio
    async def test_list_mp_error(self):
        from app.api.v1.mouvements_parts import list_mouvements_parts
        with patch("app.api.v1.mouvements_parts._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await list_mouvements_parts(SCI_UUID, _mock_request(), MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_list_mp_unexpected_exception(self):
        from app.api.v1.mouvements_parts import list_mouvements_parts

        class CrashClient:
            def table(self, name):
                raise RuntimeError("crash")

        with patch("app.api.v1.mouvements_parts._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to list"):
                await list_mouvements_parts(SCI_UUID, _mock_request(), MEMBERSHIP)


class TestMPCreateError:
    @pytest.mark.asyncio
    async def test_create_mp_error(self):
        from app.api.v1.mouvements_parts import create_mouvement_parts, MouvementPartsCreate
        payload = MouvementPartsCreate(
            date_mouvement="2026-01-01", type_mouvement="cession",
            cedant_nom="A", cessionnaire_nom="B", nb_parts=10,
            prix_unitaire=100, prix_total=1000,
        )
        with patch("app.api.v1.mouvements_parts._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await create_mouvement_parts(SCI_UUID, payload, _mock_request(), MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_create_mp_empty_result(self):
        from app.api.v1.mouvements_parts import create_mouvement_parts, MouvementPartsCreate
        payload = MouvementPartsCreate(
            date_mouvement="2026-01-01", type_mouvement="cession",
            cedant_nom="A", cessionnaire_nom="B", nb_parts=10,
            prix_unitaire=100, prix_total=1000,
        )
        with patch("app.api.v1.mouvements_parts._get_client", return_value=EmptyInsertClient()):
            with pytest.raises(DatabaseError, match="Unable to create"):
                await create_mouvement_parts(SCI_UUID, payload, _mock_request(), MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_create_mp_unexpected_exception(self):
        from app.api.v1.mouvements_parts import create_mouvement_parts, MouvementPartsCreate

        class CrashClient:
            def table(self, name):
                raise RuntimeError("crash")

        payload = MouvementPartsCreate(
            date_mouvement="2026-01-01", type_mouvement="cession",
            cedant_nom="A", cessionnaire_nom="B", nb_parts=10,
            prix_unitaire=100, prix_total=1000,
        )
        with patch("app.api.v1.mouvements_parts._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to create"):
                await create_mouvement_parts(SCI_UUID, payload, _mock_request(), MEMBERSHIP)


class TestMPDeleteError:
    @pytest.mark.asyncio
    async def test_delete_mp_error_on_check(self):
        from app.api.v1.mouvements_parts import delete_mouvement_parts
        with patch("app.api.v1.mouvements_parts._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await delete_mouvement_parts(SCI_UUID, MP_UUID, _mock_request(), MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_delete_mp_not_found(self):
        from app.api.v1.mouvements_parts import delete_mouvement_parts

        class EmptyClient:
            def table(self, name):
                class Q:
                    def select(self, *a, **k): return self
                    def eq(self, *a, **k): return self
                    def delete(self, *a, **k): return self
                    def execute(self): return FakeResult(data=[])
                return Q()

        with patch("app.api.v1.mouvements_parts._get_client", return_value=EmptyClient()):
            with pytest.raises(ResourceNotFoundError):
                await delete_mouvement_parts(SCI_UUID, MP_UUID, _mock_request(), MEMBERSHIP)

    @pytest.mark.asyncio
    async def test_delete_mp_unexpected_exception(self):
        from app.api.v1.mouvements_parts import delete_mouvement_parts

        class CrashClient:
            def table(self, name):
                raise RuntimeError("crash")

        with patch("app.api.v1.mouvements_parts._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to delete"):
                await delete_mouvement_parts(SCI_UUID, MP_UUID, _mock_request(), MEMBERSHIP)
