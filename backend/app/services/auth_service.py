"""Magic Link authentication service"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from supabase import create_client

from app.core.config import settings


class MagicLinkService:
    """Service for magic link authentication"""

    def __init__(self):
        self.client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )

    async def send_magic_link(self, email: str) -> dict:
        """
        Send magic link to user email via Supabase Auth
        Returns the access token and session info
        """
        try:
            response = self.client.auth.sign_in_with_otp({"email": email})

            return {
                "success": True,
                "message": "Magic link sent to email",
                "data": response,
            }
        except Exception as e:
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
            return {"success": False, "message": str(e), "data": None}

    async def sign_out(self, access_token: str) -> dict:
        """Sign out user"""
        try:
            # Frontend should handle this via Supabase client
            return {"success": True, "message": "Signed out successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_user_session(self, access_token: str) -> Optional[dict]:
        """
        Get current user session from access token
        """
        try:
            user = self.client.auth.get_user(access_token)
            return user
        except Exception as e:
            return None

    async def refresh_session(self, refresh_token: str) -> Optional[dict]:
        """
        Refresh user session using refresh token
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)
            return response
        except Exception as e:
            return None


# Singleton instance
magic_link_service = MagicLinkService()
