from types import SimpleNamespace

import stripe

from app.api.v1 import stripe as stripe_api
from app.core.config import settings


def test_create_checkout_session(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_test")

    def fake_create(**kwargs):
        assert kwargs["line_items"][0]["price"] == "price_test"
        assert kwargs["mode"] == "subscription"
        assert kwargs["client_reference_id"] == "user-123"
        assert kwargs["metadata"]["plan_key"] == "starter"
        return SimpleNamespace(url="https://checkout.stripe.com/c/pay_test")

    monkeypatch.setattr("app.api.v1.stripe.stripe.checkout.Session.create", fake_create)

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"plan_key": "starter"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://checkout.stripe.com/c/pay_test"
    assert "session_id" in data


def test_create_checkout_session_without_url_fails(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_test")
    monkeypatch.setattr(
        "app.api.v1.stripe.stripe.checkout.Session.create",
        lambda **_kwargs: SimpleNamespace(url=None),
    )

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"plan_key": "starter"},
        headers=auth_headers,
    )
    assert response.status_code == 503
    assert "Checkout session URL unavailable" in response.json()["error"]


def test_create_checkout_session_stripe_error_fails(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_test")

    def fake_create(**_kwargs):
        raise stripe.error.StripeError("boom")

    monkeypatch.setattr("app.api.v1.stripe.stripe.checkout.Session.create", fake_create)

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"plan_key": "starter"},
        headers=auth_headers,
    )
    assert response.status_code == 503
    assert "Checkout session creation failed" in response.json()["error"]


def test_webhook_signature_invalid(client, monkeypatch):
    def fake_construct_event(*_args, **_kwargs):
        raise stripe.error.SignatureVerificationError(
            message="Invalid signature",
            sig_header="invalid",
            http_body=b"{}",
        )

    monkeypatch.setattr("app.api.v1.stripe.stripe.Webhook.construct_event", fake_construct_event)

    response = client.post(
        "/api/v1/stripe/webhook",
        data=b"{}",
        headers={"stripe-signature": "invalid"},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "Invalid Stripe signature"


def test_webhook_missing_signature_header(client):
    response = client.post("/api/v1/stripe/webhook", data=b"{}")
    assert response.status_code == 400
    assert response.json()["error"] == "Missing Stripe signature header"


def test_webhook_invalid_payload(client, monkeypatch):
    def fake_construct_event(*_args, **_kwargs):
        raise ValueError("payload is invalid")

    monkeypatch.setattr("app.api.v1.stripe.stripe.Webhook.construct_event", fake_construct_event)

    response = client.post(
        "/api/v1/stripe/webhook",
        data=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 400
    assert "Invalid Stripe payload" in response.json()["error"]


def test_handle_event_checkout_completed_syncs_active(monkeypatch):
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["session_data"] = session_data
        captured["status_value"] = status_value

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)

    stripe_api._handle_event(
        {
            "type": "checkout.session.completed",
            "data": {"object": {"payment_status": "paid", "client_reference_id": "user-1"}},
        }
    )
    assert captured["status_value"] == "active"
    assert captured["session_data"]["client_reference_id"] == "user-1"


def test_handle_event_subscription_deleted(monkeypatch):
    captured = {}

    def fake_sync_deleted(subscription_data):
        captured["subscription_data"] = subscription_data

    monkeypatch.setattr(stripe_api, "_sync_subscription_deleted", fake_sync_deleted)
    stripe_api._handle_event(
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_123", "customer": "cus_123"}},
        }
    )
    assert captured["subscription_data"]["id"] == "sub_123"


def test_handle_event_subscription_updated(monkeypatch):
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["session_data"] = session_data
        captured["status_value"] = status_value

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)
    stripe_api._handle_event(
        {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "past_due",
                    "metadata": {"user_id": "user-2"},
                    "items": {"data": [{"price": {"id": "price_123"}}]},
                }
            },
        }
    )
    assert captured["status_value"] == "past_due"
    assert captured["session_data"]["client_reference_id"] == "user-2"


def test_sync_subscription_with_service_client(monkeypatch):
    writes = {}

    class _Query:
        def upsert(self, payload, on_conflict):
            writes["payload"] = payload
            writes["on_conflict"] = on_conflict
            return self

        def execute(self):
            writes["executed"] = True
            return {}

    class _Client:
        def table(self, name):
            writes["table"] = name
            return _Query()

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())

    stripe_api._sync_subscription(
        {
            "client_reference_id": "user-3",
            "customer": "cus_3",
            "subscription": "sub_3",
            "price_id": "price_3",
            "mode": "subscription",
        },
        "active",
    )

    assert writes["table"] == "subscriptions"
    assert writes["on_conflict"] == "user_id"
    assert writes["payload"]["status"] == "active"
    assert writes["executed"] is True


