"""Backward-compatible alias for migrated Pydantic models."""

from app.models.biens import BienCreate
from app.models.biens import BienResponse as Bien
from app.models.biens import BienUpdate

__all__ = ["Bien", "BienCreate", "BienUpdate"]
