from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from app.core.supabase_client import get_supabase_service_client
from app.core.exceptions import DatabaseError
from app.core.security import get_current_user
from app.schemas.notification_preferences import (
    NotificationPreference,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["notifications"])

DEFAULT_NOTIFICATION_TYPES = [
    "late_payment",
    "bail_expiring",
    "quittance_pending",
    "pno_expiring",
    "new_loyer",
    "new_associe",
    "subscription_expiring",
]


def _get_client():
    return get_supabase_service_client()


def _build_defaults() -> list[NotificationPreference]:
    return [
        NotificationPreference(type=t, email_enabled=True, in_app_enabled=True)
        for t in DEFAULT_NOTIFICATION_TYPES
    ]


@router.get("/notification-preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    user_id: str = Depends(get_current_user),
):
    """Return the current user's notification preferences, with defaults for missing types."""
    client = _get_client()

    result = (
        client.table("notification_preferences")
        .select("type, email_enabled, in_app_enabled")
        .eq("user_id", user_id)
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    saved: dict[str, NotificationPreference] = {}
    for row in result.data or []:
        saved[row["type"]] = NotificationPreference(
            type=row["type"],
            email_enabled=row["email_enabled"],
            in_app_enabled=row["in_app_enabled"],
        )

    # Merge with defaults so every type is always present
    preferences: list[NotificationPreference] = []
    for t in DEFAULT_NOTIFICATION_TYPES:
        if t in saved:
            preferences.append(saved[t])
        else:
            preferences.append(NotificationPreference(type=t, email_enabled=True, in_app_enabled=True))

    return NotificationPreferencesResponse(preferences=preferences)


@router.put("/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    body: NotificationPreferencesUpdate,
    user_id: str = Depends(get_current_user),
):
    """Bulk upsert notification preferences for the current user."""
    client = _get_client()

    rows = [
        {
            "user_id": user_id,
            "type": pref.type,
            "email_enabled": pref.email_enabled,
            "in_app_enabled": pref.in_app_enabled,
        }
        for pref in body.preferences
        if pref.type in DEFAULT_NOTIFICATION_TYPES
    ]

    if rows:
        result = (
            client.table("notification_preferences")
            .upsert(rows, on_conflict="user_id,type")
            .execute()
        )

        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

    logger.info(
        "notification_preferences_updated",
        user_id=user_id,
        count=len(rows),
    )

    # Return the full set including defaults for any missing types
    return await get_notification_preferences(user_id=user_id)