def test_sync_subscription_deleted_with_service_client(monkeypatch):
    writes = {}

    class _Query:
        def update(self, payload):
            writes["payload"] = payload
            return self

        def eq(self, key, value):
            writes["eq"] = (key, value)
            return self

        def execute(self):
            writes["executed"] = True
            return {}

    class _Client:
        def table(self, name):
            writes["table"] = name
            return _Query()

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())

    stripe_api._sync_subscription_deleted({"id": "sub_7", "customer": "cus_7"})
    assert writes["table"] == "subscriptions"
    assert writes["payload"] == {"status": "canceled", "is_active": False}
    assert writes["eq"] == ("stripe_subscription_id", "sub_7")
    assert writes["executed"] is True


def test_get_subscription_returns_free_fallback(client, auth_headers, free_plan):
    response = client.get("/api/v1/stripe/subscription", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["plan_key"] == "free"
    assert payload["max_scis"] == 1
    assert payload["max_biens"] == 2


def test_create_checkout_session_feature_disabled(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "feature_stripe_payments", False)

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"plan_key": "starter"},
        headers=auth_headers,
    )
    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "feature_disabled"
    assert payload["details"]["flag"] == "feature_stripe_payments"


def test_guest_checkout_rejects_free_plan(client):
    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "free", "billing_period": "month"},
    )
    assert response.status_code == 400


def test_guest_checkout_rejects_invalid_plan(client):
    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "invalid", "billing_period": "month"},
    )
    assert response.status_code in (400, 422)


def test_guest_checkout_rejects_invalid_billing_period(client):
    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "starter", "billing_period": "weekly"},
    )
    assert response.status_code in (400, 422)


def test_guest_checkout_success(client, monkeypatch):
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_test")

    def fake_create(**kwargs):
        assert kwargs["line_items"][0]["price"] == "price_test"
        assert kwargs["mode"] == "subscription"
        assert kwargs["metadata"]["plan_key"] == "starter"
        assert "client_reference_id" not in kwargs
        return SimpleNamespace(url="https://checkout.stripe.com/c/pay_guest", id="cs_guest_123")

    monkeypatch.setattr("app.api.v1.stripe.stripe.checkout.Session.create", fake_create)

    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "starter", "billing_period": "month"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://checkout.stripe.com/c/pay_guest"
    assert data["session_id"] == "cs_guest_123"


def test_guest_checkout_feature_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_stripe_payments", False)

    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "starter", "billing_period": "month"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "feature_disabled"


def test_webhook_guest_checkout_creates_user(monkeypatch):
    """checkout.session.completed with no client_reference_id triggers user creation."""
    from app.api.v1.stripe import _find_user_by_email, _create_or_get_user, _update_subscription_metadata

    # Verify helpers are callable
    assert callable(_find_user_by_email)
    assert callable(_create_or_get_user)
    assert callable(_update_subscription_metadata)

    # Test the full guest checkout flow through _handle_event
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["session_data"] = session_data
        captured["status_value"] = status_value

    def fake_create_or_get(email):
        captured["email"] = email
        return "guest-user-42"

    def fake_update_metadata(sub_id, user_id, plan_key):
        captured["metadata_update"] = {"sub_id": sub_id, "user_id": user_id, "plan_key": plan_key}

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)
    monkeypatch.setattr(stripe_api, "_create_or_get_user", fake_create_or_get)
    monkeypatch.setattr(stripe_api, "_update_subscription_metadata", fake_update_metadata)

    stripe_api._handle_event(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "payment_status": "paid",
                    "client_reference_id": None,
                    "customer_details": {"email": "guest@example.com"},
                    "subscription": "sub_guest_1",
                    "metadata": {"plan_key": "starter"},
                }
            },
        }
    )

    assert captured["email"] == "guest@example.com"
    assert captured["session_data"]["client_reference_id"] == "guest-user-42"
    assert captured["status_value"] == "active"
    assert captured["metadata_update"]["sub_id"] == "sub_guest_1"
    assert captured["metadata_update"]["user_id"] == "guest-user-42"
    assert captured["metadata_update"]["plan_key"] == "starter"


def test_webhook_guest_checkout_no_email_returns_early(monkeypatch):
    """Guest checkout without email should return without syncing."""
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["called"] = True

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)

    stripe_api._handle_event(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "payment_status": "paid",
                    "client_reference_id": None,
                    "customer_details": {},
                }
            },
        }
    )

    assert "called" not in captured


