"""Unit tests for finances_service.get_finances_overview."""
from __future__ import annotations

import pytest

from app.services.finances_service import get_finances_overview, _empty_response
from tests.conftest import FakeSupabaseClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client_with_data(
    *,
    user_id: str = "user-123",
    sci_ids: list[str] | None = None,
    biens: list[dict] | None = None,
    loyers: list[dict] | None = None,
    charges: list[dict] | None = None,
) -> FakeSupabaseClient:
    """Return a FakeSupabaseClient pre-seeded with the supplied data."""
    client = FakeSupabaseClient()

    # Replace the default store contents to have precise control
    if sci_ids is not None:
        # Keep only sci rows for the requested ids
        client.store["sci"] = [
            s for s in client.store["sci"] if s["id"] in sci_ids
        ]
        # Keep only associes rows for this user + those sci_ids
        client.store["associes"] = [
            a for a in client.store["associes"]
            if a["user_id"] == user_id and a["id_sci"] in sci_ids
        ]

    if biens is not None:
        client.store["biens"] = biens
    if loyers is not None:
        client.store["loyers"] = loyers
    if charges is not None:
        client.store["charges"] = charges

    return client


# ---------------------------------------------------------------------------
# 1. _empty_response helper
# ---------------------------------------------------------------------------

def test_empty_response_structure():
    result = _empty_response()
    assert result["revenus_total"] == 0
    assert result["charges_total"] == 0
    assert result["cashflow_net"] == 0
    assert result["taux_recouvrement"] == 0
    assert result["patrimoine_total"] == 0
    assert result["rentabilite_moyenne"] == 0
    assert result["evolution_mensuelle"] == []
    assert result["repartition_sci"] == []


# ---------------------------------------------------------------------------
# 2. No SCIs for user → immediate empty response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_scis_returns_empty():
    client = FakeSupabaseClient()
    # Use a user that has no associes entries at all
    result = await get_finances_overview(client, "unknown-user")

    assert result == _empty_response()


# ---------------------------------------------------------------------------
# 3. SCIs exist but no biens → patrimoine 0, repartition_sci populated
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scis_no_biens_returns_partial_empty():
    client = make_client_with_data(
        user_id="user-123",
        sci_ids=["sci-1"],
        biens=[],
        loyers=[],
        charges=[],
    )
    result = await get_finances_overview(client, "user-123")

    assert result["revenus_total"] == 0
    assert result["charges_total"] == 0
    assert result["cashflow_net"] == 0
    assert result["patrimoine_total"] == 0
    assert result["taux_recouvrement"] == 0
    # repartition_sci should list the SCI even with zeros
    assert len(result["repartition_sci"]) == 1
    assert result["repartition_sci"][0]["sci_nom"] == "SCI Mosa Belleville"
    assert result["repartition_sci"][0]["revenus"] == 0
    assert result["repartition_sci"][0]["charges"] == 0


# ---------------------------------------------------------------------------
# 4. Full data: revenus, charges, cashflow, taux_recouvrement, patrimoine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_data_aggregation():
    bien_id = "bien-1"
    sci_id = "sci-1"

    client = make_client_with_data(
        user_id="user-123",
        sci_ids=[sci_id],
        biens=[
            {"id": bien_id, "id_sci": sci_id, "prix_acquisition": 200_000, "loyer_cc": 1_000, "charges": 100},
        ],
        loyers=[
            {"id": "l1", "id_bien": bien_id, "montant": 1_000, "statut": "paye", "date_loyer": "2025-12-01"},
            {"id": "l2", "id_bien": bien_id, "montant": 1_000, "statut": "paye", "date_loyer": "2025-11-01"},
            {"id": "l3", "id_bien": bien_id, "montant": 1_000, "statut": "impaye", "date_loyer": "2025-10-01"},
        ],
        charges=[
            {"id": "c1", "id_bien": bien_id, "montant": 300, "date_paiement": "2025-12-15"},
        ],
    )
    result = await get_finances_overview(client, "user-123", period_months=36)

    assert result["revenus_total"] == 2_000.0     # only paye loyers
    assert result["charges_total"] == 300.0
    assert result["cashflow_net"] == 1_700.0
    # taux = 2000 / 3000 * 100 = 66.7
    assert result["taux_recouvrement"] == pytest.approx(66.7, abs=0.1)
    assert result["patrimoine_total"] == 200_000.0


# ---------------------------------------------------------------------------
# 5. Period filtering: loyers outside the cutoff are excluded
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_period_filtering_excludes_old_records():
    bien_id = "bien-2"
    sci_id = "sci-1"

    client = make_client_with_data(
        user_id="user-123",
        sci_ids=[sci_id],
        biens=[
            {"id": bien_id, "id_sci": sci_id, "prix_acquisition": 100_000, "loyer_cc": 800, "charges": 0},
        ],
        loyers=[
            # recent — should be included
            {"id": "l-new", "id_bien": bien_id, "montant": 800, "statut": "paye", "date_loyer": "2025-10-01"},
            # very old — should be excluded by FakeQuery gte filter
            {"id": "l-old", "id_bien": bien_id, "montant": 800, "statut": "paye", "date_loyer": "2000-01-01"},
        ],
        charges=[],
    )
    result = await get_finances_overview(client, "user-123", period_months=12)

    # Only the recent loyer should count
    assert result["revenus_total"] == 800.0
    assert result["cashflow_net"] == 800.0


