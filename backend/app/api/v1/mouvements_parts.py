"""CRUD API for mouvements de parts (share transfers registry) under /scis/{sci_id}/mouvements-parts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field

from app.core.exceptions import DatabaseError, GererSCIException, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/mouvements-parts", tags=["mouvements-parts"])


# ──────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────


class MouvementPartsCreate(BaseModel):
    date_mouvement: date
    type_mouvement: str = Field(..., min_length=1, max_length=50)
    cedant_nom: str = Field(..., min_length=1, max_length=200)
    cessionnaire_nom: str = Field(..., min_length=1, max_length=200)
    nb_parts: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., ge=0)
    prix_total: float = Field(..., ge=0)
    document_url: Optional[str] = None
    notes: Optional[str] = None


class MouvementPartsResponse(BaseModel):
    id: str
    id_sci: str
    date_mouvement: date
    type_mouvement: str
    cedant_nom: str
    cessionnaire_nom: str
    nb_parts: int
    prix_unitaire: float
    prix_total: float
    document_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    """Service client for INSERT operations — RLS blocks inserts before membership exists."""
    return get_supabase_service_client()


def _recalculate_associe_parts(
    write_client,
    sci_id: str,
    cedant_nom: str,
    cessionnaire_nom: str,
    nb_parts_transferred: int,
):
    """Recalculate nb_parts and part (percentage) for cedant and cessionnaire after a transfer.

    Matches associes by nom within the SCI. If no match is found, logs a warning and skips.
    Verifies that total parts still equals sci.nb_parts_total after the update.
    """
    # Fetch all associes for this SCI
    associes_result = write_client.table("associes").select("*").eq("id_sci", sci_id).execute()
    associes = associes_result.data or []

    if not associes:
        logger.warning("no_associes_found_for_recalc", sci_id=sci_id)
        return

    # Fetch SCI to get nb_parts_total
    sci_result = write_client.table("sci").select("nb_parts_total").eq("id", sci_id).execute()
    sci_data = sci_result.data or []
    nb_parts_total = sci_data[0].get("nb_parts_total") if sci_data else None

    # Find cedant and cessionnaire by nom
    cedant = next((a for a in associes if a.get("nom") == cedant_nom), None)
    cessionnaire = next((a for a in associes if a.get("nom") == cessionnaire_nom), None)

    if not cedant and not cessionnaire:
        logger.info("no_matching_associes_for_recalc", cedant=cedant_nom, cessionnaire=cessionnaire_nom)
        return

    # Update cedant: subtract parts
    if cedant:
        current_nb = cedant.get("nb_parts") or 0
        new_nb = max(0, current_nb - nb_parts_transferred)
        update_cedant = {"nb_parts": new_nb}
        if nb_parts_total and nb_parts_total > 0:
            update_cedant["part"] = round((new_nb / nb_parts_total) * 100, 2)
        write_client.table("associes").update(update_cedant).eq("id", str(cedant["id"])).execute()
        logger.info("cedant_parts_updated", associe_id=cedant["id"], old_nb=current_nb, new_nb=new_nb)

    # Update cessionnaire: add parts
    if cessionnaire:
        current_nb = cessionnaire.get("nb_parts") or 0
        new_nb = current_nb + nb_parts_transferred
        update_cess = {"nb_parts": new_nb}
        if nb_parts_total and nb_parts_total > 0:
            update_cess["part"] = round((new_nb / nb_parts_total) * 100, 2)
        write_client.table("associes").update(update_cess).eq("id", str(cessionnaire["id"])).execute()
        logger.info("cessionnaire_parts_updated", associe_id=cessionnaire["id"], old_nb=current_nb, new_nb=new_nb)

    # Verify total parts consistency
    if nb_parts_total is not None:
        updated_result = write_client.table("associes").select("nb_parts").eq("id_sci", sci_id).execute()
        total = sum((a.get("nb_parts") or 0) for a in (updated_result.data or []))
        if total != nb_parts_total:
            logger.warning(
                "parts_total_mismatch",
                sci_id=sci_id,
                expected=nb_parts_total,
                actual=total,
            )


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("", response_model=list[MouvementPartsResponse])
@router.get("/", response_model=list[MouvementPartsResponse])
async def list_mouvements_parts(
    sci_id: UUID,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """List all share transfer movements for a given SCI."""
    logger.info("listing_mouvements_parts", sci_id=str(sci_id), user_id=membership.user_id)

    try:
        client = _get_client(request)
        result = client.table("mouvements_parts").select("*").eq("id_sci", str(sci_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        rows.sort(key=lambda r: str(r.get("date_mouvement", "")), reverse=True)
        return rows
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("list_mouvements_parts_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list mouvements de parts")


@router.post("", response_model=MouvementPartsResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=MouvementPartsResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_mouvement_parts(
    sci_id: UUID,
    payload: MouvementPartsCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Create a new share transfer movement. Requires gerant role."""
    logger.info(
        "creating_mouvement_parts",
        sci_id=str(sci_id),
        user_id=membership.user_id,
        type_mouvement=payload.type_mouvement,
    )

    try:
        client = _get_client(request)
        insert_data = payload.model_dump(mode="json")
        insert_data["id_sci"] = str(sci_id)

        write_client = _get_write_client()
        result = write_client.table("mouvements_parts").insert(insert_data).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create mouvement de parts")

        created = rows[0]

        # Task 6: Recalculate parts for cedant and cessionnaire after insertion
        _recalculate_associe_parts(
            write_client, str(sci_id),
            payload.cedant_nom, payload.cessionnaire_nom, payload.nb_parts,
        )

        return created
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("create_mouvement_parts_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create mouvement de parts")