def test_webhook_subscription_updated_fallback_resolution(monkeypatch):
    """subscription.updated with no metadata.user_id resolves via stripe_customer_id."""
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["session_data"] = session_data
        captured["status_value"] = status_value

    class _Query:
        def select(self, *args):
            return self

        def eq(self, key, value):
            captured["eq"] = (key, value)
            return self

        def limit(self, n):
            return self

        def execute(self):
            return SimpleNamespace(data=[{"user_id": "resolved-user-99"}])

    class _Client:
        def table(self, name):
            return _Query()

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)
    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())

    stripe_api._handle_event(
        {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_456",
                    "customer": "cus_456",
                    "status": "active",
                    "metadata": {},
                    "items": {"data": [{"price": {"id": "price_456"}}]},
                }
            },
        }
    )

    assert captured["session_data"]["client_reference_id"] == "resolved-user-99"
    assert captured["eq"] == ("stripe_customer_id", "cus_456")


def test_webhook_ignored_when_stripe_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_stripe_payments", False)

    response = client.post(
        "/api/v1/stripe/webhook",
        data=b"{}",
        headers={"stripe-signature": "ignored"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


def test_find_user_by_email_found(monkeypatch):
    """_find_user_by_email returns user id when email matches."""

    class _User:
        email = "found@example.com"
        id = "uid-42"

    class _ListResult:
        users = [_User()]

    class _Admin:
        def list_users(self):
            return _ListResult()

    class _Auth:
        admin = _Admin()

    class _Client:
        auth = _Auth()

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())
    assert stripe_api._find_user_by_email("found@example.com") == "uid-42"


def test_find_user_by_email_not_found(monkeypatch):
    """_find_user_by_email returns None when no user matches."""

    class _User:
        email = "other@example.com"
        id = "uid-99"

    class _ListResult:
        users = [_User()]

    class _Admin:
        def list_users(self):
            return _ListResult()

    class _Auth:
        admin = _Admin()

    class _Client:
        auth = _Auth()

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())
    assert stripe_api._find_user_by_email("missing@example.com") is None


def test_find_user_by_email_exception(monkeypatch):
    """_find_user_by_email returns None on exception."""

    def _boom():
        raise RuntimeError("auth down")

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", _boom)
    assert stripe_api._find_user_by_email("x@example.com") is None


def test_create_or_get_user_existing(monkeypatch):
    """_create_or_get_user returns existing user id."""
    monkeypatch.setattr(stripe_api, "_find_user_by_email", lambda _email: "existing-uid")
    assert stripe_api._create_or_get_user("x@example.com") == "existing-uid"


def test_create_or_get_user_creates_new(monkeypatch):
    """_create_or_get_user creates a new user when not found."""
    monkeypatch.setattr(stripe_api, "_find_user_by_email", lambda _email: None)

    class _User:
        id = "new-uid-77"

    class _Result:
        user = _User()

    class _Admin:
        def create_user(self, payload):
            return _Result()

    class _Auth:
        admin = _Admin()

    class _Client:
        auth = _Auth()

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())
    assert stripe_api._create_or_get_user("new@example.com") == "new-uid-77"


def test_create_or_get_user_create_fails(monkeypatch):
    """_create_or_get_user returns None when creation fails."""
    monkeypatch.setattr(stripe_api, "_find_user_by_email", lambda _email: None)

    def _boom():
        raise RuntimeError("create failed")

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", _boom)
    assert stripe_api._create_or_get_user("fail@example.com") is None


def test_create_or_get_user_no_user_attr(monkeypatch):
    """_create_or_get_user returns None when result has no user."""
    monkeypatch.setattr(stripe_api, "_find_user_by_email", lambda _email: None)

    class _Result:
        user = None

    class _Admin:
        def create_user(self, payload):
            return _Result()

    class _Auth:
        admin = _Admin()

    class _Client:
        auth = _Auth()

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", lambda: _Client())
    assert stripe_api._create_or_get_user("no-user@example.com") is None


def test_update_subscription_metadata_success(monkeypatch):
    """_update_subscription_metadata calls Stripe modify."""
    captured = {}

    def fake_modify(sub_id, metadata=None):
        captured["sub_id"] = sub_id
        captured["metadata"] = metadata

    monkeypatch.setattr("app.api.v1.stripe.stripe.Subscription.modify", fake_modify)
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")

    stripe_api._update_subscription_metadata("sub_1", "uid_1", "pro")
    assert captured["sub_id"] == "sub_1"
    assert captured["metadata"]["user_id"] == "uid_1"
    assert captured["metadata"]["plan_key"] == "pro"


def test_update_subscription_metadata_no_plan_key(monkeypatch):
    """_update_subscription_metadata omits plan_key when None."""
    captured = {}

    def fake_modify(sub_id, metadata=None):
        captured["metadata"] = metadata

    monkeypatch.setattr("app.api.v1.stripe.stripe.Subscription.modify", fake_modify)
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")

    stripe_api._update_subscription_metadata("sub_2", "uid_2", None)
    assert "plan_key" not in captured["metadata"]
    assert captured["metadata"]["user_id"] == "uid_2"


