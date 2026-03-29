"""Service for mortgage/loan amortization table generation."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def generate_amortissement(
    montant: float,
    taux_nominal: float,
    taux_assurance: float,
    duree_mois: int,
    date_debut: str,
    mensualite: float,
) -> list[dict[str, Any]]:
    """Generate monthly amortization table using standard French formula.

    Each row contains:
        mois, date, mensualite, capital, interets, assurance, capital_restant

    Args:
        montant: Total borrowed amount.
        taux_nominal: Annual nominal rate (e.g. 2.5 for 2.5%).
        taux_assurance: Annual insurance rate (e.g. 0.3 for 0.3%).
        duree_mois: Loan duration in months.
        date_debut: Start date as ISO string (YYYY-MM-DD).
        mensualite: Monthly payment amount (capital + interest, excl. insurance).

    Returns:
        List of dicts, one per month.
    """
    taux_mensuel = (taux_nominal / 100) / 12
    taux_assurance_mensuel = (taux_assurance / 100) / 12
    capital_restant = montant

    start = date.fromisoformat(date_debut)
    rows: list[dict[str, Any]] = []

    for mois in range(1, duree_mois + 1):
        interets = round(capital_restant * taux_mensuel, 2)
        assurance = round(montant * taux_assurance_mensuel, 2)

        # Last month: adjust capital to close out rounding
        if mois == duree_mois:
            capital = round(capital_restant, 2)
        else:
            capital = round(mensualite - interets, 2)
            # Guard against negative capital (shouldn't happen with correct mensualite)
            if capital < 0:
                capital = 0.0

        capital_restant = round(capital_restant - capital, 2)
        if capital_restant < 0:
            capital_restant = 0.0

        # Compute date for this month
        month_offset = (start.month - 1 + mois) % 12 + 1
        year_offset = start.year + (start.month - 1 + mois) // 12
        day = min(start.day, _days_in_month(year_offset, month_offset))
        row_date = date(year_offset, month_offset, day)

        rows.append({
            "mois": mois,
            "date": row_date.isoformat(),
            "mensualite": round(mensualite + assurance, 2),
            "capital": capital,
            "interets": interets,
            "assurance": assurance,
            "capital_restant": capital_restant,
        })

    return rows


def _days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month."""
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - date(year, month, 1)).days
