from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel

from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client
from app.core.exceptions import DatabaseError, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.services.subscription_service import SubscriptionService
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.models.charges import ChargeCreate, ChargeResponse, ChargeUpdate
from app.models.evenements import EvenementCreate, EvenementResponse, EvenementUpdate
from app.models.loyers import LoyerCreate, LoyerResponse
from app.schemas.assurance_pno import AssurancePnoCreate, AssurancePnoResponse, AssurancePnoUpdate
from app.schemas.baux import BailCreate, BailResponse, BailUpdate
from app.schemas.documents import DocumentBienResponse
from app.schemas.fiche_bien import FicheBienResponse, RentabiliteCalculee
from app.schemas.frais_agence import FraisAgenceCreate, FraisAgenceResponse
from app.services.document_links import create_document_signed_url, extract_document_storage_path
from app.services.rentabilite_service import calculate_rentabilite

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["scis-biens"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    return get_supabase_service_client()


def _verify_bien_belongs_to_sci(client, bien_id: str, sci_id: str) -> dict:
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


@router.get("/{bien_id}/baux", response_model=list[BailResponse])
async def list_bien_baux(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste tous les baux d'un bien (historique complet)."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("baux")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_debut", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    baux = result.data or []

    # Enrich each bail with its locataires via bail_locataires join table
    for bail in baux:
        bail_id = bail.get("id")
        locataires = []
        if bail_id:
            loc_result = (
                client.table("bail_locataires")
                .select("locataires(id, nom, email, telephone)")
                .eq("id_bail", bail_id)
                .execute()
            )
            if not getattr(loc_result, "error", None) and loc_result.data:
                for row in loc_result.data:
                    if row.get("locataires"):
                        locataires.append(row["locataires"])
        bail["locataires"] = locataires

    return baux


# ──────────────────────────────────────────────────────────────
# CREATE bail for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/baux", response_model=BailResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_bien_bail(
    sci_id: UUID,
    bien_id: str,
    payload: BailCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un bail pour un bien (gérant uniquement). Expire le bail en_cours existant."""
    SubscriptionService.enforce_limit(membership.user_id, "biens")

    logger.info("creating_bail", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    bien = _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Validate minimum bail duration based on type_locatif
    if payload.date_fin:
        type_locatif = (bien.get("type_locatif") or "").lower()
        duration_days = (payload.date_fin - payload.date_debut).days
        _MINIMUM_DURATIONS = {
            "nu": (1095, "3 ans"),
            "meuble": (365, "1 an"),
            "mobilite": (30, "1 mois"),
        }
        if type_locatif in _MINIMUM_DURATIONS:
            min_days, label = _MINIMUM_DURATIONS[type_locatif]
            if duration_days < min_days:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Durée minimale légale pour un bail {type_locatif} : {label}. "
                        f"Durée fournie : {duration_days} jours."
                    ),
                )

    # Validate depot de garantie cap based on type_locatif
    if payload.depot_garantie > 0 and payload.loyer_hc > 0:
        type_locatif = (bien.get("type_locatif") or "").lower()
        _DEPOT_CAPS = {
            "nu": (1, "1 mois de loyer HC"),
            "meuble": (2, "2 mois de loyer HC"),
            "mobilite": (0, "aucun dépôt de garantie (bail mobilité)"),
        }
        if type_locatif in _DEPOT_CAPS:
            max_months, label = _DEPOT_CAPS[type_locatif]
            max_depot = payload.loyer_hc * max_months
            if payload.depot_garantie > max_depot:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Dépôt de garantie ({payload.depot_garantie:.2f} EUR) dépasse le plafond légal "
                        f"pour un bail {type_locatif} : {label} ({max_depot:.2f} EUR). "
                        f"Article 22 loi du 6 juillet 1989."
                    ),
                )

    # 1. Expire existing en_cours bail
    existing = (
        client.table("baux")
        .select("id")
        .eq("id_bien", bien_id)
        .eq("statut", "en_cours")
        .execute()
    )
    write_client = _get_write_client()

    if not getattr(existing, "error", None) and existing.data:
        for old_bail in existing.data:
            write_client.table("baux").update({"statut": "expire"}).eq("id", old_bail["id"]).execute()
            logger.info("bail_expired", bail_id=old_bail["id"])

    # 2. Insert new bail
    locataire_ids = payload.locataire_ids
    row = payload.model_dump(mode="json", exclude={"locataire_ids"})
    row["id_bien"] = bien_id
    row["statut"] = "en_cours"
    result = write_client.table("baux").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create bail")

    created = data[0]
    bail_id = created["id"]

    # 3. Attach locataires via bail_locataires join table
    locataires = []
    for loc_id in locataire_ids:
        join_row = {"id_bail": bail_id, "id_locataire": loc_id}
        write_client.table("bail_locataires").insert(join_row).execute()
        loc_detail = (
            client.table("locataires")
            .select("id, nom, email, telephone")
            .eq("id", loc_id)
            .execute()
        )
        if not getattr(loc_detail, "error", None) and loc_detail.data:
            locataires.append(loc_detail.data[0])

    created["locataires"] = locataires
    logger.info("bail_created", bail_id=bail_id, bien_id=bien_id, locataires_count=len(locataire_ids))
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE bail
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}/baux/{bail_id}", response_model=BailResponse)
@limiter.limit("30/minute")
async def update_bien_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    payload: BailUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un bail (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_bail", bail_id=bail_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("baux")
        .update(update_payload)
        .eq("id", bail_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    bail = data[0]

    # Fetch locataires
    loc_result = (
        client.table("bail_locataires")
        .select("locataires(id, nom, email, telephone)")
        .eq("id_bail", bail_id)
        .execute()
    )
    locataires = []
    if not getattr(loc_result, "error", None) and loc_result.data:
        for row in loc_result.data:
            if row.get("locataires"):
                locataires.append(row["locataires"])

    bail["locataires"] = locataires
    logger.info("bail_updated", bail_id=bail_id)
    return bail


# ──────────────────────────────────────────────────────────────
# DELETE bail
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/baux/{bail_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_bien_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un bail (gérant uniquement)."""
    logger.info("deleting_bail", bail_id=bail_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Delete join table entries first
    client.table("bail_locataires").delete().eq("id_bail", bail_id).execute()

    result = client.table("baux").delete().eq("id", bail_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("bail_deleted", bail_id=bail_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# CLOTURER bail (terminate with état des lieux + dépôt)
# ──────────────────────────────────────────────────────────────

class BailCloturePayload(BaseModel):
    date_fin_effective: date
    etat_lieux_sortie: Optional[date] = None
    depot_restitue_montant: Optional[float] = None
    retenues_detail: Optional[str] = None
    motif: Optional[str] = None
    depot_restitue: bool = False
    date_restitution: Optional[date] = None


@router.post("/{bien_id}/baux/{bail_id}/cloturer", response_model=BailResponse)
@limiter.limit("30/minute")
async def cloturer_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    payload: BailCloturePayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Clôture un bail : passage statut → terminé, mise à jour date_fin et état des lieux sortie."""
    logger.info("cloturing_bail", bail_id=bail_id, bien_id=bien_id, motif=payload.motif)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Verify bail exists and is en_cours
    bail_result = (
        client.table("baux")
        .select("*")
        .eq("id", bail_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if not bail_result.data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    existing = bail_result.data[0]
    if existing.get("statut") == "termine":
        raise ValidationError("Ce bail est déjà clôturé.")

    update_data: dict = {
        "statut": "termine",
        "date_fin": payload.date_fin_effective.isoformat(),
        "depot_restitue": payload.depot_restitue,
    }
    if payload.etat_lieux_sortie:
        update_data["etat_lieux_sortie"] = payload.etat_lieux_sortie.isoformat()
    if payload.date_restitution:
        update_data["date_restitution"] = payload.date_restitution.isoformat()

    result = (
        client.table("baux")
        .update(update_data)
        .eq("id", bail_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    bail = data[0]

    # Fetch locataires for response
    loc_result = (
        client.table("bail_locataires")
        .select("locataires(id, nom, email, telephone)")
        .eq("id_bail", bail_id)
        .execute()
    )
    locataires = []
    if not getattr(loc_result, "error", None) and loc_result.data:
        for row in loc_result.data:
            if row.get("locataires"):
                locataires.append(row["locataires"])

    bail["locataires"] = locataires
    logger.info("bail_cloture", bail_id=bail_id, date_fin=payload.date_fin_effective.isoformat())
    return bail


# ──────────────────────────────────────────────────────────────
# CONGE bail (notice to quit — locataire or bailleur)
# ──────────────────────────────────────────────────────────────

_VALID_CONGE_TYPES = {"locataire", "bailleur"}
_VALID_MOTIFS_BAILLEUR = {"Reprise pour habiter", "Vente", "Motif légitime"}


class CongePayload(BaseModel):
    type_conge: str
    date_notification: date
    motif: Optional[str] = None
    date_effet: Optional[date] = None  # If omitted, calculated from préavis


def _calculate_date_effet(
    date_notification: date,
    type_conge: str,
    type_locatif: str,
    zone_tendue: bool = False,
) -> date:
    """Calculate date_effet based on préavis rules.

    - Locataire nu: 3 mois (1 mois en zone tendue — loi Alur)
    - Locataire meublé / mobilite: 1 mois
    - Bailleur: 6 mois
    """
    if type_conge == "bailleur":
        return date_notification + timedelta(days=183)  # ~6 mois

    # Locataire
    if type_locatif in ("meuble", "mobilite"):
        return date_notification + timedelta(days=30)  # 1 mois
    # Nu: 1 mois en zone tendue, 3 mois sinon
    if zone_tendue:
        return date_notification + timedelta(days=30)
    return date_notification + timedelta(days=91)  # ~3 mois (nu / default)


@router.post("/{bien_id}/baux/{bail_id}/conge", response_model=BailResponse)
@limiter.limit("30/minute")
async def conge_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    payload: CongePayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Enregistre un congé (départ locataire ou congé bailleur) sur un bail."""
    if payload.type_conge not in _VALID_CONGE_TYPES:
        raise ValidationError(f"type_conge doit être l'un de : {', '.join(_VALID_CONGE_TYPES)}")

    if payload.type_conge == "bailleur" and payload.motif and payload.motif not in _VALID_MOTIFS_BAILLEUR:
        raise ValidationError(f"Motif bailleur invalide. Valeurs acceptées : {', '.join(_VALID_MOTIFS_BAILLEUR)}")

    logger.info("conge_bail", bail_id=bail_id, bien_id=bien_id, type_conge=payload.type_conge)

    client = _get_client(request)
    bien = _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Verify bail exists and is en_cours
    bail_result = (
        client.table("baux")
        .select("*")
        .eq("id", bail_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if not bail_result.data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    existing = bail_result.data[0]
    if existing.get("statut") == "termine":
        raise ValidationError("Impossible d'enregistrer un congé sur un bail terminé.")

    if existing.get("date_conge"):
        raise ValidationError("Un congé est déjà enregistré sur ce bail.")

    # Calculate date_effet
    type_locatif = (bien.get("type_locatif") or "").lower()
    zone_tendue = bool(bien.get("zone_tendue", False))
    date_effet = payload.date_effet or _calculate_date_effet(
        payload.date_notification, payload.type_conge, type_locatif, zone_tendue
    )

    update_data = {
        "date_conge": date_effet.isoformat(),
        "motif_conge": payload.motif or "",
        "type_conge": payload.type_conge,
    }

    result = (
        client.table("baux")
        .update(update_data)
        .eq("id", bail_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    bail = data[0]

    # Fetch locataires for response
    loc_result = (
        client.table("bail_locataires")
        .select("locataires(id, nom, email, telephone)")
        .eq("id_bail", bail_id)
        .execute()
    )
    locataires = []
    if not getattr(loc_result, "error", None) and loc_result.data:
        for row in loc_result.data:
            if row.get("locataires"):
                locataires.append(row["locataires"])

    bail["locataires"] = locataires

    # Create notification for the gérant
    try:
        from app.services.notification_service import create_notification_with_email
        from app.core.supabase_client import get_supabase_service_client as _get_notif_client

        notif_client = _get_notif_client()
        label = "locataire" if payload.type_conge == "locataire" else "bailleur"
        await create_notification_with_email(
            notif_client,
            membership.user_id,
            "conge_bail",
            {
                "title": f"Congé {label} enregistré",
                "message": f"Congé {label} enregistré sur le bail du bien {bien.get('adresse', '')}. Date d'effet : {date_effet.isoformat()}.",
                "metadata": {
                    "bail_id": bail_id,
                    "bien_id": bien_id,
                    "sci_id": str(sci_id),
                    "type_conge": payload.type_conge,
                    "date_effet": date_effet.isoformat(),
                    "dedup_key": f"conge_{bail_id}",
                },
            },
        )
    except Exception:
        logger.warning("conge_notification_failed", bail_id=bail_id, exc_info=True)

    logger.info("conge_registered", bail_id=bail_id, type_conge=payload.type_conge, date_effet=date_effet.isoformat())
    return bail


# ──────────────────────────────────────────────────────────────
# ATTACH locataire to bail
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/baux/{bail_id}/locataires", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def attach_locataire_to_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    body: dict,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Attache un locataire à un bail (colocation)."""
    locataire_id = body.get("locataire_id")
    if not locataire_id:
        raise DatabaseError("locataire_id is required")

    logger.info("attaching_locataire", bail_id=bail_id, locataire_id=locataire_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Verify bail exists for this bien
    bail_result = client.table("baux").select("id").eq("id", bail_id).eq("id_bien", bien_id).execute()
    if not bail_result.data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    join_row = {"id_bail": bail_id, "id_locataire": locataire_id}
    write_client = _get_write_client()
    result = write_client.table("bail_locataires").insert(join_row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("locataire_attached", bail_id=bail_id, locataire_id=locataire_id)
    return {"id_bail": bail_id, "id_locataire": locataire_id}


# ──────────────────────────────────────────────────────────────
# DETACH locataire from bail
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/baux/{bail_id}/locataires/{locataire_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def detach_locataire_from_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    locataire_id: int,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Détache un locataire d'un bail."""
    logger.info("detaching_locataire", bail_id=bail_id, locataire_id=locataire_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("bail_locataires")
        .delete()
        .eq("id_bail", bail_id)
        .eq("id_locataire", locataire_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("locataire_detached", bail_id=bail_id, locataire_id=locataire_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# Regularisation annuelle des charges
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/baux/{bail_id}/regularisation/{annee}")
async def get_regularisation(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    annee: int,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Calcule la regularisation annuelle des charges pour un bail."""
    from app.services.regularisation_service import calculate_regularisation

    logger.info("calculating_regularisation", bail_id=bail_id, annee=annee)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    try:
        result = calculate_regularisation(client, bail_id, annee)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return result


class RegularisationConfirmPayload(BaseModel):
    annee: int
    notes: str | None = None


@router.post("/{bien_id}/baux/{bail_id}/regularisation", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def confirm_regularisation_endpoint(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    payload: RegularisationConfirmPayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Confirme et persiste la regularisation annuelle (gerant uniquement)."""
    from app.services.regularisation_service import confirm_regularisation

    logger.info("confirming_regularisation", bail_id=bail_id, annee=payload.annee)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    write_client = _get_write_client()
    try:
        result = confirm_regularisation(
            write_client,
            bien_id=bien_id,
            bail_id=bail_id,
            annee=payload.annee,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return result


# ──────────────────────────────────────────────────────────────
# LIST charges for a bien
# ──────────────────────────────────────────────────────────────
