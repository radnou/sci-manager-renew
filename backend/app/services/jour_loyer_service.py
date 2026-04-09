"""Cascading rent-date resolution for the 'jour_loyer' setting.

Resolution order (first non-None value wins):
    bien.jour_loyer → sci.jour_loyer → global_default → 1
"""
from __future__ import annotations

from typing import Any

DEFAULT_JOUR_LOYER = 1


def resolve_jour_loyer(
    bien_jour_loyer: int | None,
    sci_jour_loyer: int | None,
    global_default: int | None = None,
) -> int:
    """Return the effective jour_loyer (1-28) for a given bien.

    Args:
        bien_jour_loyer: value stored on the ``biens`` row (may be None).
        sci_jour_loyer:  value stored on the ``sci`` row (may be None).
        global_default:  user-level preference (may be None).

    Returns:
        An integer between 1 and 28 (inclusive).
    """
    day = bien_jour_loyer or sci_jour_loyer or global_default or DEFAULT_JOUR_LOYER
    # Clamp to valid range just in case of legacy data.
    return max(1, min(28, int(day)))


def resolve_jour_loyer_for_bien(bien_row: dict[str, Any], sci_row: dict[str, Any] | None = None) -> int:
    """Convenience wrapper that accepts raw Supabase row dicts.

    Args:
        bien_row: row from the ``biens`` table.
        sci_row:  row from the ``sci`` table (optional — looked up via bien_row['id_sci'] if needed).

    Returns:
        Effective jour_loyer as an integer between 1 and 28.
    """
    bien_jour = bien_row.get("jour_loyer")
    sci_jour = (sci_row or {}).get("jour_loyer") if sci_row is not None else None
    return resolve_jour_loyer(bien_jour, sci_jour)
