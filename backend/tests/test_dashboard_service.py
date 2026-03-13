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
