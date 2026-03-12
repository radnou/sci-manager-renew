"""Authentication endpoints - Magic Link + Activate (post-checkout)"""
import asyncio

import stripe
import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ExternalServiceError, ValidationError
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_service_client
from app.services.auth_service import magic_link_service

# Re-export so tests can patch at module level
from app.api.v1.stripe import _find_user_by_email  # noqa: F401

router = APIRouter(prefix="/auth", tags=["auth"])
logger = structlog.get_logger(__name__)


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    success: bool
    message: str


class ActivateResponse(BaseModel):
    token_hash: str
    type: str = "magiclink"
    plan_key: str | None = None


@router.get("/activate", response_model=ActivateResponse)
@limiter.limit("5/minute")
async def activate_session(
    request: Request, session_id: str | None = None
) -> ActivateResponse:
    """Auto-login after Stripe checkout — returns OTP token for frontend verifyOtp."""
    del request  # required by limiter but unused

    if not session_id:
        raise ValidationError("session_id is required")

    # 1. Validate with Stripe
    stripe.api_key = settings.stripe_secret_key
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        raise ValidationError("Invalid or expired session")

    if session.payment_status != "paid":
        raise ValidationError("Payment not completed")

    # 2. Extract email + plan_key
    email = session.customer_details.email if session.customer_details else None
    if not email:
        raise ValidationError("No email found in session")
    plan_key = session.metadata.get("plan_key") if session.metadata else None

    # 3. Find user (webhook should have created them — retry up to 3 times)
    user_id: str | None = None
    for _attempt in range(3):
        user_id = _find_user_by_email(email)
        if user_id:
            break
        await asyncio.sleep(2)

    if not user_id:
        raise ExternalServiceError("Supabase", "Account not yet created — please retry")

    # 4. Anti-replay: upsert with ignore_duplicates
    client = get_supabase_service_client()
    result = client.table("activated_sessions").upsert(
        {"session_id": session_id, "user_id": user_id},
        on_conflict="session_id",
        ignore_duplicates=True,
    ).execute()
    if not result.data:
        raise AuthenticationError("This activation link has already been used")

    # 5. Generate magic link for auto-login
    link_result = client.auth.admin.generate_link({
        "type": "magiclink",
        "email": email,
    })

    token_hash = ""
    if hasattr(link_result, "properties"):
        token_hash = getattr(link_result.properties, "hashed_token", "")

    logger.info("session_activated", session_id=session_id, user_id=user_id)
    return ActivateResponse(token_hash=token_hash, plan_key=plan_key)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password", response_model=MagicLinkResponse)
@limiter.limit("3/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest) -> MagicLinkResponse:
    """Send password reset email via Supabase Auth.

    Always returns success to prevent email enumeration.
    """
    del request  # required by limiter but unused
    logger.info("forgot_password_requested", email=payload.email)
    try:
        client = get_supabase_service_client()
        client.auth.reset_password_email(
            payload.email,
            {"redirect_to": f"{settings.frontend_url}/reset-password"},
        )
    except Exception as e:
        logger.error("forgot_password_error", email=payload.email, error=str(e))
    # Always return success to avoid email enumeration
    return MagicLinkResponse(
        success=True,
        message="If this email exists, a reset link has been sent.",
    )


@router.post("/magic-link/send", response_model=MagicLinkResponse)
@limiter.limit("5/minute")
async def send_magic_link(request: Request, payload: MagicLinkRequest) -> MagicLinkResponse:
    """
    Send magic link to user email for password-less authentication
    """
    logger.info("sending_magic_link", email=payload.email)
    try:
        # Send via Supabase Auth OTP
        result = await magic_link_service.send_magic_link(payload.email)

        if not result["success"]:
            logger.warning("magic_link_send_failed", email=payload.email, reason=result["message"])
            raise ValidationError(result["message"])

        logger.info("magic_link_sent", email=payload.email)
        return MagicLinkResponse(
            success=True,
            message=f"Magic link sent to {payload.email}. Check your email.",
        )
    except (ValidationError, AuthenticationError, ExternalServiceError):
        raise
    except Exception as e:
        logger.error("magic_link_send_error", email=payload.email, error=str(e))
        raise ExternalServiceError("Supabase Auth", "Failed to send magic link")


@router.post("/magic-link/verify", response_model=MagicLinkResponse)
@limiter.limit("10/minute")
async def verify_magic_link(request: Request, token: str) -> MagicLinkResponse:
    """
    Verify magic link token
    Token comes from URL parameter (email_token or token)
    """
    del request
    logger.info("verifying_magic_link")
    try:
        result = await magic_link_service.verify_magic_link(token)

        if not result["success"]:
            logger.warning("magic_link_verification_failed", reason=result["message"])
            raise AuthenticationError(result["message"])

        logger.info("magic_link_verified")
        return MagicLinkResponse(success=True, message="Magic link verified")
    except (ValidationError, AuthenticationError, ExternalServiceError):
        raise
    except Exception as e:
        logger.error("magic_link_verification_error", error=str(e))
        raise ExternalServiceError("Supabase Auth", "Failed to verify magic link")


@router.post("/logout", response_model=MagicLinkResponse)
@limiter.limit("20/minute")
async def logout(request: Request, access_token: str) -> MagicLinkResponse:
    """
    Sign out user
    """
    del request
    logger.info("logging_out_user")
    try:
        result = await magic_link_service.sign_out(access_token)

        if not result["success"]:
            logger.warning("logout_failed", reason=result["message"])
            raise ValidationError(result["message"])

        logger.info("user_logged_out")
        return MagicLinkResponse(success=True, message="Signed out successfully")
    except (ValidationError, AuthenticationError, ExternalServiceError):
        raise
    except Exception as e:
        logger.error("logout_error", error=str(e))
        raise ExternalServiceError("Supabase Auth", "Failed to sign out")
