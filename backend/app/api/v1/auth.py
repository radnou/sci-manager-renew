"""Authentication endpoints - Magic Link"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.auth_service import magic_link_service
from app.services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["auth"])


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
    try:
        # Send via Supabase Auth OTP
        result = await magic_link_service.send_magic_link(request.email)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        return MagicLinkResponse(
            success=True,
            message=f"Magic link sent to {request.email}. Check your email.",
        )
    except HTTPException:
        raise
    except Exception as e:
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
    try:
        result = await magic_link_service.verify_magic_link(token)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=result["message"]
            )

        return MagicLinkResponse(success=True, message="Magic link verified")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify magic link",
        )


@router.post("/logout", response_model=MagicLinkResponse)
async def logout(access_token: str) -> MagicLinkResponse:
    """
    Sign out user
    """
    try:
        result = await magic_link_service.sign_out(access_token)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        return MagicLinkResponse(success=True, message="Signed out successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign out",
        )
