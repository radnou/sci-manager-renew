"""Backward-compatible alias for migrated Pydantic models."""

from app.models.loyers import LoyerCreate
from app.models.loyers import LoyerResponse as Loyer
from app.models.loyers import LoyerUpdate

__all__ = ["Loyer", "LoyerCreate", "LoyerUpdate"]
