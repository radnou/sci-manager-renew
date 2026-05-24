"""Credits immobiliers API — nested under /scis/{sci_id}/biens/{bien_id}/credits."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_service_client, get_supabase_user_client
from app.schemas.credit_immobilier import (
    AmortissementRow,
    CreditImmobilierCreate,
    CreditImmobilierResponse,
    CreditImmobilierUpdate,
)
from app.services.credit_service import generate_amortissement

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/scis/{sci_id}/biens/{bien_id}/credits",
    tags=["credits-immobiliers"],
)


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _verify_bien_belongs_to_sci(client, bien_id: str, sci_id: str) -> dict:
    """Fetch a bien and verify it belongs to the given SCI."""
    result = client.table("biens").select("*").eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    rows = result.data or []
    if not rows:
        raise ResourceNotFoundError("Bien", bien_id)
    bien = rows[0]
    if str(bien.get("id_sci", "")) != sci_id:
        raise ResourceNotFoundError("Bien", bien_id)
    return bien


# ──────────────────────────────────────────────────────────────
# LIST credits
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[CreditImmobilierResponse])
async def list_credits(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les crédits immobiliers d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("credits_immobiliers")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_debut", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE credit
# ──────────────────────────────────────────────────────────────

@router.post("", response_model=CreditImmobilierResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_credit(
    sci_id: UUID,
    bien_id: str,
    payload: CreditImmobilierCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un crédit immobilier pour un bien (gérant uniquement)."""
    logger.info("creating_credit", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    write_client = _get_client(request)
    result = write_client.table("credits_immobiliers").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create credit immobilier")

    created = data[0]
    logger.info("credit_created", credit_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE credit
# ──────────────────────────────────────────────────────────────

@router.patch("/{credit_id}", response_model=CreditImmobilierResponse)
@limiter.limit("30/minute")
async def update_credit(
    sci_id: UUID,
    bien_id: str,
    credit_id: str,
    payload: CreditImmobilierUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un crédit immobilier (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_credit", credit_id=credit_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    write_client = _get_client(request)
    result = (
        write_client.table("credits_immobiliers")
        .update(update_payload)
        .eq("id", credit_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Credit immobilier", credit_id)

    logger.info("credit_updated", credit_id=credit_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE credit
# ──────────────────────────────────────────────────────────────

@router.delete("/{credit_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_credit(
    sci_id: UUID,
    bien_id: str,
    credit_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un crédit immobilier (gérant uniquement)."""
    logger.info("deleting_credit", credit_id=credit_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    write_client = _get_client(request)
    result = (
        write_client.table("credits_immobiliers")
        .delete()
        .eq("id", credit_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))


# ──────────────────────────────────────────────────────────────
# AMORTISSEMENT table (computed, no DB)
# ──────────────────────────────────────────────────────────────

@router.get("/{credit_id}/amortissement", response_model=list[AmortissementRow])
async def get_amortissement(
    sci_id: UUID,
    bien_id: str,
    credit_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Génère le tableau d'amortissement d'un crédit."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("credits_immobiliers")
        .select("*")
        .eq("id", credit_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    rows = result.data or []
    if not rows:
        raise ResourceNotFoundError("Credit immobilier", credit_id)

    credit = rows[0]
    table = generate_amortissement(
        montant=float(credit["montant_emprunte"]),
        taux_nominal=float(credit["taux_nominal"]),
        taux_assurance=float(credit.get("taux_assurance") or 0),
        duree_mois=int(credit["duree_mois"]),
        date_debut=credit["date_debut"],
        mensualite=float(credit["mensualite"]),
    )

    return table
