"""
Paywall & membership dependencies for FastAPI routes.

Usage:
    @router.get("/protected", dependencies=[Depends(require_active_subscription)])
    async def protected_route(user_id: str = Depends(get_current_user)):
        ...

    @router.post("/gerant-only")
    async def gerant_route(membership: AssocieMembership = Depends(require_gerant_role)):
        ...
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_service_client
from app.services.subscription_service import SubscriptionService


@dataclass
class SubscriptionInfo:
    user_id: str
    plan_key: str
    is_active: bool
    onboarding_completed: bool


@dataclass
class AssocieMembership:
    user_id: str
    sci_id: str
    role: str  # 'gerant' | 'associe'
    associe_id: str


async def require_active_subscription(
    user_id: str = Depends(get_current_user),
) -> SubscriptionInfo:
    """
    Verify user has an active subscription.
    Raises HTTP 402 (Payment Required) if not.
    """
    summary = SubscriptionService.get_subscription_summary(user_id)

    # Load onboarding_completed from DB
    client = get_supabase_service_client()
    result = (
        client.table("subscriptions")
        .select("onboarding_completed")
        .eq("user_id", user_id)
        .execute()
    )
    onboarding_completed = False
    if result.data:
        onboarding_completed = bool(result.data[0].get("onboarding_completed", False))

    if not summary.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "subscription_required",
                "message": "Un abonnement actif est requis.",
                "redirect": "/pricing",
            },
        )

    return SubscriptionInfo(
        user_id=user_id,
        plan_key=str(summary.get("plan_key", "free")),
        is_active=True,
        onboarding_completed=onboarding_completed,
    )


async def require_sci_membership(
    sci_id: UUID,
    user_id: str = Depends(get_current_user),
) -> AssocieMembership:
    """
    Verify user is a member (associe) of the given SCI.
    Returns the membership with role info.
    Raises HTTP 404 if not a member.
    """
    client = get_supabase_service_client()
    result = (
        client.table("associes")
        .select("id, role")
        .eq("id_sci", str(sci_id))
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SCI non trouvée",
        )

    row = result.data[0]
    return AssocieMembership(
        user_id=user_id,
        sci_id=str(sci_id),
        role=row.get("role", "associe"),
        associe_id=str(row["id"]),
    )


async def require_gerant_role(
    membership: AssocieMembership = Depends(require_sci_membership),
) -> AssocieMembership:
    """
    Verify user is a gerant (not just associe).
    For write operations (POST/PATCH/DELETE).
    """
    if membership.role != "gerant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au gérant de la SCI.",
        )
    return membership
