"""Authentication endpoints - Magic Link"""
import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.auth_service import magic_link_service

router = APIRouter(prefix="/auth", tags=["auth"])
logger = structlog.get_logger(__name__)


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    success: bool
    message: str


@router.post("/magic-link/send", response_model=MagicLinkResponse)
async def send_magic_link(request: MagicLinkRequest) -> MagicLinkResponse:
    """
    Send magic link to user email for password-less authentication
    """
    logger.info("sending_magic_link", email=request.email)
    try:
        # Send via Supabase Auth OTP
        result = await magic_link_service.send_magic_link(request.email)

        if not result["success"]:
            logger.warning("magic_link_send_failed", email=request.email, reason=result["message"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        logger.info("magic_link_sent", email=request.email)
        return MagicLinkResponse(
            success=True,
            message=f"Magic link sent to {request.email}. Check your email.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("magic_link_send_error", email=request.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send magic link",
        )


@router.post("/magic-link/verify", response_model=MagicLinkResponse)
async def verify_magic_link(token: str) -> MagicLinkResponse:
    """
    Verify magic link token
    Token comes from URL parameter (email_token or token)
    """
    logger.info("verifying_magic_link")
    try:
        result = await magic_link_service.verify_magic_link(token)

        if not result["success"]:
            logger.warning("magic_link_verification_failed", reason=result["message"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=result["message"]
            )

        logger.info("magic_link_verified")
        return MagicLinkResponse(success=True, message="Magic link verified")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("magic_link_verification_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify magic link",
        )


@router.post("/logout", response_model=MagicLinkResponse)
async def logout(access_token: str) -> MagicLinkResponse:
    """
    Sign out user
    """
    logger.info("logging_out_user")
    try:
        result = await magic_link_service.sign_out(access_token)

        if not result["success"]:
            logger.warning("logout_failed", reason=result["message"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        logger.info("user_logged_out")
        return MagicLinkResponse(success=True, message="Signed out successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("logout_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign out",
        )
