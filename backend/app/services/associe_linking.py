"""Auto-link associe records to users based on email match.

When a user logs in or completes onboarding, any `associes` records that
match their email but have no `user_id` are automatically claimed.  This
enables the multi-user invitation flow: a gerant creates an associe with
an email, and when that person signs up they gain access to the SCI.
"""

import structlog

from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)


def link_user_to_pending_associes(user_id: str, email: str) -> int:
    """Find associes with matching email and no user_id, link them.

    Uses the service-role client to bypass RLS so we can update records
    that the user cannot yet see (they have no user_id claim on them).

    Returns the number of records linked.
    """
    if not user_id or not email:
        return 0

    client = get_supabase_service_client()

    # Find unlinked associes with this email (case-insensitive match)
    email_lower = email.strip().lower()
    result = (
        client.table("associes")
        .select("id")
        .ilike("email", email_lower)
        .is_("user_id", "null")
        .execute()
    )

    if not result.data:
        return 0

    linked = 0
    for record in result.data:
        try:
            update_result = (
                client.table("associes")
                .update({"user_id": user_id})
                .eq("id", record["id"])
                .is_("user_id", "null")  # Guard: only update if still unlinked
                .execute()
            )
            if update_result.data:
                linked += 1
        except Exception:
            logger.warning(
                "associe_link_failed",
                user_id=user_id,
                associe_id=record["id"],
                exc_info=True,
            )

    if linked:
        logger.info(
            "associes_auto_linked",
            user_id=user_id,
            email=email_lower,
            count=linked,
        )

    return linked
