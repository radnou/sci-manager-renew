"""
Onboarding API — tracks onboarding wizard progress.

GET  /api/v1/onboarding        → current status
POST /api/v1/onboarding/complete → mark onboarding as completed
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_service_client

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
logger = structlog.get_logger(__name__)


class OnboardingStatus(BaseModel):
    completed: bool
    sci_created: bool
    bien_created: bool
    bail_created: bool
    notifications_set: bool


class OnboardingCompleteResponse(BaseModel):
    completed: bool


def _check_onboarding_progress(user_id: str) -> OnboardingStatus:
    """Check real progress based on existing data."""
    client = get_supabase_service_client()

    # Check onboarding_completed flag
    sub_result = (
        client.table("subscriptions")
        .select("onboarding_completed")
        .eq("user_id", user_id)
        .execute()
    )
    completed = False
    if sub_result.data:
        completed = bool(sub_result.data[0].get("onboarding_completed", False))

    # Check if user has at least one SCI (via associes membership)
    sci_result = (
        client.table("associes")
        .select("id_sci")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    sci_created = bool(sci_result.data)

    # Check if user has at least one bien (via SCI membership)
    bien_created = False
    if sci_created:
        sci_ids = [str(row["id_sci"]) for row in sci_result.data]
        for sci_id in sci_ids:
            bien_result = (
                client.table("biens")
                .select("id")
                .eq("id_sci", sci_id)
                .limit(1)
                .execute()
            )
            if bien_result.data:
                bien_created = True
                break

    # Check if at least one bail exists
    bail_created = False
    if bien_created:
        for sci_id in sci_ids:
            biens_result = (
                client.table("biens")
                .select("id")
                .eq("id_sci", sci_id)
                .execute()
            )
            for bien_row in biens_result.data or []:
                bail_result = (
                    client.table("baux")
                    .select("id")
                    .eq("id_bien", str(bien_row["id"]))
                    .limit(1)
                    .execute()
                )
                if bail_result.data:
                    bail_created = True
                    break
            if bail_created:
                break

    # Check if notification preferences exist
    notif_result = (
        client.table("notification_preferences")
        .select("id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    notifications_set = bool(notif_result.data)

    return OnboardingStatus(
        completed=completed,
        sci_created=sci_created,
        bien_created=bien_created,
        bail_created=bail_created,
        notifications_set=notifications_set,
    )


@router.get("", response_model=OnboardingStatus)
async def get_onboarding_status(
    user_id: str = Depends(get_current_user),
) -> OnboardingStatus:
    logger.info("fetching_onboarding_status", user_id=user_id)
    return _check_onboarding_progress(user_id)


@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    user_id: str = Depends(get_current_user),
) -> OnboardingCompleteResponse:
    """Mark onboarding as completed for the user."""
    logger.info("completing_onboarding", user_id=user_id)

    client = get_supabase_service_client()
    client.table("subscriptions").update(
        {"onboarding_completed": True}
    ).eq("user_id", user_id).execute()

    return OnboardingCompleteResponse(completed=True)
