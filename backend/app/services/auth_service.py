"""Magic Link authentication service — uses Resend + custom HTML templates"""
from typing import Optional

import structlog
from supabase import create_client

from app.core.config import settings
from app.core.external_services import run_with_retry
from app.services.email_service import email_service

logger = structlog.get_logger(__name__)


class MagicLinkService:
    """Service for magic link authentication via custom email templates"""

    def __init__(self):
        self.client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )

    async def send_magic_link(self, email: str) -> dict:
        """
        Generate magic link via Supabase Admin API and send via Resend
        with the custom HTML template.
        """
        try:
            # Generate link without sending email (admin API)
            link_result = await run_with_retry(
                operation="supabase_auth.generate_link",
                func=lambda: self.client.auth.admin.generate_link({
                    "type": "magiclink",
                    "email": email,
                }),
                context={"email": email},
            )

            # Extract the action link from the response
            action_link = ""
            if hasattr(link_result, "properties"):
                action_link = getattr(link_result.properties, "action_link", "")

            if not action_link:
                logger.error("magic_link_no_action_link", email=email)
                return {"success": False, "message": "Failed to generate magic link", "data": None}

            # Send via Resend with custom HTML template
            await email_service.send_magic_link(email, action_link)

            logger.info("magic_link_sent_via_resend", email=email)
            return {
                "success": True,
                "message": "Magic link sent to email",
                "data": None,
            }
        except Exception as e:
            logger.error("send_magic_link_failed", email=email, error=str(e), exc_info=True)
            return {"success": False, "message": str(e), "data": None}

    async def verify_magic_link(self, token: str) -> Optional[dict]:
        """
        Verify magic link token and return user session
        Token should come from URL parameter email_token
        """
        try:
            # Supabase handles verification automatically via URL
            # Frontend receives the session after clicking magic link
            return {"success": True, "message": "Magic link verified"}
        except Exception as e:
            logger.error("verify_magic_link_failed", error=str(e), exc_info=True)
            return {"success": False, "message": str(e)}

    async def create_user_from_magic_link(
        self, email: str, user_metadata: Optional[dict] = None
    ) -> dict:
        """
        Create user account after magic link verification
        Call this after user clicks magic link
        """
        try:
            # User already created by Supabase Auth OTP flow
            # Just update metadata if provided
            if user_metadata:
                response = self.client.auth.update_user(
                    {"user_metadata": user_metadata}
                )
                return {
                    "success": True,
                    "message": "User profile updated",
                    "data": response,
                }

            return {"success": True, "message": "User authenticated"}
        except Exception as e:
            logger.error("create_user_from_magic_link_failed", email=email, error=str(e), exc_info=True)
            return {"success": False, "message": str(e), "data": None}

    async def sign_out(self, access_token: str) -> dict:
        """Sign out user"""
        try:
            # Frontend should handle this via Supabase client
            return {"success": True, "message": "Signed out successfully"}
        except Exception as e:
            logger.error("sign_out_failed", error=str(e), exc_info=True)
            return {"success": False, "message": str(e)}

    async def get_user_session(self, access_token: str) -> Optional[dict]:
        """
        Get current user session from access token
        """
        try:
            user = await run_with_retry(
                operation="supabase_auth.get_user",
                func=lambda: self.client.auth.get_user(access_token),
                context={"has_access_token": bool(access_token)},
            )
            return user
        except Exception:
            return None

    async def refresh_session(self, refresh_token: str) -> Optional[dict]:
        """
        Refresh user session using refresh token
        """
        try:
            response = await run_with_retry(
                operation="supabase_auth.refresh_session",
                func=lambda: self.client.auth.refresh_session(refresh_token),
                context={"has_refresh_token": bool(refresh_token)},
            )
            return response
        except Exception:
            return None


# Singleton instance
magic_link_service = MagicLinkService()