def test_update_subscription_metadata_exception(monkeypatch):
    """_update_subscription_metadata swallows exceptions."""

    def fake_modify(sub_id, metadata=None):
        raise RuntimeError("stripe down")

    monkeypatch.setattr("app.api.v1.stripe.stripe.Subscription.modify", fake_modify)
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")

    # Should not raise
    stripe_api._update_subscription_metadata("sub_3", "uid_3", "starter")


def test_sync_subscription_exception_path(monkeypatch):
    """_sync_subscription logs warning when DB fails."""

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", _boom)

    # Should not raise
    stripe_api._sync_subscription(
        {"client_reference_id": "user-1", "customer": "cus_1"},
        "active",
    )


def test_sync_subscription_deleted_exception_path(monkeypatch):
    """_sync_subscription_deleted logs warning when DB fails."""

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", _boom)

    # Should not raise
    stripe_api._sync_subscription_deleted({"id": "sub_99", "customer": "cus_99"})


def test_sync_subscription_no_user_id_returns_early(monkeypatch):
    """_sync_subscription returns early when client_reference_id is None."""
    called = {"sync": False}

    def fake_client():
        called["sync"] = True

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", fake_client)

    stripe_api._sync_subscription({"client_reference_id": None}, "active")
    assert not called["sync"]


def test_sync_subscription_deleted_no_ids_returns_early(monkeypatch):
    """_sync_subscription_deleted returns early when no customer or sub id."""
    called = {"sync": False}

    def fake_client():
        called["sync"] = True

    monkeypatch.setattr(stripe_api, "get_supabase_service_client", fake_client)

    stripe_api._sync_subscription_deleted({})
    assert not called["sync"]


def test_handle_event_unknown_type(monkeypatch):
    """_handle_event ignores unknown event types."""
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["called"] = True

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)

    stripe_api._handle_event({"type": "charge.refunded", "data": {"object": {}}})
    assert "called" not in captured


def test_handle_event_non_dict_obj(monkeypatch):
    """_handle_event handles dict-like object via dict() conversion."""
    captured = {}

    def fake_sync(session_data, status_value, **_kwargs):
        captured["status_value"] = status_value

    monkeypatch.setattr(stripe_api, "_sync_subscription", fake_sync)

    # Use a class that supports dict() conversion (iterable of key-value pairs)
    class DictLikeObj:
        def __init__(self):
            self._data = {
                "payment_status": "paid",
                "client_reference_id": "user-ns",
            }

        def __iter__(self):
            return iter(self._data.items())

        def keys(self):
            return self._data.keys()

        def __getitem__(self, key):
            return self._data[key]

    stripe_api._handle_event(
        {
            "type": "checkout.session.completed",
            "data": {"object": DictLikeObj()},
        }
    )
    assert captured["status_value"] == "active"


def test_webhook_valid_event_processed(client, monkeypatch):
    """Webhook with valid signature processes event and returns success."""
    monkeypatch.setattr(
        "app.api.v1.stripe.stripe.Webhook.construct_event",
        lambda **_kwargs: {"type": "invoice.payment_succeeded", "data": {"object": {}}},
    )

    response = client.post(
        "/api/v1/stripe/webhook",
        data=b'{"type": "invoice.payment_succeeded"}',
        headers={"stripe-signature": "valid_sig"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_guest_checkout_stripe_error(client, monkeypatch):
    """Guest checkout returns 503 on Stripe error."""
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_test")

    def fake_create(**_kwargs):
        raise stripe.error.StripeError("boom")

    monkeypatch.setattr("app.api.v1.stripe.stripe.checkout.Session.create", fake_create)

    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "starter", "billing_period": "month"},
    )
    assert response.status_code == 503
    assert "Checkout session creation failed" in response.json()["error"]


def test_guest_checkout_no_url(client, monkeypatch):
    """Guest checkout returns 503 when session has no URL."""
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_test")

    monkeypatch.setattr(
        "app.api.v1.stripe.stripe.checkout.Session.create",
        lambda **_kwargs: SimpleNamespace(url=None, id="cs_no_url"),
    )

    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "starter", "billing_period": "month"},
    )
    assert response.status_code == 503
    assert "Checkout session URL unavailable" in response.json()["error"]


def test_checkout_catalog_disabled(client, auth_headers, monkeypatch):
    """Checkout fails when catalog feature flag is disabled."""
    monkeypatch.setattr(settings, "feature_stripe_payments", True)
    monkeypatch.setattr(settings, "feature_new_checkout_catalog", False)

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"plan_key": "starter"},
        headers=auth_headers,
    )
    assert response.status_code == 503
    assert response.json()["code"] == "feature_disabled"
