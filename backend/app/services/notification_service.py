from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

logger = structlog.get_logger(__name__)

DEDUP_WINDOW_DAYS = 7


def _find_duplicate(supabase_client, user_id: str, notification_type: str, dedup_key: str | None) -> bool:
    """Check if a notification with the same dedup_key exists within the last 7 days.

    Returns True if a duplicate is found (meaning we should skip creation).
    Checks ALL notifications (read or unread) to prevent re-creation after dismissal.
    """
    if not dedup_key:
        return False

    cutoff = (datetime.now(timezone.utc) - timedelta(days=DEDUP_WINDOW_DAYS)).isoformat()

    result = (
        supabase_client.table("notifications")
        .select("id, metadata")
        .eq("user_id", user_id)
        .eq("type", notification_type)
        .gte("created_at", cutoff)
        .execute()
    )

    for row in result.data or []:
        meta = row.get("metadata") or {}
        if meta.get("dedup_key") == dedup_key:
            return True

    return False


async def create_notification_with_email(
    supabase_client,
    user_id: str,
    notification_type: str,
    data: dict,
) -> bool:
    """
    Create an in-app notification and/or send an email depending on user preferences.

    Returns True if a notification was created, False if deduplicated/skipped.

    1. Dedup check: skip if identical notification exists (unread, last 7 days)
    2. Check user's preferences for this notification_type
    3. If in_app_enabled: insert into notifications table
    4. If email_enabled: send email via Resend
    """
    # 0. Deduplication check
    metadata = data.get("metadata") or {}
    dedup_key = metadata.get("dedup_key")
    if _find_duplicate(supabase_client, user_id, notification_type, dedup_key):
        logger.info(
            "notification_deduplicated",
            user_id=user_id,
            notification_type=notification_type,
            dedup_key=dedup_key,
        )
        return False

    # 1. Fetch user preferences for this type
    result = (
        supabase_client.table("notification_preferences")
        .select("email_enabled, in_app_enabled")
        .eq("user_id", user_id)
        .eq("type", notification_type)
        .execute()
    )

    # Default: both enabled if no preference row exists
    if result.data:
        pref = result.data[0]
        email_enabled = pref["email_enabled"]
        in_app_enabled = pref["in_app_enabled"]
    else:
        email_enabled = True
        in_app_enabled = True

    # 2. Create in-app notification
    if in_app_enabled:
        try:
            supabase_client.table("notifications").insert(
                {
                    "user_id": user_id,
                    "type": notification_type,
                    "title": data.get("title", "Notification"),
                    "message": data.get("message", ""),
                    "metadata": data.get("metadata", {}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
            logger.info(
                "in_app_notification_created",
                user_id=user_id,
                notification_type=notification_type,
            )
        except Exception:
            logger.error(
                "in_app_notification_failed",
                user_id=user_id,
                notification_type=notification_type,
                exc_info=True,
            )

    # 3. Send email notification
    if email_enabled:
        try:
            from app.core.supabase_client import get_supabase_service_client
            from app.services.email_service import email_service

            # Resolve user email from Supabase Auth
            service_client = get_supabase_service_client()
            user_resp = service_client.auth.admin.get_user_by_id(user_id)
            user_email = getattr(user_resp, "user", user_resp)
            email_addr = getattr(user_email, "email", None)

            if not email_addr:
                logger.warning(
                    "email_notification_skipped_no_email",
                    user_id=user_id,
                )
            else:
                await email_service.send_notification_email(
                    email=email_addr,
                    title=data.get("title", "Notification"),
                    message=data.get("message", ""),
                    notification_type=notification_type,
                )
                logger.info(
                    "email_notification_sent",
                    user_id=user_id,
                    notification_type=notification_type,
                )
        except Exception:
            logger.error(
                "email_notification_failed",
                user_id=user_id,
                notification_type=notification_type,
                exc_info=True,
            )

    return True
