"""Tests for dashboard_service.py — KPIs, alertes, SCI cards, activity feed."""
from __future__ import annotations

from datetime import date, timedelta
from copy import deepcopy

import pytest

from tests.conftest import FakeSupabaseClient
from app.services import dashboard_service
from app.services.dashboard_service import (
    _get_user_sci_ids,
    _query_in_sci_ids,
    get_alertes,
    get_portfolio_kpis,
    get_sci_cards,
    get_recent_activity,
)
from app.core.exceptions import DatabaseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = "user-123"
SCI_1 = "sci-1"
SCI_2 = "sci-2"


def _client_with(extra_store: dict | None = None) -> FakeSupabaseClient:
    """Return a FakeSupabaseClient populated with base associes + sci rows."""
    c = FakeSupabaseClient()
    if extra_store:
        for table, rows in extra_store.items():
            c.store[table] = rows
    return c


def _empty_client() -> FakeSupabaseClient:
    """Return a client where the user has no associes (no SCI access)."""
    c = FakeSupabaseClient()
    c.store["associes"] = []
    return c


# ---------------------------------------------------------------------------
# 1. _get_user_sci_ids
# ---------------------------------------------------------------------------

class TestGetUserSciIds:
    def test_returns_sci_ids_for_user(self):
        client = _client_with()
        ids = _get_user_sci_ids(client, USER_ID)
        assert set(ids) == {SCI_1, SCI_2}

    def test_returns_empty_for_unknown_user(self):
        client = _client_with()
        ids = _get_user_sci_ids(client, "no-such-user")
        assert ids == []

    def test_raises_on_db_error(self):
        """If the FakeResult has an error attribute set, DatabaseError is raised."""
        from tests.conftest import FakeResult

        class ErrorClient:
            def table(self, name):
                class EQ:
                    def select(self, *a, **k): return self
                    def eq(self, *a, **k): return self
                    def execute(self): return FakeResult(data=[], error="db boom")
                return EQ()

        with pytest.raises(DatabaseError):
            _get_user_sci_ids(ErrorClient(), USER_ID)


# ---------------------------------------------------------------------------
# 2. _query_in_sci_ids  (fallback path — FakeQuery has in_)
# ---------------------------------------------------------------------------

class TestQueryInSciIds:
    def test_filters_by_sci_id(self):
        client = _client_with({
            "biens": [
                {"id": "b1", "id_sci": SCI_1},
                {"id": "b2", "id_sci": "other-sci"},
            ]
        })
        rows = _query_in_sci_ids(client, "biens", "id,id_sci", [SCI_1])
        assert all(r["id_sci"] == SCI_1 for r in rows)
        assert len(rows) == 1

    def test_returns_empty_list_for_no_sci_ids(self):
        client = _client_with()
        rows = _query_in_sci_ids(client, "biens", "id", [])
        assert rows == []


# ---------------------------------------------------------------------------
# 3. get_portfolio_kpis — empty store
# ---------------------------------------------------------------------------

class TestGetPortfolioKpisEmpty:
    @pytest.mark.asyncio
    async def test_kpis_all_zero_when_no_sci(self):
        client = _empty_client()
        kpis = await get_portfolio_kpis(client, USER_ID)
        assert kpis["sci_count"] == 0
        assert kpis["biens_count"] == 0
        assert kpis["taux_recouvrement"] == 0.0
        assert kpis["cashflow_net"] == 0.0
        assert kpis["loyers_total"] == 0.0
        assert kpis["loyers_payes"] == 0.0
        assert kpis["charges_total"] == 0.0


# ---------------------------------------------------------------------------
# 4. get_portfolio_kpis — seeded data
# ---------------------------------------------------------------------------

