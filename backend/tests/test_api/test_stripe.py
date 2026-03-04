from types import SimpleNamespace

import stripe


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

