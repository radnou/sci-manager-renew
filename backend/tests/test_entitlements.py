"""Tests for plan entitlements catalog and helper functions."""

from datetime import datetime, timedelta, timezone

from app.core.entitlements import (
    PlanKey,
    get_plan,
    get_trial_expired_plan,
    is_trial_active,
    list_public_plans,
    resolve_plan_key_from_price_id,
    resolve_price_id_for_plan,
)


def test_free_plan_is_trial():
    plan = get_plan(PlanKey.FREE)
    assert plan.is_public is False
    assert plan.display_name == "Essai"
    assert plan.max_scis == 1
    assert plan.max_biens == 5
    # Trial has full Pilotage-level features
    assert plan.cerfa_enabled is True
    assert plan.fiscalite_enabled is True
    assert plan.associes_enabled is True


def test_starter_plan_is_gestion():
    plan = get_plan(PlanKey.STARTER)
    assert plan.display_name == "Gestion"
    assert plan.max_scis == 1
    assert plan.max_biens == 5
    assert plan.multi_sci_enabled is False
    assert plan.documents_enabled is True
    assert plan.notifications_enabled is True
    assert plan.dashboard_complet is True
    assert plan.cerfa_enabled is True
    assert plan.fiscalite_enabled is True


def test_pro_plan_is_pilotage():
    plan = get_plan(PlanKey.PRO)
    assert plan.display_name == "Pilotage"
    assert plan.max_scis is None
    assert plan.max_biens is None
    assert plan.cerfa_enabled is True
    assert plan.fiscalite_enabled is True
    assert plan.associes_enabled is True
    assert plan.pno_frais_enabled is True
    assert plan.rentabilite_enabled is True
    assert plan.dashboard_complet is True
    assert plan.multi_sci_enabled is True


def test_fondateur_plan():
    plan = get_plan(PlanKey.FONDATEUR)
    assert plan.display_name == "Fondateur"
    assert plan.max_scis is None
    assert plan.max_biens is None
    assert plan.lifetime is True
    assert plan.checkout_mode == "payment"
    assert plan.billing_period == "lifetime"
    # Same features as Pilotage
    assert plan.cerfa_enabled is True
    assert plan.fiscalite_enabled is True
    assert plan.associes_enabled is True
    assert plan.pno_frais_enabled is True
    assert plan.rentabilite_enabled is True


def test_lifetime_grandfathered_to_pro():
    plan = get_plan(PlanKey.LIFETIME)
    assert plan.plan_key == PlanKey.PRO
    assert plan.display_name == "Pilotage"


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


def test_list_public_plans_includes_paid_plans():
    plans = list_public_plans()
    keys = {p.plan_key for p in plans}
    # FREE is no longer public (it's trial-only), FONDATEUR is public
    assert PlanKey.STARTER in keys
    assert PlanKey.PRO in keys
    assert PlanKey.FONDATEUR in keys
    assert PlanKey.CABINET in keys
    assert PlanKey.FREE not in keys


def test_resolve_price_id_fondateur(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_fondateur_price_id", "price_fondateur_test")
    result = resolve_price_id_for_plan(PlanKey.FONDATEUR)
    assert result == "price_fondateur_test"


def test_resolve_price_id_gestion_fallback(monkeypatch):
    """New gestion env var falls back to old starter env var."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_gestion_monthly_price_id", "")
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_starter_monthly")
    result = resolve_price_id_for_plan(PlanKey.STARTER)
    assert result == "price_starter_monthly"


def test_resolve_price_id_gestion_new_var(monkeypatch):
    """New gestion env var takes precedence over old starter."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_gestion_monthly_price_id", "price_gestion_new")
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_starter_old")
    result = resolve_price_id_for_plan(PlanKey.STARTER)
    assert result == "price_gestion_new"


def test_resolve_price_id_annual_starter(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_gestion_annual_price_id", "")
    monkeypatch.setattr(settings, "stripe_starter_annual_price_id", "price_starter_annual")
    result = resolve_price_id_for_plan(PlanKey.STARTER, billing_period="year")
    assert result == "price_starter_annual"


def test_resolve_price_id_monthly_default(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_gestion_monthly_price_id", "")
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_starter_monthly")
    result = resolve_price_id_for_plan(PlanKey.STARTER)
    assert result == "price_starter_monthly"


def test_resolve_plan_key_from_annual_price(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_pro_annual_price_id", "price_pro_annual")
    result = resolve_plan_key_from_price_id("price_pro_annual")
    assert result == PlanKey.PRO


def test_resolve_plan_key_fondateur(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_fondateur_price_id", "price_fondateur_test")
    result = resolve_plan_key_from_price_id("price_fondateur_test")
    assert result == PlanKey.FONDATEUR


def test_resolve_plan_key_trial():
    result = resolve_plan_key_from_price_id("trial")
    assert result == PlanKey.FREE


def test_resolve_price_id_lifetime_returns_none():
    result = resolve_price_id_for_plan(PlanKey.LIFETIME)
    assert result is None


def test_trial_expired_plan():
    plan = get_trial_expired_plan()
    assert plan.display_name == "Essai expiré"
    assert plan.max_scis == 0
    assert plan.max_biens == 0
    assert plan.cerfa_enabled is False
    assert plan.fiscalite_enabled is False
    assert plan.charges_enabled is False


def test_is_trial_active_within_window():
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    assert is_trial_active("trialing", future) is True


def test_is_trial_active_expired():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    assert is_trial_active("trialing", past) is False


def test_is_trial_active_wrong_status():
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    assert is_trial_active("active", future) is False


def test_is_trial_active_no_end_date():
    assert is_trial_active("trialing", None) is False


def test_is_trial_active_unix_timestamp():
    future_ts = (datetime.now(timezone.utc) + timedelta(days=7)).timestamp()
    assert is_trial_active("trialing", str(future_ts)) is True


def test_is_trial_active_invalid_value():
    assert is_trial_active("trialing", "not-a-date") is False
