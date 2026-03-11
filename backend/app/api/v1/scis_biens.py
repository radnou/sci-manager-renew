"""Nested biens API under /scis/{sci_id}/biens with fiche bien support."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Response, status
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.models.loyers import LoyerCreate, LoyerResponse
from app.schemas.fiche_bien import FicheBienResponse, RentabiliteCalculee
from app.services.rentabilite_service import calculate_rentabilite

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/biens", tags=["scis-biens"])


def _get_client():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _verify_bien_belongs_to_sci(client, bien_id: str, sci_id: str) -> dict:
    """Fetch a bien and verify it belongs to the given SCI. Returns the bien row."""
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
# LIST biens for a SCI
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[BienResponse])
@router.get("/", response_model=list[BienResponse])
async def list_sci_biens(
    sci_id: UUID,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les biens d'une SCI."""
    client = _get_client()
    result = client.table("biens").select("*").eq("id_sci", str(sci_id)).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE bien for a SCI
# ──────────────────────────────────────────────────────────────

@router.post("", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
async def create_sci_bien(
    sci_id: UUID,
    payload: BienCreate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un bien dans la SCI (gérant uniquement)."""
    logger.info("creating_bien_nested", sci_id=str(sci_id), adresse=payload.adresse)

    client = _get_client()
    row = payload.model_dump(mode="json")
    # Force the sci_id from the URL path
    row["id_sci"] = str(sci_id)

    result = client.table("biens").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create bien")

    created = data[0]
    logger.info("bien_created_nested", bien_id=created.get("id"), sci_id=str(sci_id))
    return created


# ──────────────────────────────────────────────────────────────
# GET fiche bien (full detail view)
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}", response_model=FicheBienResponse)
async def get_fiche_bien(
    sci_id: UUID,
    bien_id: str,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Retourne la fiche complète d'un bien avec bail, loyers, charges, PNO, frais, documents et rentabilité."""
    client = _get_client()
    bien = _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Fetch related data in sequence (Supabase sync client)
    # Bail actif
    bail_actif = None
    bail_result = (
        client.table("baux")
        .select("*")
        .eq("id_bien", bien_id)
        .eq("statut", "en_cours")
        .limit(1)
        .execute()
    )
    if not getattr(bail_result, "error", None) and bail_result.data:
        bail_row = bail_result.data[0]
        # Fetch locataires linked to this bail
        locataires = []
        bail_id = bail_row.get("id")
        if bail_id:
            loc_result = (
                client.table("locataires")
                .select("id, nom, prenom, email, telephone")
                .eq("id_bail", bail_id)
                .execute()
            )
            if not getattr(loc_result, "error", None) and loc_result.data:
                locataires = loc_result.data
        bail_row["locataires"] = locataires
        bail_actif = bail_row

    # Loyers récents (last 12)
    loyers_result = (
        client.table("loyers")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_loyer", desc=True)
        .limit(12)
        .execute()
    )
    loyers_recents = []
    if not getattr(loyers_result, "error", None):
        loyers_recents = loyers_result.data or []

    # Charges
    charges_result = (
        client.table("charges")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_charge", desc=True)
        .execute()
    )
    charges_list = []
    if not getattr(charges_result, "error", None):
        charges_list = charges_result.data or []

    # Assurance PNO
    assurance_pno = None
    pno_result = (
        client.table("assurances_pno")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_debut", desc=True)
        .limit(1)
        .execute()
    )
    if not getattr(pno_result, "error", None) and pno_result.data:
        assurance_pno = pno_result.data[0]

    # Frais agence
    frais_result = (
        client.table("frais_agence")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_frais", desc=True)
        .execute()
    )
    frais_agence = []
    if not getattr(frais_result, "error", None):
        frais_agence = frais_result.data or []

    # Documents
    docs_result = (
        client.table("documents")
        .select("*")
        .eq("id_bien", bien_id)
        .order("created_at", desc=True)
        .execute()
    )
    documents = []
    if not getattr(docs_result, "error", None):
        documents = docs_result.data or []

    # Calculate rentabilite
    prime_pno = 0
    if assurance_pno:
        prime_pno = assurance_pno.get("prime_annuelle", 0) or 0

    frais_annuel = sum(f.get("montant", 0) or 0 for f in frais_agence)

    loyer_mensuel = bien.get("loyer_cc", 0) or bien.get("loyer", 0) or 0
    charges_mensuelles = bien.get("charges", 0) or 0
    prix_acquisition = bien.get("prix_acquisition")

    rentabilite = calculate_rentabilite(
        prix_acquisition=prix_acquisition,
        loyer_mensuel=loyer_mensuel,
        charges_mensuelles=charges_mensuelles,
        prime_pno_annuelle=prime_pno,
        frais_agence_annuel=frais_annuel,
    )

    # Build response, mapping DB fields to schema fields
    return FicheBienResponse(
        id=bien.get("id"),
        id_sci=bien.get("id_sci"),
        adresse=bien.get("adresse", ""),
        ville=bien.get("ville", ""),
        code_postal=bien.get("code_postal", ""),
        type_bien=bien.get("type_locatif", "appartement"),
        loyer=loyer_mensuel,
        charges=charges_mensuelles,
        surface_m2=bien.get("surface_m2"),
        nb_pieces=bien.get("nb_pieces"),
        dpe_classe=bien.get("dpe_classe"),
        photo_url=bien.get("photo_url"),
        prix_acquisition=prix_acquisition,
        statut=bien.get("statut"),
        bail_actif=bail_actif,
        loyers_recents=loyers_recents,
        charges_list=charges_list,
        assurance_pno=assurance_pno,
        frais_agence=frais_agence,
        documents=documents,
        rentabilite=RentabiliteCalculee(**rentabilite),
    )


# ──────────────────────────────────────────────────────────────
# UPDATE bien
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}", response_model=BienResponse)
async def update_sci_bien(
    sci_id: UUID,
    bien_id: str,
    payload: BienUpdate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un bien (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_bien_nested", bien_id=bien_id, sci_id=str(sci_id), fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("biens").update(update_payload).eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Bien", bien_id)

    logger.info("bien_updated_nested", bien_id=bien_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE bien
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sci_bien(
    sci_id: UUID,
    bien_id: str,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un bien (gérant uniquement)."""
    logger.info("deleting_bien_nested", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("biens").delete().eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("bien_deleted_nested", bien_id=bien_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# LIST loyers for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/loyers", response_model=list[LoyerResponse])
async def list_bien_loyers(
    sci_id: UUID,
    bien_id: str,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les loyers d'un bien."""
    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("loyers")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_loyer", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE loyer for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/loyers", response_model=LoyerResponse, status_code=status.HTTP_201_CREATED)
async def create_bien_loyer(
    sci_id: UUID,
    bien_id: str,
    payload: LoyerCreate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un loyer pour un bien (gérant uniquement)."""
    logger.info("creating_loyer_nested", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id
    row["id_sci"] = str(sci_id)

    result = client.table("loyers").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create loyer")

    created = data[0]
    logger.info("loyer_created_nested", loyer_id=created.get("id"), bien_id=bien_id)
    return created
