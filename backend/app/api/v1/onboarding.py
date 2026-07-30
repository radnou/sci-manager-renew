"""
Onboarding API — tracks onboarding wizard progress.

GET  /api/v1/onboarding        → current status
POST /api/v1/onboarding/complete → mark onboarding as completed
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.core.supabase_client import (
    get_supabase_user_client,
    get_supabase_service_client,
)
from app.services.associe_linking import link_user_to_pending_associes

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
logger = structlog.get_logger(__name__)


class OnboardingProfile(BaseModel):
    role: str
    volume: str
    current_tool: str
    priorities: list[str]


class OnboardingProfilePayload(BaseModel):
    role: str
    volume: str
    current_tool: str
    priorities: list[str]


class OnboardingStatus(BaseModel):
    completed: bool
    sci_created: bool
    sci_id: str | None = None
    bien_created: bool
    bail_created: bool
    notifications_set: bool
    profile_set: bool = False
    profile: OnboardingProfile | None = None


class OnboardingCompleteResponse(BaseModel):
    completed: bool


def _check_onboarding_progress(request: Request, user_id: str) -> OnboardingStatus:
    """Check real progress based on existing data."""
    client = get_supabase_user_client(request)

    # Check onboarding_completed flag + profile
    sub_result = (
        client.table("subscriptions")
        .select("onboarding_completed, onboarding_profile")
        .eq("user_id", user_id)
        .execute()
    )
    completed = False
    profile_set = False
    profile = None
    if sub_result.data:
        completed = bool(sub_result.data[0].get("onboarding_completed", False))
        raw_profile = sub_result.data[0].get("onboarding_profile")
        if raw_profile and isinstance(raw_profile, dict):
            profile_set = True
            profile = OnboardingProfile(**raw_profile)

    # Check if user has at least one SCI (via associes membership)
    # Filter out demo data in Python to avoid mock/query edge cases
    sci_result = (
        client.table("associes")
        .select("id_sci, is_demo")
        .eq("user_id", user_id)
        .execute()
    )
    real_scis = [
        row for row in (sci_result.data or []) if not row.get("is_demo", False)
    ]
    sci_created = bool(real_scis)
    first_sci_id = str(real_scis[0]["id_sci"]) if real_scis else None

    # Check if user has at least one real bien
    bien_created = False
    if sci_created:
        sci_ids = [str(row["id_sci"]) for row in real_scis]
        for sci_id in sci_ids:
            bien_result = (
                client.table("biens")
                .select("id, is_demo")
                .eq("id_sci", sci_id)
                .execute()
            )
            real_biens = [
                b for b in (bien_result.data or []) if not b.get("is_demo", False)
            ]
            if real_biens:
                bien_created = True
                break

    # Check if at least one real bail exists
    bail_created = False
    if bien_created:
        for sci_id in sci_ids:
            biens_result = (
                client.table("biens")
                .select("id, is_demo")
                .eq("id_sci", sci_id)
                .execute()
            )
            for bien_row in [
                b for b in (biens_result.data or []) if not b.get("is_demo", False)
            ]:
                bail_result = (
                    client.table("baux")
                    .select("id, is_demo")
                    .eq("id_bien", str(bien_row["id"]))
                    .execute()
                )
                real_baux = [
                    b for b in (bail_result.data or []) if not b.get("is_demo", False)
                ]
                if real_baux:
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
        sci_id=first_sci_id,
        bien_created=bien_created,
        bail_created=bail_created,
        notifications_set=notifications_set,
        profile_set=profile_set,
        profile=profile,
    )


@router.get("", response_model=OnboardingStatus)
async def get_onboarding_status(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> OnboardingStatus:
    logger.info("fetching_onboarding_status", user_id=user_id)
    return _check_onboarding_progress(request, user_id)


@router.post("/profile", response_model=OnboardingProfile)
@limiter.limit("30/minute")
async def save_onboarding_profile(
    request: Request,
    payload: OnboardingProfilePayload,
    user_id: str = Depends(get_current_user),
) -> OnboardingProfile:
    """Save onboarding profiling answers for the user."""
    logger.info("saving_onboarding_profile", user_id=user_id, role=payload.role)

    profile_data = payload.model_dump()
    client = get_supabase_service_client()

    existing = (
        client.table("subscriptions").select("id").eq("user_id", user_id).execute()
    )
    if existing.data:
        client.table("subscriptions").update({"onboarding_profile": profile_data}).eq(
            "user_id", user_id
        ).execute()
    else:
        client.table("subscriptions").insert(
            {"user_id": user_id, "onboarding_profile": profile_data, "status": "free"}
        ).execute()

    return OnboardingProfile(**profile_data)


@router.post("/complete", response_model=OnboardingCompleteResponse)
@limiter.limit("30/minute")
async def complete_onboarding(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> OnboardingCompleteResponse:
    """Mark onboarding as completed for the user."""
    logger.info("completing_onboarding", user_id=user_id)

    client = get_supabase_user_client(request)
    # Sécurité (audit C1, migration 043) : l'écriture sur `subscriptions` est
    # réservée au service_role. user_id provient du JWT vérifié, donc
    # l'autorisation est déjà établie à ce stade.
    sub_client = get_supabase_service_client()
    # Check if row exists first — if not, create with status='free'
    existing = (
        sub_client.table("subscriptions").select("id").eq("user_id", user_id).execute()
    )
    if existing.data:
        sub_client.table("subscriptions").update({"onboarding_completed": True}).eq(
            "user_id", user_id
        ).execute()
    else:
        sub_client.table("subscriptions").insert(
            {"user_id": user_id, "onboarding_completed": True, "status": "free"}
        ).execute()

    # Auto-link pending associe invitations for this user
    try:
        user_resp = client.auth.admin.get_user_by_id(user_id)
        user_email = getattr(user_resp, "user", None)
        if user_email:
            user_email = getattr(user_email, "email", None)
        if user_email:
            link_user_to_pending_associes(user_id, user_email)
    except Exception:
        logger.warning(
            "associe_linking_during_onboarding_failed", user_id=user_id, exc_info=True
        )

    return OnboardingCompleteResponse(completed=True)
