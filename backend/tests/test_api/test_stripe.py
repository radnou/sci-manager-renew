from types import SimpleNamespace

import stripe

from app.api.v1 import stripe as stripe_api


def test_create_checkout_session(client, auth_headers, monkeypatch):
    def fake_create(**kwargs):
        assert kwargs["line_items"][0]["price"] == "price_test"
        assert kwargs["mode"] == "subscription"
        assert kwargs["client_reference_id"] == "user-123"
        return SimpleNamespace(url="https://checkout.stripe.com/c/pay_test")

    monkeypatch.setattr("app.api.v1.stripe.stripe.checkout.Session.create", fake_create)

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"price_id": "price_test"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"url": "https://checkout.stripe.com/c/pay_test"}


def test_create_checkout_session_without_url_fails(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.stripe.stripe.checkout.Session.create",
        lambda **_kwargs: SimpleNamespace(url=None),
    )

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"price_id": "price_test"},
        headers=auth_headers,
    )
    assert response.status_code == 503
    assert "Checkout session URL unavailable" in response.json()["error"]


def test_create_checkout_session_stripe_error_fails(client, auth_headers, monkeypatch):
    def fake_create(**_kwargs):
        raise stripe.error.StripeError("boom")

    monkeypatch.setattr("app.api.v1.stripe.stripe.checkout.Session.create", fake_create)

    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        json={"price_id": "price_test"},
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
    assert response.json()["detail"] == "Invalid Stripe signature"


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

    def fake_sync(session_data, status_value):
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

    def fake_sync(session_data, status_value):
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
    assert writes["payload"] == {"status": "canceled"}
    assert writes["eq"] == ("stripe_subscription_id", "sub_7")
    assert writes["executed"] is True