class TestGetPortfolioKpisSeeded:
    @pytest.mark.asyncio
    async def test_sci_count_equals_number_of_scis(self):
        client = _client_with()
        kpis = await get_portfolio_kpis(client, USER_ID)
        # user-123 is in both sci-1 and sci-2
        assert kpis["sci_count"] == 2

    @pytest.mark.asyncio
    async def test_biens_count_aggregated_across_scis(self):
        client = _client_with({
            "biens": [
                {"id": "b1", "id_sci": SCI_1},
                {"id": "b2", "id_sci": SCI_1},
                {"id": "b3", "id_sci": SCI_2},
            ]
        })
        kpis = await get_portfolio_kpis(client, USER_ID)
        assert kpis["biens_count"] == 3

    @pytest.mark.asyncio
    async def test_taux_recouvrement_calculation(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 1000, "statut": "paye"},
                {"id": "l2", "id_sci": SCI_1, "montant": 1000, "statut": "en_attente"},
                {"id": "l3", "id_sci": SCI_2, "montant": 1000, "statut": "paye"},
                {"id": "l4", "id_sci": SCI_2, "montant": 1000, "statut": "en_retard"},
            ]
        })
        kpis = await get_portfolio_kpis(client, USER_ID)
        # 2 paid out of 4 → 50.0%
        assert kpis["taux_recouvrement"] == 50.0
        assert kpis["loyers_total"] == 4000.0
        assert kpis["loyers_payes"] == 2000.0

    @pytest.mark.asyncio
    async def test_cashflow_net_deducts_charges(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 1500, "statut": "paye"},
            ],
            "charges": [
                {"id": "c1", "id_sci": SCI_1, "montant": 300},
            ],
        })
        kpis = await get_portfolio_kpis(client, USER_ID)
        assert kpis["cashflow_net"] == 1200.0
        assert kpis["charges_total"] == 300.0

    @pytest.mark.asyncio
    async def test_taux_recouvrement_zero_when_no_loyers(self):
        client = _client_with()  # no loyers seeded
        kpis = await get_portfolio_kpis(client, USER_ID)
        assert kpis["taux_recouvrement"] == 0.0


# ---------------------------------------------------------------------------
# 5. get_alertes
# ---------------------------------------------------------------------------

class TestGetAlertesEmpty:
    @pytest.mark.asyncio
    async def test_no_alertes_when_no_sci(self):
        client = _empty_client()
        alertes = await get_alertes(client, USER_ID)
        assert alertes == []

    @pytest.mark.asyncio
    async def test_no_alertes_with_all_paid_loyers(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 800, "statut": "paye",
                 "date_loyer": "2024-01-01", "paiement_date": "2024-01-05"},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        assert alertes == []


