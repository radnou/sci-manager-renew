"""Tests for lead capture endpoint."""

import pytest


def test_capture_lead_success(client, fake_supabase):
    """POST /api/v1/leads/capture stores lead and returns 200."""
    response = client.post(
        "/api/v1/leads/capture",
        json={
            "email": "test@example.com",
            "source": "simulateur-cerfa",
            "utm_source": "google",
            "utm_medium": "cpc",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "captured"

    # Verify data was stored in fake_supabase
    leads = fake_supabase.store.get("lead_captures", [])
    assert len(leads) == 1
    assert leads[0]["email"] == "test@example.com"
    assert leads[0]["source"] == "simulateur-cerfa"


def test_capture_lead_invalid_email(client):
    """Invalid email returns 422."""
    response = client.post(
        "/api/v1/leads/capture",
        json={"email": "not-an-email", "source": "test"},
    )
    assert response.status_code == 422


def test_capture_lead_minimal(client, fake_supabase):
    """Minimal payload (just email) works."""
    response = client.post(
        "/api/v1/leads/capture",
        json={"email": "minimal@test.fr"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "captured"
