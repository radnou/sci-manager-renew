"""Authentication endpoints - Magic Link"""
import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, EmailStr

from app.core.exceptions import AuthenticationError, ExternalServiceError, ValidationError
from app.core.rate_limit import limiter
from app.services.auth_service import magic_link_service

router = APIRouter(prefix="/auth", tags=["auth"])
logger = structlog.get_logger(__name__)


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    success: bool
    message: str


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
