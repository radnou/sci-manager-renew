"""Tests for the notifications API endpoints."""

from __future__ import annotations

import pytest


BASE_URL = "/api/v1/notifications"


@pytest.fixture
def seed_notifications(fake_supabase):
    """Insert sample notifications into the fake store."""
    notifications = [
        {
            "id": "notif-1",
            "user_id": "user-123",
            "type": "loyer",
            "title": "Loyer recu",
            "message": "Le loyer de janvier a ete enregistre.",
            "metadata": {},
            "read_at": None,
            "created_at": "2026-01-15T10:00:00+00:00",
        },
        {
            "id": "notif-2",
            "user_id": "user-123",
            "type": "charge",
            "title": "Nouvelle charge",
            "message": "Une charge a ete ajoutee.",
            "metadata": {},
            "read_at": "2026-01-16T08:00:00+00:00",
            "created_at": "2026-01-14T09:00:00+00:00",
        },
        {
            "id": "notif-3",
            "user_id": "user-123",
            "type": "document",
            "title": "Document genere",
            "message": "La quittance est prete.",
            "metadata": {},
            "read_at": None,
            "created_at": "2026-01-16T12:00:00+00:00",
        },
        {
            "id": "notif-other",
            "user_id": "user-456",
            "type": "loyer",
            "title": "Autre user",
            "message": "Notification pour un autre user.",
            "metadata": {},
            "read_at": None,
            "created_at": "2026-01-15T10:00:00+00:00",
        },
    ]
    fake_supabase.store["notifications"] = notifications
    return notifications


# ---------------------------------------------------------------
# GET /api/v1/notifications/
# ---------------------------------------------------------------


