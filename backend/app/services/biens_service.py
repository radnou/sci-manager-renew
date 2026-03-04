"""Backward-compatible wrapper for Phase 2 migration."""

from app.services.sci_service import SCIService


def calculate_rentabilite(bien: dict) -> dict[str, float]:
    return SCIService.calculate_rentabilite(bien)
