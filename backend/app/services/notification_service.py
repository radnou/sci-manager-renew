from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


async def create_notification_with_email(
    supabase_client,
    user_id: str,
    notification_type: str,
    data: dict,
) -> None:
    """
    Create an in-app notification and/or send an email depending on user preferences.

    1. Check user's preferences for this notification_type
    2. If in_app_enabled: insert into notifications table
    3. If email_enabled: send email via Resend
    """
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
            from app.services.email_service import send_notification_email

            await send_notification_email(
                user_id=user_id,
                notification_type=notification_type,
                data=data,
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
