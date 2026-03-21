"""Calendrier fiscal API — fiscal calendar with completion status for a SCI."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from app.core.exceptions import DatabaseError, GererSCIException, ResourceNotFoundError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/calendrier-fiscal", tags=["calendrier-fiscal"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    return get_supabase_service_client()


# ──────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────


class EcheanceFiscale(BaseModel):
    key: str
    label: str
    date_limite: str
    statut: str = "a_faire"  # a_faire | fait
    reference: str = ""
    date_realisation: Optional[str] = None


class CalendrierFiscalResponse(BaseModel):
    annee: int
    echeances: list[EcheanceFiscale] = []


class MarquerFaitPayload(BaseModel):
    date_realisation: str


class MarquerFaitResponse(BaseModel):
    key: str
    statut: str
    date_realisation: str


# ──────────────────────────────────────────────────────────────
# Fiscal calendar definition
# ──────────────────────────────────────────────────────────────

_ECHEANCES_DEFINITION = [
    {
        "key": "2072",
        "label": "Declaration 2072",
        "month": 5,
        "day": 3,
        "reference": "Art. 172 CGI",
        "regime": "IR",
    },
    {
        "key": "2044",
        "label": "Declaration 2044",
        "month": 5,
        "day": 31,
        "reference": "Art. 28 CGI",
        "regime": "IR",
    },
    {
        "key": "liasse_is",
        "label": "Liasse fiscale IS",
        "month": 3,
        "day": 31,
        "reference": "Art. 223 CGI",
        "regime": "IS",
    },
    {
        "key": "taxe_fonciere",
        "label": "Taxe fonciere",
        "month": 10,
        "day": 15,
        "reference": "Art. 1399 CGI",
        "regime": None,
    },
    {
        "key": "cfe",
        "label": "CFE",
        "month": 12,
        "day": 15,
        "reference": "Art. 1447 CGI",
        "regime": None,
    },
    {
        "key": "ag",
        "label": "AG annuelle",
        "month": 6,
        "day": 30,
        "reference": "Art. 1856 C.civ",
        "regime": None,
    },
]


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("/{annee}", response_model=CalendrierFiscalResponse)
async def get_calendrier_fiscal(
    request: Request,
    sci_id: UUID,
    annee: int,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Return the fiscal calendar for a given SCI and year, with completion status."""
    logger.info("get_calendrier_fiscal", sci_id=str(sci_id), annee=annee)

    client = _get_client(request)

    # Fetch SCI regime fiscal
    sci_result = client.table("sci").select("regime_fiscal").eq("id", str(sci_id)).execute()
    if not (sci_result.data or []):
        raise ResourceNotFoundError("SCI", str(sci_id))
    regime = (sci_result.data[0].get("regime_fiscal") or "").upper()

    # Fetch completion records from calendrier_fiscal table
    completions_result = (
        client.table("calendrier_fiscal")
        .select("echeance_key, date_realisation")
        .eq("id_sci", str(sci_id))
        .eq("annee", annee)
        .execute()
    )
    completions = {
        row["echeance_key"]: row.get("date_realisation")
        for row in (completions_result.data or [])
    }

    # Also check AG: if an AG exists for this year's exercice, mark as fait
    ag_result = (
        client.table("assemblees_generales")
        .select("date_ag")
        .eq("id_sci", str(sci_id))
        .eq("exercice_annee", annee)
        .execute()
    )
    if ag_result.data and "ag" not in completions:
        completions["ag"] = ag_result.data[0].get("date_ag")

    echeances = []
    for defn in _ECHEANCES_DEFINITION:
        # Filter by regime: skip regime-specific deadlines that don't match
        if defn["regime"] is not None:
            if defn["regime"] == "IR" and regime == "IS":
                continue
            if defn["regime"] == "IS" and regime != "IS":
                continue

        date_limite = date(annee, defn["month"], defn["day"]).isoformat()
        date_realisation = completions.get(defn["key"])
        statut = "fait" if date_realisation else "a_faire"

        echeances.append(EcheanceFiscale(
            key=defn["key"],
            label=defn["label"],
            date_limite=date_limite,
            statut=statut,
            reference=defn.get("reference", ""),
            date_realisation=date_realisation,
        ))

    return CalendrierFiscalResponse(annee=annee, echeances=echeances)


@router.post("/{annee}/{key}/marquer-fait", response_model=MarquerFaitResponse)
async def marquer_echeance_faite(
    request: Request,
    sci_id: UUID,
    annee: int,
    key: str,
    payload: MarquerFaitPayload,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Mark a fiscal deadline as completed."""
    logger.info("marquer_echeance_faite", sci_id=str(sci_id), annee=annee, key=key)

    # Validate key exists
    valid_keys = {d["key"] for d in _ECHEANCES_DEFINITION}
    if key not in valid_keys:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"Cle d'echeance invalide : {key}. Valeurs acceptees : {', '.join(sorted(valid_keys))}")

    write_client = _get_write_client()

    # Check if already exists (upsert)
    existing = (
        write_client.table("calendrier_fiscal")
        .select("id")
        .eq("id_sci", str(sci_id))
        .eq("annee", annee)
        .eq("echeance_key", key)
        .execute()
    )

    if existing.data:
        # Update existing
        write_client.table("calendrier_fiscal").update({
            "date_realisation": payload.date_realisation,
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        # Insert new
        write_client.table("calendrier_fiscal").insert({
            "id_sci": str(sci_id),
            "annee": annee,
            "echeance_key": key,
            "date_realisation": payload.date_realisation,
        }).execute()

    logger.info("echeance_marquee_faite", key=key, annee=annee, sci_id=str(sci_id))

    return MarquerFaitResponse(
        key=key,
        statut="fait",
        date_realisation=payload.date_realisation,
    )
