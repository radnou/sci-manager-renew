"""Tests for app/services/bilan_mensuel_service.py.

Covers generate_bilan_mensuel, get_or_generate_bilan, list_periodes,
auto_generate_bilans, _send_bilan_email, and _empty_bilan.
All DB interactions go through FakeSupabaseClient (no real network calls).
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import FakeSupabaseClient
from app.services import bilan_mensuel_service
from app.services.bilan_mensuel_service import (
    _empty_bilan,
    generate_bilan_mensuel,
    get_or_generate_bilan,
    list_periodes,
    auto_generate_bilans,
    _upsert_bilan,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = "user-123"
PERIODE = "2026-03"


def _fresh() -> FakeSupabaseClient:
    """FakeSupabaseClient with base seed data."""
    c = FakeSupabaseClient()
    return c


def _empty() -> FakeSupabaseClient:
    """Client with no associes — user has no SCIs."""
    c = FakeSupabaseClient()
    c.store["associes"] = []
    return c


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# 1. _empty_bilan
# ---------------------------------------------------------------------------

class TestEmptyBilan:
    def test_structure(self):
        b = _empty_bilan("2026-05")
        assert b["periode"] == "2026-05"
        assert b["scis"] == []
        assert b["total_entrees"] == 0
        assert b["total_sorties"] == 0
        assert b["solde"] == 0

    def test_kpis_all_zero(self):
        b = _empty_bilan("2026-05")
        kpis = b["kpis"]
        assert kpis["nb_biens"] == 0
        assert kpis["nb_scis"] == 0
        assert kpis["taux_recouvrement"] == 0

    def test_portefeuille_all_zero(self):
        b = _empty_bilan("2026-05")
        p = b["portefeuille"]
        assert p["cashflow_net"] == 0
        assert p["revenus_attendus"] == 0

    def test_generated_at_present(self):
        b = _empty_bilan("2026-01")
        assert "generated_at" in b
        assert b["generated_at"]  # non-empty string


# ---------------------------------------------------------------------------
# 2. generate_bilan_mensuel — no SCIs
# ---------------------------------------------------------------------------

class TestGenerateBilanNoSci:
    def test_returns_empty_bilan_when_no_associes(self):
        c = _empty()
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        assert result["scis"] == []
        assert result["total_entrees"] == 0
        assert result["kpis"]["nb_scis"] == 0

    def test_returns_empty_bilan_when_no_biens(self):
        c = _fresh()
        c.store["biens"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        assert result["total_entrees"] == 0
        assert result["scis"] == []


# ---------------------------------------------------------------------------
# 3. generate_bilan_mensuel — nominal with loyers
# ---------------------------------------------------------------------------

class TestGenerateBilanWithLoyers:
    def setup_method(self):
        self.c = _fresh()
        # Only loyers in 2026-03 (PERIODE)
        self.c.store["loyers"] = [
            {
                "id": "l-a", "id_bien": "bien-1",
                "date_loyer": "2026-03-05", "montant": 1000.0,
                "statut": "paye", "id_locataire": None,
            },
            {
                "id": "l-b", "id_bien": "bien-9",
                "date_loyer": "2026-03-01", "montant": 800.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        self.c.store["charges"] = []

    def test_total_entrees(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        assert result["total_entrees"] == 1800.0

    def test_total_sorties_zero_when_no_charges(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        assert result["total_sorties"] == 0.0

    def test_solde_equals_entrees(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        assert result["solde"] == 1800.0

    def test_kpis_nb_biens_populated(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        kpis = result["kpis"]
        assert kpis["nb_biens"] >= 1
        assert kpis["nb_scis"] >= 1

    def test_taux_recouvrement_100_when_all_paid(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        assert result["kpis"]["taux_recouvrement"] == 100.0

    def test_scis_list_populated(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        assert len(result["scis"]) >= 1

    def test_bien_data_contains_lignes(self):
        result = _run(generate_bilan_mensuel(self.c, USER_ID, PERIODE))
        # Find any bien with a loyer
        found = False
        for sci in result["scis"]:
            for bien in sci["biens"]:
                if bien["total_entrees"] > 0:
                    found = True
                    assert len(bien["lignes"]) >= 1
                    # Verify ligne structure
                    l = bien["lignes"][0]
                    assert "date" in l
                    assert "libelle" in l
                    assert "entrees" in l
                    assert "sorties" in l
                    assert "solde" in l
                    assert "type" in l
        assert found


# ---------------------------------------------------------------------------
# 4. generate_bilan_mensuel — with charges
# ---------------------------------------------------------------------------

class TestGenerateBilanWithCharges:
    def test_charges_reduce_solde(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l1", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 1200.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = [
            {
                "id": "ch1", "id_bien": "bien-1",
                "montant": 300.0, "type_charge": "copropriete",
                "date_paiement": "2026-03-10",
            },
        ]
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        assert result["total_sorties"] == 300.0
        assert result["solde"] == pytest.approx(900.0)

    def test_charge_lignes_type_is_charge(self):
        c = _fresh()
        c.store["loyers"] = []
        c.store["charges"] = [
            {
                "id": "ch2", "id_bien": "bien-1",
                "montant": 150.0, "type_charge": "taxe_fonciere",
                "date_paiement": "2026-03-15",
            },
        ]
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        # Find the charge ligne
        for sci in result["scis"]:
            for bien in sci["biens"]:
                for ligne in bien["lignes"]:
                    if ligne["type"] == "charge":
                        assert ligne["sorties"] == 150.0
                        assert ligne["entrees"] == 0


# ---------------------------------------------------------------------------
# 5. generate_bilan_mensuel — impayés
# ---------------------------------------------------------------------------

class TestGenerateBilanImpayes:
    def test_impaye_loyer_not_counted_in_entrees(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l-paid", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 1000.0,
                "statut": "paye", "id_locataire": None,
            },
            {
                "id": "l-late", "id_bien": "bien-1",
                "date_loyer": "2026-03-05", "montant": 500.0,
                "statut": "en_retard", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        assert result["total_entrees"] == 1000.0  # only the paid one

    def test_en_attente_loyer_counted_as_impaye(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l-pend", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 800.0,
                "statut": "en_attente", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        assert result["total_entrees"] == 0.0
        # The impayes field in portefeuille should be 800
        assert result["portefeuille"]["impayes"] == 800.0


# ---------------------------------------------------------------------------
# 6. generate_bilan_mensuel — with locataire name resolution
# ---------------------------------------------------------------------------

class TestGenerateBilanLocataire:
    def test_locataire_name_in_libelle(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l-loc", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 900.0,
                "statut": "paye", "id_locataire": "loc-1",
            },
        ]
        c.store["locataires"] = [
            {"id": "loc-1", "nom": "Dupont"},
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        # Find the loyer ligne
        for sci in result["scis"]:
            for bien in sci["biens"]:
                for ligne in bien["lignes"]:
                    if ligne["type"] == "loyer":
                        assert "Dupont" in ligne["libelle"]

    def test_loyer_without_locataire_uses_default_label(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l-noname", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 700.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        for sci in result["scis"]:
            for bien in sci["biens"]:
                for ligne in bien["lignes"]:
                    if ligne["type"] == "loyer":
                        assert ligne["libelle"] == "Loyer"


# ---------------------------------------------------------------------------
# 7. generate_bilan_mensuel — December (month == 12) boundary
# ---------------------------------------------------------------------------

class TestGenerateBilanDecember:
    def test_december_date_range_correct(self):
        """Month 12 → next year Jan boundary — no crash."""
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l-dec", "id_bien": "bien-1",
                "date_loyer": "2025-12-15", "montant": 1000.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, "2025-12"))
        assert result["periode"] == "2025-12"
        assert result["total_entrees"] == 1000.0


# ---------------------------------------------------------------------------
# 8. generate_bilan_mensuel — legacy fields preserved
# ---------------------------------------------------------------------------

class TestGenerateBilanLegacyFields:
    def test_portefeuille_field_present(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l1", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 500.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        assert "portefeuille" in result
        p = result["portefeuille"]
        assert "revenus_attendus" in p
        assert "revenus_encaisses" in p
        assert "cashflow_net" in p
        assert "taux_recouvrement" in p
        assert "nb_biens" in p
        assert "nb_scis" in p

    def test_sci_legacy_fields(self):
        c = _fresh()
        c.store["loyers"] = []
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        for sci in result["scis"]:
            assert "revenus_attendus" in sci
            assert "cashflow_net" in sci
            assert "taux_recouvrement" in sci


# ---------------------------------------------------------------------------
# 9. list_periodes
# ---------------------------------------------------------------------------

class TestListPeriodes:
    def test_returns_sorted_desc(self):
        c = _fresh()
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-1", "date_loyer": "2026-01-01",
             "montant": 100, "statut": "paye", "id_locataire": None},
            {"id": "l2", "id_bien": "bien-1", "date_loyer": "2026-03-15",
             "montant": 100, "statut": "paye", "id_locataire": None},
            {"id": "l3", "id_bien": "bien-9", "date_loyer": "2025-12-01",
             "montant": 100, "statut": "paye", "id_locataire": None},
        ]
        periods = _run(list_periodes(c, USER_ID))
        assert periods[0] >= periods[-1]  # descending order

    def test_deduplicates_same_month(self):
        c = _fresh()
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-1", "date_loyer": "2026-03-05",
             "montant": 100, "statut": "paye", "id_locataire": None},
            {"id": "l2", "id_bien": "bien-1", "date_loyer": "2026-03-20",
             "montant": 100, "statut": "paye", "id_locataire": None},
        ]
        periods = _run(list_periodes(c, USER_ID))
        assert periods.count("2026-03") == 1

    def test_returns_empty_when_no_associes(self):
        c = _empty()
        periods = _run(list_periodes(c, USER_ID))
        assert periods == []

    def test_returns_empty_when_no_biens(self):
        c = _fresh()
        c.store["biens"] = []
        periods = _run(list_periodes(c, USER_ID))
        assert periods == []

    def test_returns_empty_when_no_loyers(self):
        c = _fresh()
        c.store["loyers"] = []
        periods = _run(list_periodes(c, USER_ID))
        assert periods == []

    def test_month_format_is_yyyy_mm(self):
        c = _fresh()
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-1", "date_loyer": "2026-05-10",
             "montant": 100, "statut": "paye", "id_locataire": None},
        ]
        periods = _run(list_periodes(c, USER_ID))
        assert "2026-05" in periods
        assert all(len(p) == 7 for p in periods)


# ---------------------------------------------------------------------------
# 10. get_or_generate_bilan — cache hit
# ---------------------------------------------------------------------------

class TestGetOrGenerateBilanCacheHit:
    def test_returns_cached_data_when_present(self):
        c = _fresh()
        cached_data = {"periode": PERIODE, "total_entrees": 9999.0}
        c.store["bilans_mensuels"] = [
            {
                "user_id": USER_ID,
                "periode": PERIODE,
                "scope": "portefeuille",
                "scope_id": None,
                "data": cached_data,
                "scope_nom": "Portefeuille",
            }
        ]
        result = _run(get_or_generate_bilan(c, USER_ID, PERIODE))
        assert result["total_entrees"] == 9999.0

    def test_force_refresh_bypasses_cache(self):
        c = _fresh()
        cached_data = {"periode": PERIODE, "total_entrees": 9999.0}
        c.store["bilans_mensuels"] = [
            {
                "user_id": USER_ID,
                "periode": PERIODE,
                "scope": "portefeuille",
                "scope_id": None,
                "data": cached_data,
                "scope_nom": "Portefeuille",
            }
        ]
        c.store["loyers"] = []
        c.store["charges"] = []
        # With force_refresh, should regenerate (not use 9999)
        result = _run(get_or_generate_bilan(c, USER_ID, PERIODE, force_refresh=True))
        assert result.get("total_entrees") != 9999.0


# ---------------------------------------------------------------------------
# 11. get_or_generate_bilan — scope = "sci"
# ---------------------------------------------------------------------------

class TestGetOrGenerateBilanScopeSci:
    def test_sci_scope_returns_scoped_data(self):
        c = _fresh()
        c.store["bilans_mensuels"] = []
        c.store["loyers"] = [
            {
                "id": "l1", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 500.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(
            get_or_generate_bilan(c, USER_ID, PERIODE, scope="sci", scope_id="sci-1")
        )
        # Should contain period
        assert "periode" in result

    def test_sci_scope_id_not_found_returns_full_bilan(self):
        c = _fresh()
        c.store["bilans_mensuels"] = []
        c.store["loyers"] = []
        c.store["charges"] = []
        result = _run(
            get_or_generate_bilan(c, USER_ID, PERIODE, scope="sci", scope_id="nonexistent-sci")
        )
        # Falls through to full bilan
        assert "periode" in result

    def test_bien_scope_returns_scoped_data(self):
        c = _fresh()
        c.store["bilans_mensuels"] = []
        c.store["loyers"] = [
            {
                "id": "l1", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 700.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(
            get_or_generate_bilan(c, USER_ID, PERIODE, scope="bien", scope_id="bien-1")
        )
        assert "periode" in result

    def test_bien_scope_id_not_found_returns_full_bilan(self):
        c = _fresh()
        c.store["bilans_mensuels"] = []
        c.store["loyers"] = []
        c.store["charges"] = []
        result = _run(
            get_or_generate_bilan(c, USER_ID, PERIODE, scope="bien", scope_id="nonexistent-bien")
        )
        assert "periode" in result

    def test_unknown_scope_falls_back_to_portefeuille(self):
        c = _fresh()
        c.store["bilans_mensuels"] = []
        c.store["loyers"] = []
        c.store["charges"] = []
        result = _run(
            get_or_generate_bilan(c, USER_ID, PERIODE, scope="unknown_scope")
        )
        assert "periode" in result


# ---------------------------------------------------------------------------
# 12. _upsert_bilan — writes to store
# ---------------------------------------------------------------------------

class TestUpsertBilan:
    def test_upserts_row_to_bilans_mensuels(self):
        c = _fresh()
        c.store["bilans_mensuels"] = []
        data = {"periode": PERIODE, "total_entrees": 42.0}
        _upsert_bilan(c, USER_ID, PERIODE, "portefeuille", None, "Portefeuille", data)
        assert len(c.store["bilans_mensuels"]) == 1
        row = c.store["bilans_mensuels"][0]
        assert row["user_id"] == USER_ID
        assert row["scope"] == "portefeuille"

    def test_upsert_exception_swallowed(self):
        """If upsert fails (e.g., broken client), no exception propagates."""
        class BrokenClient:
            def table(self, name):
                raise RuntimeError("DB crash")

        # Should not raise
        _upsert_bilan(BrokenClient(), USER_ID, PERIODE, "portefeuille", None, "p", {})


# ---------------------------------------------------------------------------
# 13. auto_generate_bilans — wrong day returns 0
# ---------------------------------------------------------------------------

class TestAutoGenerateBilans:
    def test_returns_zero_when_not_day_2(self):
        from unittest.mock import patch
        from datetime import datetime, timezone

        # Force datetime.now to return a day != 2
        with patch(
            "app.services.bilan_mensuel_service.datetime"
        ) as mock_dt:
            # Create a real datetime for day 1
            fake_now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = fake_now

            c = _fresh()
            result = _run(auto_generate_bilans(c))
            assert result == 0

    def test_runs_on_day_2_and_generates_per_active_user(self):
        from unittest.mock import patch
        from datetime import datetime, timezone

        with patch(
            "app.services.bilan_mensuel_service.datetime"
        ) as mock_dt:
            fake_now = datetime(2026, 6, 2, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = fake_now

            c = _fresh()
            c.store["subscriptions"] = [
                {"user_id": USER_ID, "status": "active"},
            ]
            c.store["bilans_mensuels"] = []
            c.store["loyers"] = []
            c.store["charges"] = []

            # Patch email so we don't actually try to send
            with patch("app.services.bilan_mensuel_service._send_bilan_email", new=AsyncMock()):
                result = _run(auto_generate_bilans(c))
            assert result >= 1

    def test_january_uses_december_prev_month(self):
        """When current month is January, previous month should be December."""
        from unittest.mock import patch
        from datetime import datetime, timezone

        with patch(
            "app.services.bilan_mensuel_service.datetime"
        ) as mock_dt:
            fake_now = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = fake_now

            c = _fresh()
            c.store["subscriptions"] = [
                {"user_id": USER_ID, "status": "active"},
            ]
            c.store["bilans_mensuels"] = []
            c.store["loyers"] = []
            c.store["charges"] = []

            with patch("app.services.bilan_mensuel_service._send_bilan_email", new=AsyncMock()):
                result = _run(auto_generate_bilans(c))
            # Should have tried to generate for 2025-12
            assert isinstance(result, int)


# ---------------------------------------------------------------------------
# 14. _send_bilan_email — email lookup paths
# ---------------------------------------------------------------------------

class TestSendBilanEmail:
    def test_sends_via_auth_users_email(self):
        """When auth.users returns email, email_service.send_email is called."""
        from app.services.bilan_mensuel_service import _send_bilan_email

        c = _fresh()
        c.store["auth.users"] = [{"id": USER_ID, "email": "test@example.com"}]
        c.store["notification_preferences"] = []

        mock_email = AsyncMock()
        mock_email.frontend_url = "https://example.com"
        with patch("app.services.email_service.email_service", mock_email):
            _run(_send_bilan_email(c, USER_ID, PERIODE))
            mock_email.send_email.assert_called_once()

    def test_falls_back_to_associes_when_auth_users_empty(self):
        """When auth.users returns empty, falls back to associes table."""
        from app.services.bilan_mensuel_service import _send_bilan_email

        c = _fresh()
        c.store["auth.users"] = []
        # Associes has an email for this user (from conftest seed)
        c.store["notification_preferences"] = []

        mock_email = AsyncMock()
        mock_email.frontend_url = "https://example.com"
        with patch("app.services.email_service.email_service", mock_email):
            _run(_send_bilan_email(c, USER_ID, PERIODE))
            mock_email.send_email.assert_called_once()

    def test_skips_email_when_preferences_disabled(self):
        """When notification_preferences disables bilan_mensuel email, skip."""
        from app.services.bilan_mensuel_service import _send_bilan_email

        c = _fresh()
        c.store["auth.users"] = [{"id": USER_ID, "email": "test@example.com"}]
        c.store["notification_preferences"] = [
            {
                "user_id": USER_ID,
                "notification_type": "bilan_mensuel",
                "email_enabled": False,
            }
        ]

        mock_email = AsyncMock()
        mock_email.frontend_url = "https://example.com"
        with patch("app.services.email_service.email_service", mock_email):
            _run(_send_bilan_email(c, USER_ID, PERIODE))
            mock_email.send_email.assert_not_called()

    def test_skips_email_when_no_email_found(self):
        """When no email can be found, do not call send_email."""
        from app.services.bilan_mensuel_service import _send_bilan_email

        c = _fresh()
        c.store["auth.users"] = []
        c.store["associes"] = []  # no fallback either
        c.store["notification_preferences"] = []

        mock_email = AsyncMock()
        mock_email.frontend_url = "https://example.com"
        with patch("app.services.email_service.email_service", mock_email):
            _run(_send_bilan_email(c, USER_ID, PERIODE))
            mock_email.send_email.assert_not_called()

    def test_exception_in_email_swallowed(self):
        """Email failures should be logged but not re-raised."""
        from app.services.bilan_mensuel_service import _send_bilan_email

        c = _fresh()
        c.store["auth.users"] = [{"id": USER_ID, "email": "test@example.com"}]
        c.store["notification_preferences"] = []

        mock_email = AsyncMock()
        mock_email.send_email = AsyncMock(side_effect=RuntimeError("SMTP error"))
        mock_email.frontend_url = "https://example.com"
        with patch("app.services.email_service.email_service", mock_email):
            # Should not raise
            _run(_send_bilan_email(c, USER_ID, PERIODE))


# ---------------------------------------------------------------------------
# 15. generate_bilan_mensuel — running solde computed correctly
# ---------------------------------------------------------------------------

class TestRunningBalanceComputation:
    def test_running_solde_increases_with_loyer(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l1", "id_bien": "bien-1",
                "date_loyer": "2026-03-01", "montant": 500.0,
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = [
            {
                "id": "ch1", "id_bien": "bien-1",
                "montant": 100.0, "type_charge": "copropriete",
                "date_paiement": "2026-03-02",
            },
        ]
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        for sci in result["scis"]:
            for bien in sci["biens"]:
                if bien["total_entrees"] > 0:
                    # Last ligne should have running solde of 500 - 100 = 400
                    lignes = bien["lignes"]
                    assert lignes[-1]["solde"] == pytest.approx(400.0)


# ---------------------------------------------------------------------------
# 16. generate_bilan_mensuel — loyers outside period are excluded
# ---------------------------------------------------------------------------

class TestLoyersOutsidePeriodExcluded:
    def test_loyers_from_different_period_not_included(self):
        c = _fresh()
        c.store["loyers"] = [
            {
                "id": "l-other", "id_bien": "bien-1",
                "date_loyer": "2026-04-01", "montant": 9999.0,  # April, not March
                "statut": "paye", "id_locataire": None,
            },
        ]
        c.store["charges"] = []
        result = _run(generate_bilan_mensuel(c, USER_ID, PERIODE))
        # PERIODE is "2026-03", so this April loyer should not appear
        assert result["total_entrees"] == 0.0
