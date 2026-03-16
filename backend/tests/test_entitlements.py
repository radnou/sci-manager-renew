"""Tests for plan entitlements catalog and helper functions."""

from app.core.entitlements import (
    PlanKey,
    get_plan,
    list_public_plans,
    resolve_plan_key_from_price_id,
    resolve_price_id_for_plan,
)


def test_free_plan_is_public():
    plan = get_plan(PlanKey.FREE)
    assert plan.is_public is True
    assert plan.display_name == "Essentiel"
    assert plan.max_scis == 1
    assert plan.max_biens == 2


def test_starter_plan_renamed_gestion():
    plan = get_plan(PlanKey.STARTER)
    assert plan.display_name == "Gestion"
    assert plan.max_scis == 3
    assert plan.max_biens == 10
    assert plan.multi_sci_enabled is True
    assert plan.documents_enabled is True
    assert plan.notifications_enabled is True
    assert plan.dashboard_complet is True
    assert plan.cerfa_enabled is False
    assert plan.fiscalite_enabled is False


def test_pro_plan_renamed_fiscal():
    plan = get_plan(PlanKey.PRO)
    assert plan.display_name == "Fiscal"
    assert plan.max_scis is None
    assert plan.max_biens is None
    assert plan.cerfa_enabled is True
    assert plan.fiscalite_enabled is True
    assert plan.associes_enabled is True
    assert plan.pno_frais_enabled is True
    assert plan.rentabilite_enabled is True
    assert plan.dashboard_complet is True


def test_lifetime_grandfathered_to_pro():
    plan = get_plan(PlanKey.LIFETIME)
    assert plan.plan_key == PlanKey.PRO
    assert plan.display_name == "Fiscal"


def test_features_payload_includes_new_fields():
    plan = get_plan(PlanKey.PRO)
    payload = plan.features_payload()
    assert "documents_enabled" in payload
    assert "notifications_enabled" in payload
    assert "associes_enabled" in payload
    assert "pno_frais_enabled" in payload
    assert "rentabilite_enabled" in payload
    assert "dashboard_complet" in payload
    assert payload["documents_enabled"] is True


def test_list_public_plans_includes_all_three():
    plans = list_public_plans()
    keys = {p.plan_key for p in plans}
    assert keys == {PlanKey.FREE, PlanKey.STARTER, PlanKey.PRO}


def test_resolve_price_id_annual_starter(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_starter_annual_price_id", "price_starter_annual")
    result = resolve_price_id_for_plan(PlanKey.STARTER, billing_period="year")
    assert result == "price_starter_annual"


def test_resolve_price_id_monthly_default(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_starter_monthly")
    result = resolve_price_id_for_plan(PlanKey.STARTER)
    assert result == "price_starter_monthly"


def test_resolve_plan_key_from_annual_price(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_pro_annual_price_id", "price_pro_annual")
    result = resolve_plan_key_from_price_id("price_pro_annual")
    assert result == PlanKey.PRO


def test_resolve_price_id_lifetime_returns_none():
    result = resolve_price_id_for_plan(PlanKey.LIFETIME)
    assert result is None