@router.delete("/{mouvement_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_mouvement_parts(
    sci_id: UUID,
    mouvement_id: UUID,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Delete a share transfer movement. Requires gerant role."""
    logger.info(
        "deleting_mouvement_parts",
        sci_id=str(sci_id),
        mouvement_id=str(mouvement_id),
        user_id=membership.user_id,
    )

    try:
        client = _get_client(request)

        # Verify the mouvement exists and belongs to this SCI
        check = client.table("mouvements_parts").select("id").eq("id", str(mouvement_id)).eq("id_sci", str(sci_id)).execute()
        if getattr(check, "error", None):
            raise DatabaseError(str(check.error))
        if not (check.data or []):
            raise ResourceNotFoundError("MouvementParts", str(mouvement_id))

        result = client.table("mouvements_parts").delete().eq("id", str(mouvement_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("delete_mouvement_parts_failed", mouvement_id=str(mouvement_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete mouvement de parts")


# ──────────────────────────────────────────────────────────────
# SIMULATION droits d'enregistrement sur cession de parts
# ──────────────────────────────────────────────────────────────

TAUX_DROITS_ENREGISTREMENT = 5.0  # 5% — Art. 726 CGI

_FORMALITES_CESSION = [
    "Acte de cession (SSP ou notarié)",
    "Enregistrement aux impôts dans 1 mois",
    "Signification à la société (art. 1690 C.civ)",
    "Mise à jour des statuts",
    "Publication si changement de gérant",
]


class SimulationDroitsResponse(BaseModel):
    prix_total: float
    droits_enregistrement: float
    taux: float
    base_taxable: float
    reference_legale: str
    formalites: list[str]


@router.get("/simulation-droits", response_model=SimulationDroitsResponse)
async def simulation_droits_enregistrement(
    sci_id: UUID,
    request: Request,
    nb_parts: int,
    prix_unitaire: float,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Simulate registration duties for a share transfer (Art. 726 CGI)."""
    if nb_parts <= 0:
        raise ValidationError("nb_parts doit être supérieur à 0")
    if prix_unitaire < 0:
        raise ValidationError("prix_unitaire doit être positif ou nul")

    logger.info(
        "simulation_droits",
        sci_id=str(sci_id),
        nb_parts=nb_parts,
        prix_unitaire=prix_unitaire,
    )

    prix_total = nb_parts * prix_unitaire
    base_taxable = prix_total
    droits = round(base_taxable * TAUX_DROITS_ENREGISTREMENT / 100, 2)

    return SimulationDroitsResponse(
        prix_total=prix_total,
        droits_enregistrement=droits,
        taux=TAUX_DROITS_ENREGISTREMENT,
        base_taxable=base_taxable,
        reference_legale="Art. 726 CGI — Droits d'enregistrement sur cessions de parts sociales",
        formalites=_FORMALITES_CESSION,
    )
