"""Tests for plan entitlements catalog and helper functions."""

from app.core.entitlements import (
    PlanKey,
    get_plan,
    list_public_plans,
    resolve_plan_key_from_price_id,
    resolve_price_id_for_plan,
)


def test_free_plan_is_blocked():
    """FREE plan is a blocked non-subscriber state (payment-first model)."""
    plan = get_plan(PlanKey.FREE)
    assert plan.is_public is False
    assert plan.display_name == "Non abonné"
    assert plan.max_scis == 0
    assert plan.max_biens == 0
    # No features enabled
    assert plan.cerfa_enabled is False
    assert plan.fiscalite_enabled is False
    assert plan.charges_enabled is False
    assert plan.associes_enabled is False


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


def test_get_plan_none_returns_free():
    """When plan_key is None (new user, no subscription resolved yet), fall back to FREE."""
    plan = get_plan(None)
    assert plan.plan_key == PlanKey.FREE
    assert plan.max_scis == 0


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


def test_resolve_plan_key_unknown_falls_back_to_free():
    """Unknown price_id falls back to FREE."""
    result = resolve_plan_key_from_price_id("price_unknown_xyz")
    assert result == PlanKey.FREE


def test_resolve_price_id_lifetime_returns_none_when_only_placeholder(monkeypatch):
    """When env vars are still placeholders, lifetime resolution must return None
    so callers raise a clear 'Price ID unavailable' error rather than passing a
    fake id to Stripe."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_lifetime_price_id", "price_lifetime_placeholder")
    monkeypatch.setattr(settings, "stripe_fondateur_price_id", "price_fondateur_placeholder")
    result = resolve_price_id_for_plan(PlanKey.LIFETIME)
    assert result is None


def test_resolve_price_id_lifetime_uses_dedicated_env(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_lifetime_price_id", "price_lifetime_real")
    monkeypatch.setattr(settings, "stripe_fondateur_price_id", "price_fondateur_real")
    result = resolve_price_id_for_plan(PlanKey.LIFETIME)
    assert result == "price_lifetime_real"


def test_resolve_price_id_lifetime_falls_back_to_fondateur(monkeypatch):
    """If no dedicated lifetime price is configured, fall back to fondateur."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_lifetime_price_id", "price_lifetime_placeholder")
    monkeypatch.setattr(settings, "stripe_fondateur_price_id", "price_fondateur_real")
    result = resolve_price_id_for_plan(PlanKey.LIFETIME)
    assert result == "price_fondateur_real"


def test_resolve_price_id_lifetime_accepts_string_plan_key(monkeypatch):
    """resolve_price_id_for_plan must accept the literal string 'lifetime'
    (this is what the pricing page sends)."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_lifetime_price_id", "price_lifetime_real")
    result = resolve_price_id_for_plan("lifetime")
    assert result == "price_lifetime_real"


def test_resolve_plan_key_lifetime(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_lifetime_price_id", "price_lifetime_real")
    result = resolve_plan_key_from_price_id("price_lifetime_real")
    assert result == PlanKey.LIFETIME