# ---------------------------------------------------------------------------
# 6. evolution_mensuelle groups loyers by month
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evolution_mensuelle_grouping():
    bien_id = "bien-3"
    sci_id = "sci-1"

    client = make_client_with_data(
        user_id="user-123",
        sci_ids=[sci_id],
        biens=[
            {"id": bien_id, "id_sci": sci_id, "prix_acquisition": 50_000, "loyer_cc": 500, "charges": 0},
        ],
        loyers=[
            {"id": "la", "id_bien": bien_id, "montant": 500, "statut": "paye", "date_loyer": "2025-11-01"},
            {"id": "lb", "id_bien": bien_id, "montant": 500, "statut": "paye", "date_loyer": "2025-11-15"},
            {"id": "lc", "id_bien": bien_id, "montant": 600, "statut": "paye", "date_loyer": "2025-12-01"},
        ],
        charges=[
            {"id": "ca", "id_bien": bien_id, "montant": 100, "date_paiement": "2025-12-05"},
        ],
    )
    result = await get_finances_overview(client, "user-123", period_months=36)

    months = {m["mois"]: m for m in result["evolution_mensuelle"]}
    assert "2025-11" in months
    assert "2025-12" in months
    assert months["2025-11"]["revenus"] == pytest.approx(1_000.0)
    assert months["2025-11"]["charges"] == pytest.approx(0.0)
    assert months["2025-12"]["revenus"] == pytest.approx(600.0)
    assert months["2025-12"]["charges"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 7. repartition_sci aggregates correctly across multiple SCIs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repartition_sci_multiple_scis():
    client = make_client_with_data(
        user_id="user-123",
        sci_ids=["sci-1", "sci-2"],
        biens=[
            {"id": "b-sci1", "id_sci": "sci-1", "prix_acquisition": 100_000, "loyer_cc": 1_000, "charges": 0},
            {"id": "b-sci2", "id_sci": "sci-2", "prix_acquisition": 200_000, "loyer_cc": 2_000, "charges": 0},
        ],
        loyers=[
            {"id": "l-s1", "id_bien": "b-sci1", "montant": 1_000, "statut": "paye", "date_loyer": "2025-12-01"},
            {"id": "l-s2", "id_bien": "b-sci2", "montant": 2_000, "statut": "paye", "date_loyer": "2025-12-01"},
        ],
        charges=[],
    )
    result = await get_finances_overview(client, "user-123", period_months=36)

    sci_data = {r["sci_nom"]: r for r in result["repartition_sci"]}
    assert sci_data["SCI Mosa Belleville"]["revenus"] == pytest.approx(1_000.0)
    assert sci_data["SCI Horizon Lyon"]["revenus"] == pytest.approx(2_000.0)
    assert result["revenus_total"] == pytest.approx(3_000.0)
    assert result["patrimoine_total"] == pytest.approx(300_000.0)


# ---------------------------------------------------------------------------
# 8. Statut "paid" (English variant) is treated as paid
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_statut_paid_english_variant():
    bien_id = "bien-4"
    sci_id = "sci-1"

    client = make_client_with_data(
        user_id="user-123",
        sci_ids=[sci_id],
        biens=[
            {"id": bien_id, "id_sci": sci_id, "prix_acquisition": 0, "loyer_cc": 700, "charges": 0},
        ],
        loyers=[
            {"id": "lx", "id_bien": bien_id, "montant": 700, "statut": "paid", "date_loyer": "2025-12-01"},
        ],
        charges=[],
    )
    result = await get_finances_overview(client, "user-123", period_months=36)

    assert result["revenus_total"] == 700.0
    assert result["taux_recouvrement"] == 100.0


# ---------------------------------------------------------------------------
# 9. Rentabilite_moyenne calculation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rentabilite_moyenne_calculation():
    bien_id = "bien-5"
    sci_id = "sci-1"

    client = make_client_with_data(
        user_id="user-123",
        sci_ids=[sci_id],
        biens=[
            {"id": bien_id, "id_sci": sci_id, "prix_acquisition": 100_000, "loyer_cc": 1_000, "charges": 0},
        ],
        loyers=[
            {"id": "lr", "id_bien": bien_id, "montant": 1_000, "statut": "paye", "date_loyer": "2025-12-01"},
        ],
        charges=[],
    )
    # period_months=12, revenus=1000, patrimoine=100000
    # rentabilite = (1000 / 100000 * 100) * (12/12) = 1.0%
    result = await get_finances_overview(client, "user-123", period_months=12)

    assert result["rentabilite_moyenne"] == pytest.approx(1.0, abs=0.1)


# ---------------------------------------------------------------------------
# 10. Zero patrimoine does not cause division by zero
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_zero_patrimoine_no_division_error():
    bien_id = "bien-6"
    sci_id = "sci-1"

    client = make_client_with_data(
        user_id="user-123",
        sci_ids=[sci_id],
        biens=[
            {"id": bien_id, "id_sci": sci_id, "prix_acquisition": 0, "loyer_cc": 500, "charges": 0},
        ],
        loyers=[
            {"id": "lz", "id_bien": bien_id, "montant": 500, "statut": "paye", "date_loyer": "2025-12-01"},
        ],
        charges=[],
    )
    result = await get_finances_overview(client, "user-123", period_months=12)

    assert result["rentabilite_moyenne"] == 0
    assert result["patrimoine_total"] == 0
