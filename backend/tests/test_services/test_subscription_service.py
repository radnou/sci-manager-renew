import pytest

from app.core.exceptions import PlanLimitError, SubscriptionInactiveError, UpgradeRequiredError
from app.services.subscription_service import SubscriptionService


class _Result:
    def __init__(self, data, count=None):
        self.data = data
        self.count = len(data) if count is None else count


class _Query:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self.filters = []
        self._count = None

    def select(self, *_args, count=None, **_kwargs):
        self._count = count
        return self

    def eq(self, key, value):
        self.filters.append((key, str(value)))
        return self

    def in_(self, key, values):
        self.filters.append((key, {str(value) for value in values}))
        return self

    def execute(self):
        rows = self.store.get(self.table_name, [])
        filtered = []
        for row in rows:
            keep = True
            for key, value in self.filters:
                if isinstance(value, set):
                    if str(row.get(key)) not in value:
                        keep = False
                        break
                elif str(row.get(key)) != value:
                    keep = False
                    break
            if keep:
                filtered.append(row)
        return _Result(filtered, count=len(filtered))


class _Client:
    def __init__(self, store):
        self.store = store

    def table(self, name):
        return _Query(self.store, name)


def build_store():
    return {
        "subscriptions": [],
        "associes": [{"id_sci": "sci-1", "user_id": "user-123"}],
        "biens": [
            {"id": "bien-1", "id_sci": "sci-1"},
            {"id": "bien-2", "id_sci": "sci-1"},
        ],
    }


def patch_client(monkeypatch, store):
    monkeypatch.setattr(
        "app.services.subscription_service.get_supabase_service_client",
        lambda: _Client(store),
    )


def test_get_subscription_summary_defaults_to_free(monkeypatch):
    store = build_store()
    patch_client(monkeypatch, store)

    summary = SubscriptionService.get_subscription_summary("user-123")
    assert summary["plan_key"] == "free"
    assert summary["max_scis"] == 1
    assert summary["max_biens"] == 2
    assert summary["current_scis"] == 1
    assert summary["current_biens"] == 2


def test_enforce_limit_raises_when_enforcement_active(monkeypatch):
    store = build_store()
    patch_client(monkeypatch, store)
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "enforce",
    )

    with pytest.raises(PlanLimitError):
        SubscriptionService.enforce_limit("user-123", "biens")


def test_enforce_limit_warn_mode_allows_request(monkeypatch):
    store = build_store()
    patch_client(monkeypatch, store)
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "warn",
    )

    summary = SubscriptionService.enforce_limit("user-123", "biens")
    assert summary["plan_key"] == "free"


def test_inactive_subscription_can_be_bypassed_in_observe_mode(monkeypatch):
    store = build_store()
    store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "past_due",
            "is_active": False,
            "max_scis": 10,
            "max_biens": 20,
            "features": {"multi_sci_enabled": True},
        }
    ]
    patch_client(monkeypatch, store)
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "observe",
    )

    summary = SubscriptionService.enforce_limit("user-123", "biens")
    assert summary["plan_key"] == "pro"


def test_inactive_subscription_raises_when_enforced(monkeypatch):
    store = build_store()
    store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "past_due",
            "is_active": False,
            "max_scis": 10,
            "max_biens": 20,
            "features": {"multi_sci_enabled": True},
        }
    ]
    patch_client(monkeypatch, store)
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "enforce",
    )

    with pytest.raises(SubscriptionInactiveError):
        SubscriptionService.enforce_limit("user-123", "biens")


def test_ensure_feature_enabled_raises_for_missing_feature(monkeypatch):
    store = build_store()
    store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 1,
            "max_biens": 5,
            "features": {"multi_sci_enabled": False},
        }
    ]
    patch_client(monkeypatch, store)
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "enforce",
    )

    with pytest.raises(UpgradeRequiredError):
        SubscriptionService.ensure_feature_enabled("user-123", "multi_sci_enabled")


def test_ensure_feature_enabled_warn_mode_allows(monkeypatch):
    store = build_store()
    store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 1,
            "max_biens": 5,
            "features": {"multi_sci_enabled": False},
        }
    ]
    patch_client(monkeypatch, store)
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "warn",
    )

    summary = SubscriptionService.ensure_feature_enabled("user-123", "multi_sci_enabled")
    assert summary["plan_key"] == "starter"