class TestGetAlertesLoyers:
    @pytest.mark.asyncio
    async def test_alerte_loyer_en_retard_statut(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 900, "statut": "en_retard",
                 "date_loyer": "2024-01-01"},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        loyer_alertes = [a for a in alertes if a["type"] == "loyer_en_retard"]
        assert len(loyer_alertes) == 1
        assert loyer_alertes[0]["severity"] == "high"
        assert loyer_alertes[0]["entity_id"] == "l1"

    @pytest.mark.asyncio
    async def test_alerte_loyer_overdue_no_payment(self):
        """Loyer without payment_date and date older than 5 days triggers alert."""
        old_date = (date.today() - timedelta(days=10)).isoformat()
        client = _client_with({
            "loyers": [
                {"id": "l2", "id_sci": SCI_1, "montant": 700, "statut": "en_attente",
                 "date_loyer": old_date, "paiement_date": None},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        loyer_alertes = [a for a in alertes if a["type"] == "loyer_en_retard"]
        assert len(loyer_alertes) == 1

    @pytest.mark.asyncio
    async def test_no_alerte_for_recent_unpaid_loyer(self):
        """Loyer unpaid but only 2 days old should NOT trigger an alert."""
        recent_date = (date.today() - timedelta(days=2)).isoformat()
        client = _client_with({
            "loyers": [
                {"id": "l3", "id_sci": SCI_1, "montant": 700, "statut": "en_attente",
                 "date_loyer": recent_date, "paiement_date": None},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        loyer_alertes = [a for a in alertes if a["type"] == "loyer_en_retard"]
        assert len(loyer_alertes) == 0


class TestGetAlertesBail:
    @pytest.mark.asyncio
    async def test_alerte_bail_expire_bientot(self):
        expiry = (date.today() + timedelta(days=30)).isoformat()
        client = _client_with({
            "locataires": [
                {"id": "loc1", "id_sci": SCI_1, "statut": "en_cours",
                 "date_fin_bail": expiry},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        bail_alertes = [a for a in alertes if a["type"] == "bail_expire_bientot"]
        assert len(bail_alertes) == 1
        assert bail_alertes[0]["severity"] == "medium"
        assert bail_alertes[0]["date"] == expiry

    @pytest.mark.asyncio
    async def test_no_alerte_bail_far_future(self):
        expiry = (date.today() + timedelta(days=200)).isoformat()
        client = _client_with({
            "locataires": [
                {"id": "loc2", "id_sci": SCI_1, "statut": "en_cours",
                 "date_fin_bail": expiry},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        bail_alertes = [a for a in alertes if a["type"] == "bail_expire_bientot"]
        assert len(bail_alertes) == 0

    @pytest.mark.asyncio
    async def test_no_alerte_bail_not_en_cours(self):
        """Terminated leases should not generate alerts."""
        expiry = (date.today() + timedelta(days=10)).isoformat()
        client = _client_with({
            "locataires": [
                {"id": "loc3", "id_sci": SCI_1, "statut": "termine",
                 "date_fin_bail": expiry},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        bail_alertes = [a for a in alertes if a["type"] == "bail_expire_bientot"]
        assert len(bail_alertes) == 0

    @pytest.mark.asyncio
    async def test_alerte_uses_date_fin_fallback(self):
        """Should work whether field is named date_fin_bail or date_fin."""
        expiry = (date.today() + timedelta(days=15)).isoformat()
        client = _client_with({
            "locataires": [
                {"id": "loc4", "id_sci": SCI_1, "statut": "en_cours",
                 "date_fin": expiry},
            ]
        })
        alertes = await get_alertes(client, USER_ID)
        bail_alertes = [a for a in alertes if a["type"] == "bail_expire_bientot"]
        assert len(bail_alertes) == 1


# ---------------------------------------------------------------------------
# 6. get_sci_cards
# ---------------------------------------------------------------------------

class TestGetSciCards:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_sci(self):
        client = _empty_client()
        cards = await get_sci_cards(client, USER_ID)
        assert cards == []

    @pytest.mark.asyncio
    async def test_card_count_matches_sci_count(self):
        client = _client_with()
        cards = await get_sci_cards(client, USER_ID)
        assert len(cards) == 2

    @pytest.mark.asyncio
    async def test_card_fields_present(self):
        client = _client_with()
        cards = await get_sci_cards(client, USER_ID)
        for card in cards:
            assert "id" in card
            assert "nom" in card
            assert "biens_count" in card
            assert "loyer_total" in card
            assert "recouvrement" in card

    @pytest.mark.asyncio
    async def test_card_recouvrement_computed_correctly(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 500, "statut": "paye"},
                {"id": "l2", "id_sci": SCI_1, "montant": 500, "statut": "en_attente"},
            ]
        })
        cards = await get_sci_cards(client, USER_ID)
        card_sci1 = next(c for c in cards if c["id"] == SCI_1)
        assert card_sci1["recouvrement"] == 50.0
        assert card_sci1["loyer_total"] == 1000.0
        assert card_sci1["loyer_payes"] == 500.0

    @pytest.mark.asyncio
    async def test_card_biens_count_per_sci(self):
        client = _client_with({
            "biens": [
                {"id": "b1", "id_sci": SCI_1},
                {"id": "b2", "id_sci": SCI_1},
                {"id": "b3", "id_sci": SCI_2},
            ]
        })
        cards = await get_sci_cards(client, USER_ID)
        card_sci1 = next(c for c in cards if c["id"] == SCI_1)
        card_sci2 = next(c for c in cards if c["id"] == SCI_2)
        assert card_sci1["biens_count"] == 2
        assert card_sci2["biens_count"] == 1

    @pytest.mark.asyncio
    async def test_card_recouvrement_zero_when_no_loyers(self):
        client = _client_with()
        cards = await get_sci_cards(client, USER_ID)
        for card in cards:
            assert card["recouvrement"] == 0.0


# ---------------------------------------------------------------------------
# 7. get_recent_activity
# ---------------------------------------------------------------------------

class TestGetRecentActivity:
    @pytest.mark.asyncio
    async def test_empty_when_no_sci(self):
        client = _empty_client()
        activity = await get_recent_activity(client, USER_ID)
        assert activity == []

    @pytest.mark.asyncio
    async def test_includes_loyer_entries(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 900, "statut": "paye",
                 "date_loyer": "2024-03-01", "created_at": "2024-03-01T10:00:00"},
            ]
        })
        activity = await get_recent_activity(client, USER_ID)
        loyer_items = [a for a in activity if a["type"] == "loyer"]
        assert len(loyer_items) >= 1
        assert "900" in loyer_items[0]["description"]

    @pytest.mark.asyncio
    async def test_includes_bien_entries(self):
        client = _client_with({
            "biens": [
                {"id": "b1", "id_sci": SCI_1, "nom": "Appart Paris 11",
                 "adresse": "11 rue de la Paix", "created_at": "2024-02-01T08:00:00"},
            ]
        })
        activity = await get_recent_activity(client, USER_ID)
        bien_items = [a for a in activity if a["type"] == "bien"]
        assert len(bien_items) >= 1
        assert "11 rue de la Paix" in bien_items[0]["description"]

    @pytest.mark.asyncio
    async def test_activity_sorted_by_created_at_desc(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 100, "statut": "paye",
                 "date_loyer": "2024-01-01", "created_at": "2024-01-01T08:00:00"},
                {"id": "l2", "id_sci": SCI_1, "montant": 200, "statut": "paye",
                 "date_loyer": "2024-03-01", "created_at": "2024-03-01T12:00:00"},
            ]
        })
        activity = await get_recent_activity(client, USER_ID)
        loyer_items = [a for a in activity if a["type"] == "loyer"]
        assert len(loyer_items) == 2
        # Most recent first
        assert loyer_items[0]["created_at"] > loyer_items[1]["created_at"]

    @pytest.mark.asyncio
    async def test_activity_respects_limit(self):
        many_loyers = [
            {"id": f"l{i}", "id_sci": SCI_1, "montant": 100 + i, "statut": "paye",
             "date_loyer": "2024-01-01", "created_at": f"2024-01-{i+1:02d}T00:00:00"}
            for i in range(15)
        ]
        client = _client_with({"loyers": many_loyers})
        activity = await get_recent_activity(client, USER_ID, limit=5)
        assert len(activity) <= 5

    @pytest.mark.asyncio
    async def test_activity_entry_fields(self):
        client = _client_with({
            "loyers": [
                {"id": "l1", "id_sci": SCI_1, "montant": 750, "statut": "paye",
                 "date_loyer": "2024-05-01", "created_at": "2024-05-02T09:00:00"},
            ]
        })
        activity = await get_recent_activity(client, USER_ID)
        item = next(a for a in activity if a["type"] == "loyer")
        assert "type" in item
        assert "description" in item
        assert "id_sci" in item
        assert "created_at" in item


# ---------------------------------------------------------------------------
# 8. _query_in_sci_ids fallback path (no in_ method) — lines 29-35
# ---------------------------------------------------------------------------

class TestQueryInSciIdsFallback:
    def test_fallback_without_in_method(self):
        """When the query object has no in_ method, fallback iterates per-SCI."""
        from tests.conftest import FakeResult

        class NoInQuery:
            def __init__(self, store, table):
                self._store = store
                self._table = table
                self._filters = {}

            def select(self, *a, **k):
                return self

            def eq(self, key, value):
                self._filters[key] = str(value)
                return self

            def execute(self):
                rows = self._store.get(self._table, [])
                matched = [r for r in rows if all(str(r.get(k)) == v for k, v in self._filters.items())]
                return FakeResult(data=matched)

        class NoInClient:
            def __init__(self):
                self._store = {
                    "biens": [
                        {"id": "b1", "id_sci": SCI_1, "adresse": "addr1"},
                        {"id": "b2", "id_sci": SCI_2, "adresse": "addr2"},
                        {"id": "b3", "id_sci": "other", "adresse": "addr3"},
                    ]
                }

            def table(self, name):
                return NoInQuery(self._store, name)

        result = _query_in_sci_ids(NoInClient(), "biens", "id,id_sci", [SCI_1, SCI_2])
        assert len(result) == 2
        ids = {r["id"] for r in result}
        assert ids == {"b1", "b2"}

    def test_fallback_raises_on_error(self):
        """Fallback path raises DatabaseError when result has error (line 33)."""
        from tests.conftest import FakeResult

        class ErrorQuery:
            def select(self, *a, **k): return self
            def eq(self, *a, **k): return self
            def execute(self): return FakeResult(data=[], error="db fail")

        class ErrorClient:
            def table(self, name):
                return ErrorQuery()

        with pytest.raises(DatabaseError):
            _query_in_sci_ids(ErrorClient(), "biens", "id", [SCI_1])


# ---------------------------------------------------------------------------
# 9. _query_in_sci_ids error after in_ — line 37-38
# ---------------------------------------------------------------------------

class TestQueryInSciIdsErrorAfterIn:
    def test_raises_on_error_after_in(self):
        """When in_ is available but execute() returns an error, raise DatabaseError."""
        from tests.conftest import FakeResult

        class InErrorQuery:
            def select(self, *a, **k): return self
            def in_(self, *a, **k): return self
            def execute(self): return FakeResult(data=[], error="connection lost")

        class InErrorClient:
            def table(self, name):
                return InErrorQuery()

        with pytest.raises(DatabaseError):
            _query_in_sci_ids(InErrorClient(), "biens", "id", [SCI_1])


# ---------------------------------------------------------------------------
# 10. _format_date_fr edge cases — lines 51-52
# ---------------------------------------------------------------------------

class TestFormatDateFr:
    def test_valid_date(self):
        from app.services.dashboard_service import _format_date_fr
        assert _format_date_fr("2025-07-01") == "1 juillet 2025"

    def test_invalid_date_returns_input(self):
        from app.services.dashboard_service import _format_date_fr
        assert _format_date_fr("not-a-date") == "not-a-date"

    def test_empty_string_returns_input(self):
        from app.services.dashboard_service import _format_date_fr
        assert _format_date_fr("") == ""

    def test_january(self):
        from app.services.dashboard_service import _format_date_fr
        assert _format_date_fr("2026-01-15") == "15 janvier 2026"

    def test_december(self):
        from app.services.dashboard_service import _format_date_fr
        assert _format_date_fr("2026-12-25") == "25 décembre 2026"


# ---------------------------------------------------------------------------
# 11. get_alertes — bail check exception (lines 136-138)
# ---------------------------------------------------------------------------

class TestGetAlertesBailException:
    @pytest.mark.asyncio
    async def test_bail_check_exception_swallowed(self):
        """When locataires query fails, alertes still returns loyer alerts."""
        from tests.conftest import FakeResult

        class FailLocatairesClient:
            """Client where locataires table raises on query."""
            def __init__(self):
                self._call_count = 0
                self._base = _client_with({
                    "loyers": [
                        {"id": "l1", "id_sci": SCI_1, "montant": 500,
                         "statut": "en_retard", "date_loyer": "2024-01-01"},
                    ]
                })

            def table(self, name):
                if name == "locataires":
                    raise RuntimeError("locataires table broken")
                return self._base.table(name)

        client = FailLocatairesClient()
        alertes = await get_alertes(client, USER_ID)
        # Should still have loyer alerts despite locataires failure
        loyer_alertes = [a for a in alertes if a["type"] == "loyer_en_retard"]
        assert len(loyer_alertes) >= 1


# ---------------------------------------------------------------------------
# 12. get_portfolio_kpis — charges exception (lines 194-197)
# ---------------------------------------------------------------------------

class TestGetPortfolioKpisChargesException:
    @pytest.mark.asyncio
    async def test_charges_exception_returns_zero(self):
        """When charges query fails, charges_total defaults to 0."""
        from tests.conftest import FakeResult

        class FailChargesClient:
            def __init__(self):
                self._base = _client_with({
                    "loyers": [
                        {"id": "l1", "id_sci": SCI_1, "montant": 1000, "statut": "paye",
                         "date_loyer": "2026-01-01"},
                    ],
                })

            def table(self, name):
                if name == "charges":
                    raise RuntimeError("charges table broken")
                return self._base.table(name)

        client = FailChargesClient()
        kpis = await get_portfolio_kpis(client, USER_ID)
        assert kpis["charges_total"] == 0.0
        assert kpis["loyers_payes"] == 1000.0


# ---------------------------------------------------------------------------
# 13. get_recent_activity — exception paths (lines 294-295, 310-311)
# ---------------------------------------------------------------------------

class TestGetRecentActivityExceptions:
    @pytest.mark.asyncio
    async def test_loyers_exception_returns_biens_only(self):
        """When loyers query fails, activity still includes biens."""

        class FailLoyersClient:
            def __init__(self):
                self._base = _client_with({
                    "biens": [
                        {"id": "b1", "id_sci": SCI_1, "adresse": "10 rue Test",
                         "created_at": "2024-01-01T00:00:00"},
                    ],
                })

            def table(self, name):
                if name == "loyers":
                    raise RuntimeError("loyers broken")
                return self._base.table(name)

        client = FailLoyersClient()
        activity = await get_recent_activity(client, USER_ID)
        bien_items = [a for a in activity if a["type"] == "bien"]
        assert len(bien_items) >= 1

    @pytest.mark.asyncio
    async def test_biens_exception_returns_loyers_only(self):
        """When biens query fails, activity still includes loyers."""

        class FailBiensClient:
            def __init__(self):
                self._base = _client_with({
                    "loyers": [
                        {"id": "l1", "id_sci": SCI_1, "montant": 800, "statut": "paye",
                         "date_loyer": "2024-03-01", "created_at": "2024-03-01T10:00:00"},
                    ],
                })

            def table(self, name):
                if name == "biens":
                    raise RuntimeError("biens broken")
                return self._base.table(name)

        client = FailBiensClient()
        activity = await get_recent_activity(client, USER_ID)
        loyer_items = [a for a in activity if a["type"] == "loyer"]
        assert len(loyer_items) >= 1

    @pytest.mark.asyncio
    async def test_bien_without_adresse_fallback(self):
        """Bien without adresse uses 'Bien' as default name."""
        client = _client_with({
            "biens": [
                {"id": "b-noadr", "id_sci": SCI_1, "created_at": "2024-01-01T00:00:00"},
            ],
        })
        activity = await get_recent_activity(client, USER_ID)
        bien_items = [a for a in activity if a["type"] == "bien"]
        assert any("Bien" in b["description"] for b in bien_items)