class TestListNotifications:
    def test_list_notifications_empty(self, client, auth_headers, fake_supabase):
        """User with no notifications gets an empty list."""
        fake_supabase.store["notifications"] = []

        resp = client.get(BASE_URL + "/", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_notifications_with_data(self, client, auth_headers, seed_notifications):
        """Returns all notifications for the authenticated user."""
        resp = client.get(BASE_URL + "/", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        # user-123 has 3 notifications; notif-other belongs to user-456
        assert len(data) == 3
        returned_ids = {n["id"] for n in data}
        assert returned_ids == {"notif-1", "notif-2", "notif-3"}

    def test_list_notifications_ordered_by_created_at_desc(
        self, client, auth_headers, seed_notifications
    ):
        """Notifications are returned newest first."""
        resp = client.get(BASE_URL + "/", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        dates = [n["created_at"] for n in data]
        assert dates == sorted(dates, reverse=True)

    def test_list_notifications_unread_only(self, client, auth_headers, seed_notifications):
        """With unread_only=true, only notifications where read_at is null are returned."""
        resp = client.get(
            BASE_URL + "/",
            headers=auth_headers,
            params={"unread_only": "true"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        returned_ids = {n["id"] for n in data}
        assert returned_ids == {"notif-1", "notif-3"}
        for n in data:
            assert n["read_at"] is None

    def test_list_notifications_with_limit(self, client, auth_headers, seed_notifications):
        """Limit parameter restricts the number of returned notifications."""
        resp = client.get(
            BASE_URL + "/",
            headers=auth_headers,
            params={"limit": 1},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_list_notifications_unauthenticated(self, client):
        """Request without auth headers returns 401."""
        resp = client.get(BASE_URL + "/")
        assert resp.status_code == 401


# ---------------------------------------------------------------
# GET /api/v1/notifications/count
# ---------------------------------------------------------------


class TestUnreadCount:
    def test_unread_count_zero(self, client, auth_headers, fake_supabase):
        """No notifications yields count=0."""
        fake_supabase.store["notifications"] = []

        resp = client.get(BASE_URL + "/count", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json() == {"count": 0}

    def test_unread_count_with_unread(self, client, auth_headers, seed_notifications):
        """Count reflects only unread notifications for the current user."""
        resp = client.get(BASE_URL + "/count", headers=auth_headers)

        assert resp.status_code == 200
        # user-123 has 2 unread (notif-1 and notif-3)
        assert resp.json() == {"count": 2}

    def test_unread_count_all_read(self, client, auth_headers, fake_supabase):
        """When all notifications are read, count is 0."""
        fake_supabase.store["notifications"] = [
            {
                "id": "notif-read",
                "user_id": "user-123",
                "type": "loyer",
                "title": "Loyer",
                "message": "Already read",
                "metadata": {},
                "read_at": "2026-01-16T08:00:00+00:00",
                "created_at": "2026-01-15T10:00:00+00:00",
            },
        ]

        resp = client.get(BASE_URL + "/count", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json() == {"count": 0}

    def test_unread_count_unauthenticated(self, client):
        """Request without auth headers returns 401."""
        resp = client.get(BASE_URL + "/count")
        assert resp.status_code == 401


# ---------------------------------------------------------------
# PATCH /api/v1/notifications/{notification_id}/read
# ---------------------------------------------------------------


class TestMarkAsRead:
    def test_mark_as_read(self, client, auth_headers, seed_notifications, fake_supabase):
        """Marking an unread notification sets read_at."""
        resp = client.patch(BASE_URL + "/notif-1/read", headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "notif-1"
        assert body["read_at"] is not None

        # Verify the store was updated
        row = next(
            n for n in fake_supabase.store["notifications"] if n["id"] == "notif-1"
        )
        assert row["read_at"] is not None

    def test_mark_as_read_not_found(self, client, auth_headers, fake_supabase):
        """Non-existent notification returns 404."""
        fake_supabase.store["notifications"] = []

        resp = client.patch(BASE_URL + "/nonexistent-id/read", headers=auth_headers)

        assert resp.status_code == 404

    def test_mark_as_read_other_user(self, client, auth_headers, seed_notifications):
        """Cannot mark another user's notification as read (returns 404)."""
        resp = client.patch(BASE_URL + "/notif-other/read", headers=auth_headers)

        assert resp.status_code == 404

    def test_mark_as_read_unauthenticated(self, client):
        """Request without auth headers returns 401."""
        resp = client.patch(BASE_URL + "/notif-1/read")
        assert resp.status_code == 401


# ---------------------------------------------------------------
# PATCH /api/v1/notifications/read-all
# ---------------------------------------------------------------


class TestMarkAllAsRead:
    def test_mark_all_as_read(self, client, auth_headers, seed_notifications, fake_supabase):
        """All unread notifications for the user are marked as read."""
        resp = client.patch(BASE_URL + "/read-all", headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["updated"] == 2  # notif-1 and notif-3 were unread

        # Verify all user-123 notifications now have read_at set
        user_notifs = [
            n for n in fake_supabase.store["notifications"]
            if n["user_id"] == "user-123"
        ]
        for n in user_notifs:
            assert n["read_at"] is not None

    def test_mark_all_as_read_none_unread(self, client, auth_headers, fake_supabase):
        """When no unread notifications exist, updated count is 0."""
        fake_supabase.store["notifications"] = [
            {
                "id": "notif-read",
                "user_id": "user-123",
                "type": "loyer",
                "title": "Loyer",
                "message": "Already read",
                "metadata": {},
                "read_at": "2026-01-16T08:00:00+00:00",
                "created_at": "2026-01-15T10:00:00+00:00",
            },
        ]

        resp = client.patch(BASE_URL + "/read-all", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json() == {"updated": 0}

    def test_mark_all_as_read_does_not_affect_other_users(
        self, client, auth_headers, seed_notifications, fake_supabase
    ):
        """Other user's notifications remain unread."""
        client.patch(BASE_URL + "/read-all", headers=auth_headers)

        other_notif = next(
            n for n in fake_supabase.store["notifications"]
            if n["id"] == "notif-other"
        )
        assert other_notif["read_at"] is None

    def test_mark_all_as_read_unauthenticated(self, client):
        """Request without auth headers returns 401."""
        resp = client.patch(BASE_URL + "/read-all")
        assert resp.status_code == 401
