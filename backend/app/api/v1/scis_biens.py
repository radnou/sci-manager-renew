"""Nested biens API under /scis/{sci_id}/biens with fiche bien support."""

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

router = APIRouter(prefix="/scis/{sci_id}/biens", tags=["scis-biens"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    """Service client for INSERT operations — RLS blocks inserts before membership exists."""
    return get_supabase_service_client()


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
# Upload validation constants
# ──────────────────────────────────────────────────────────────

_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
_ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp", "doc", "docx", "xls", "xlsx", "csv", "txt"}
_MAGIC_BYTES = {
    b"%PDF": "pdf",
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG": "png",
    b"RIFF": "webp",  # WebP starts with RIFF
    b"PK": "docx",    # OOXML (docx, xlsx) are ZIP archives starting with PK
}


def _validate_upload(file_content: bytes, filename: str | None) -> str:
    """Validate uploaded file. Returns the sanitized extension.

    Raises ValidationError if file is invalid.
    """
    # Size check
    if len(file_content) > _MAX_UPLOAD_SIZE:
        raise ValidationError(f"Fichier trop volumineux (max {_MAX_UPLOAD_SIZE // (1024 * 1024)} Mo).")

    if len(file_content) == 0:
        raise ValidationError("Fichier vide.")

    # Extension check
    ext = ""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()

    if not ext or ext not in _ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Extension .{ext or '?'} non autorisée. Extensions acceptées: {', '.join(sorted(_ALLOWED_EXTENSIONS))}."
        )

    # Magic bytes check (basic — verify the file starts with expected bytes for known types)
    matched_type = None
    for magic, ftype in _MAGIC_BYTES.items():
        if file_content[: len(magic)] == magic:
            matched_type = ftype
            break

    # If we recognized a magic type, verify it's consistent with the extension
    if matched_type:
        consistent = False
        if matched_type == "docx" and ext in {"docx", "doc", "xlsx", "xls"}:
            consistent = True
        elif matched_type == "jpg" and ext in {"jpg", "jpeg"}:
            consistent = True
        elif matched_type == ext:
            consistent = True

        if not consistent:
            raise ValidationError(
                f"Le contenu du fichier ne correspond pas à l'extension .{ext}."
            )

    return ext


def _refresh_documents_urls(client, docs: list[dict]) -> list[dict]:
    """Return docs with fresh signed URLs for internal storage objects."""
    bucket = client.storage.from_("documents")
    refreshed_docs: list[dict] = []
    for doc in docs:
        refreshed = dict(doc)
        url = refreshed.get("url")
        if isinstance(url, str) and url:
            refreshed["url"] = create_document_signed_url(bucket, url)
        refreshed_docs.append(refreshed)
    return refreshed_docs


# ──────────────────────────────────────────────────────────────
# LIST biens for a SCI
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[BienResponse])
@router.get("/", response_model=list[BienResponse])
async def list_sci_biens(
    sci_id: UUID,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les biens d'une SCI avec statut d'occupation."""
    client = _get_client(request)
    result = client.table("biens").select("*").eq("id_sci", str(sci_id)).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    biens = result.data or []
    if not biens:
        return biens

    # Fetch active baux to determine occupation status
    bien_ids = [b["id"] for b in biens]
    baux_result = (
        client.table("baux")
        .select("id_bien")
        .in_("id_bien", bien_ids)
        .eq("statut", "en_cours")
        .execute()
    )
    occupied_ids = set()
    if baux_result.data:
        occupied_ids = {row["id_bien"] for row in baux_result.data}

    for bien in biens:
        if not bien.get("statut"):
            bien["statut"] = "loue" if bien["id"] in occupied_ids else "vacant"

    return biens


# ──────────────────────────────────────────────────────────────
# CREATE bien for a SCI
# ──────────────────────────────────────────────────────────────

@router.post("", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
async def create_sci_bien(
    sci_id: UUID,
    payload: BienCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un bien dans la SCI (gérant uniquement)."""
    SubscriptionService.enforce_limit(membership.user_id, "biens")

    logger.info("creating_bien_nested", sci_id=str(sci_id), adresse=payload.adresse)

    client = _get_client(request)
    row = payload.model_dump(mode="json")
    # Force the sci_id from the URL path
    row["id_sci"] = str(sci_id)

    write_client = _get_write_client()
    result = write_client.table("biens").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create bien")

    created = data[0]
    bien_id = str(created.get("id", ""))
    logger.info("bien_created_nested", bien_id=bien_id, sci_id=str(sci_id))

    # Auto-create "Acquisition" événement if acquisition data is provided
    if payload.prix_acquisition is not None and payload.acquisition_date is not None:
        total_cost = float(payload.prix_acquisition)
        frais_notaire = float(payload.frais_notaire or 0)
        frais_agence = float(payload.frais_agence_acquisition or 0)
        total_with_frais = total_cost + frais_notaire + frais_agence

        desc_parts = [f"Acquisition pour {total_cost} €."]
        if frais_notaire > 0:
            desc_parts.append(f"Frais de notaire : {frais_notaire} €.")
        if frais_agence > 0:
            desc_parts.append(f"Frais d'agence : {frais_agence} €.")
        desc_parts.append(f"Coût total : {total_with_frais} €.")

        evenement_data = {
            "id_bien": bien_id,
            "type": "acquisition",
            "titre": f"Acquisition — {payload.adresse}",
            "description": " ".join(desc_parts),
            "date_evenement": payload.acquisition_date.isoformat(),
            "montant": total_with_frais,
            "deductible_fiscalement": False,
        }
        try:
            write_client.table("evenements_bien").insert(evenement_data).execute()
            logger.info("acquisition_event_created", bien_id=bien_id)
        except Exception:
            logger.warning("acquisition_event_creation_failed", bien_id=bien_id, exc_info=True)

    return created


# ──────────────────────────────────────────────────────────────
# GET fiche bien (full detail view)
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}", response_model=FicheBienResponse)
async def get_fiche_bien(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Retourne la fiche complète d'un bien avec bail, loyers, charges, PNO, frais, documents et rentabilité."""
    client = _get_client(request)
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
                client.table("bail_locataires")
                .select("locataires(id, nom, email, telephone)")
                .eq("id_bail", bail_id)
                .execute()
            )
            if not getattr(loc_result, "error", None) and loc_result.data:
                locataires = [
                    row["locataires"]
                    for row in loc_result.data
                    if row.get("locataires")
                ]
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
        .order("date_paiement", desc=True)
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
        .order("date_echeance", desc=True)
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
        .order("created_at", desc=True)
        .execute()
    )
    frais_agence = []
    if not getattr(frais_result, "error", None):
        frais_agence = frais_result.data or []

    # Documents
    docs_result = (
        client.table("documents_bien")
        .select("*")
        .eq("id_bien", bien_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    documents = []
    if not getattr(docs_result, "error", None):
        documents = _refresh_documents_urls(client, docs_result.data or [])

    # Calculate rentabilite
    prime_pno = 0
    if assurance_pno:
        prime_pno = assurance_pno.get("montant_annuel", 0) or 0

    loyer_hc = 0
    if bail_actif:
        loyer_hc = bail_actif.get("loyer_hc", 0) or 0
    frais_annuel = 0
    for f in frais_agence:
        montant = f.get("montant_ou_pourcentage", 0) or 0
        if f.get("type_frais") == "pourcentage":
            frais_annuel += loyer_hc * 12 * montant / 100
        else:
            frais_annuel += montant * 12 if montant > 100 else montant

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
        type_locatif=bien.get("type_locatif", "appartement"),
        type_bien=bien.get("type_bien"),
        loyer_cc=loyer_mensuel,
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
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un bien (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_bien_nested", bien_id=bien_id, sci_id=str(sci_id), fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
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
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un bien (gérant uniquement)."""
    logger.info("deleting_bien_nested", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
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
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les loyers d'un bien."""
    client = _get_client(request)
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
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un loyer pour un bien (gérant uniquement)."""
    SubscriptionService.enforce_limit(membership.user_id, "biens")

    logger.info("creating_loyer_nested", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id
    row["id_sci"] = str(sci_id)

    existing = client.table("loyers").select("id").eq("id_bien", bien_id).eq("date_loyer", row["date_loyer"]).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Un loyer existe déjà pour ce bien à cette date")

    write_client = _get_write_client()
    result = write_client.table("loyers").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create loyer")

    created = data[0]
    logger.info("loyer_created_nested", loyer_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# LIST baux for a bien (history)
# ──────────────────────────────────────────────────────────────

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
    if not getattr(existing, "error", None) and existing.data:
        for old_bail in existing.data:
            client.table("baux").update({"statut": "expire"}).eq("id", old_bail["id"]).execute()
            logger.info("bail_expired", bail_id=old_bail["id"])

    # 2. Insert new bail
    locataire_ids = payload.locataire_ids
    row = payload.model_dump(mode="json", exclude={"locataire_ids"})
    row["id_bien"] = bien_id
    row["statut"] = "en_cours"

    write_client = _get_write_client()
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


@router.post("/{bien_id}/baux/{bail_id}/cloturer", response_model=BailResponse)
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
    }
    if payload.etat_lieux_sortie:
        update_data["etat_lieux_sortie"] = payload.etat_lieux_sortie.isoformat()

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


def _calculate_date_effet(date_notification: date, type_conge: str, type_locatif: str) -> date:
    """Calculate date_effet based on préavis rules.

    - Locataire nu: 3 mois (1 mois en zone tendue, but we default to 3)
    - Locataire meublé: 1 mois
    - Bailleur: 6 mois
    """
    if type_conge == "bailleur":
        return date_notification + timedelta(days=183)  # ~6 mois

    # Locataire
    if type_locatif == "meuble":
        return date_notification + timedelta(days=30)  # 1 mois
    return date_notification + timedelta(days=91)  # ~3 mois (nu / default)


@router.post("/{bien_id}/baux/{bail_id}/conge", response_model=BailResponse)
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
    date_effet = payload.date_effet or _calculate_date_effet(
        payload.date_notification, payload.type_conge, type_locatif
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


# ──────────────────────────────────────────────────────────────
# LIST charges for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/charges", response_model=list[ChargeResponse])
async def list_bien_charges(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les charges d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("charges")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_paiement", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE charge for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/charges", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_bien_charge(
    sci_id: UUID,
    bien_id: str,
    payload: ChargeCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée une charge pour un bien (gérant uniquement)."""
    logger.info("creating_charge", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id
    # Note: charges table has no id_sci column — scoping is via id_bien → biens.id_sci

    write_client = _get_write_client()
    result = write_client.table("charges").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create charge")

    created = data[0]
    logger.info("charge_created", charge_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE charge
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}/charges/{charge_id}", response_model=ChargeResponse)
async def update_bien_charge(
    sci_id: UUID,
    bien_id: str,
    charge_id: str,
    payload: ChargeUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour une charge (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_charge", charge_id=charge_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("charges")
        .update(update_payload)
        .eq("id", charge_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Charge", charge_id)

    logger.info("charge_updated", charge_id=charge_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE charge
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/charges/{charge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien_charge(
    sci_id: UUID,
    bien_id: str,
    charge_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime une charge (gérant uniquement)."""
    logger.info("deleting_charge", charge_id=charge_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("charges").delete().eq("id", charge_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("charge_deleted", charge_id=charge_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# GET assurance PNO for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/assurance-pno", response_model=list[AssurancePnoResponse])
async def list_bien_assurance_pno(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les assurances PNO d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("assurances_pno")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_debut", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE assurance PNO
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/assurance-pno", response_model=AssurancePnoResponse, status_code=status.HTTP_201_CREATED)
async def create_bien_assurance_pno(
    sci_id: UUID,
    bien_id: str,
    payload: AssurancePnoCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée une assurance PNO pour un bien (gérant uniquement)."""
    logger.info("creating_assurance_pno", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    write_client = _get_write_client()
    result = write_client.table("assurances_pno").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create assurance PNO")

    created = data[0]
    logger.info("assurance_pno_created", pno_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE assurance PNO
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}/assurance-pno/{pno_id}", response_model=AssurancePnoResponse)
async def update_bien_assurance_pno(
    sci_id: UUID,
    bien_id: str,
    pno_id: int,
    payload: AssurancePnoUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour une assurance PNO (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_assurance_pno", pno_id=pno_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("assurances_pno")
        .update(update_payload)
        .eq("id", pno_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("AssurancePno", str(pno_id))

    logger.info("assurance_pno_updated", pno_id=pno_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE assurance PNO
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/assurance-pno/{pno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien_assurance_pno(
    sci_id: UUID,
    bien_id: str,
    pno_id: int,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime une assurance PNO (gérant uniquement)."""
    logger.info("deleting_assurance_pno", pno_id=pno_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("assurances_pno").delete().eq("id", pno_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("assurance_pno_deleted", pno_id=pno_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# LIST frais agence for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/frais-agence", response_model=list[FraisAgenceResponse])
async def list_bien_frais_agence(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les frais d'agence d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("frais_agence")
        .select("*")
        .eq("id_bien", bien_id)
        .order("created_at", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE frais agence
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/frais-agence", response_model=FraisAgenceResponse, status_code=status.HTTP_201_CREATED)
async def create_bien_frais_agence(
    sci_id: UUID,
    bien_id: str,
    payload: FraisAgenceCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un frais d'agence pour un bien (gérant uniquement)."""
    logger.info("creating_frais_agence", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    write_client = _get_write_client()
    result = write_client.table("frais_agence").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create frais agence")

    created = data[0]
    logger.info("frais_agence_created", frais_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# DELETE frais agence
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/frais-agence/{frais_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien_frais_agence(
    sci_id: UUID,
    bien_id: str,
    frais_id: int,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un frais d'agence (gérant uniquement)."""
    logger.info("deleting_frais_agence", frais_id=frais_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("frais_agence").delete().eq("id", frais_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("frais_agence_deleted", frais_id=frais_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# LIST documents for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/documents", response_model=list[DocumentBienResponse])
async def list_bien_documents(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les documents d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("documents_bien")
        .select("*")
        .eq("id_bien", bien_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return _refresh_documents_urls(client, result.data or [])


# ──────────────────────────────────────────────────────────────
# UPLOAD document for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/documents", response_model=DocumentBienResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    file: UploadFile = File(...),
    nom: str = Form(...),
    categorie: str = Form("autre"),
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Upload un document pour un bien (gérant uniquement)."""
    logger.info("uploading_document", bien_id=bien_id, sci_id=str(sci_id), nom=nom, categorie=categorie)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Read file content
    file_content = await file.read()

    # Validate upload (size, extension, magic bytes)
    file_ext = _validate_upload(file_content, file.filename)

    import uuid as _uuid
    storage_path = f"sci-{sci_id}/bien-{bien_id}/{_uuid.uuid4().hex}.{file_ext}"

    # Upload to Supabase Storage bucket "documents"
    try:
        client.storage.from_("documents").upload(
            storage_path,
            file_content,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception as exc:
        logger.error("document_upload_failed", error=str(exc))
        raise DatabaseError(f"Upload failed: {exc}")

    # Generate a time-limited signed URL (24 h) instead of a public URL
    try:
        url = create_document_signed_url(client.storage.from_("documents"), storage_path, 86400)
    except DatabaseError:
        logger.error("signed_url_empty", storage_path=storage_path)
        raise

    # Insert record into documents table
    from datetime import datetime, timezone
    row = {
        "id_bien": bien_id,
        "nom": nom,
        "categorie": categorie,
        "url": url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    write_client = _get_write_client()
    result = write_client.table("documents_bien").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create document record")

    created = data[0]
    logger.info("document_uploaded", doc_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# DELETE document
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    sci_id: UUID,
    bien_id: str,
    doc_id: int,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un document (gérant uniquement).

    Security: verifies the document belongs to the bien which belongs to the
    SCI the authenticated user is gérant of before allowing deletion.
    """
    logger.info("deleting_document", doc_id=doc_id, bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # --- Ownership check: confirm the document exists and belongs to this bien ---
    doc_result = (
        client.table("documents_bien")
        .select("id, id_bien, url")
        .eq("id", doc_id)
        .execute()
    )
    if getattr(doc_result, "error", None):
        raise DatabaseError(str(doc_result.error))

    doc_rows = doc_result.data or []
    if not doc_rows:
        raise ResourceNotFoundError("Document", str(doc_id))

    doc = doc_rows[0]
    if str(doc.get("id_bien", "")) != bien_id:
        # Document exists but does not belong to this bien — treat as not found
        # to avoid leaking document existence to unauthorized users.
        raise ResourceNotFoundError("Document", str(doc_id))

    # --- Delete the file from Supabase Storage ---
    doc_url = doc.get("url", "")
    if doc_url:
        storage_path = extract_document_storage_path(doc_url)
        if storage_path:
            try:
                client.storage.from_("documents").remove([storage_path])
                logger.info("storage_file_deleted", path=storage_path)
            except Exception as exc:
                # Log but do not block the DB record deletion — the file may
                # already have been removed or the path may be stale.
                logger.warning("storage_file_delete_failed", path=storage_path, error=str(exc))

    # --- Delete the database record ---
    result = client.table("documents_bien").delete().eq("id", doc_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("document_deleted", doc_id=doc_id, bien_id=bien_id, sci_id=str(sci_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# LIST evenements for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/evenements", response_model=list[EvenementResponse])
async def list_bien_evenements(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    annee: int | None = Query(default=None, description="Filtrer par année"),
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les événements d'un bien, avec filtre optionnel par année."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    query = (
        client.table("evenements_bien")
        .select("*")
        .eq("id_bien", bien_id)
    )

    if annee is not None:
        query = query.gte("date_evenement", f"{annee}-01-01").lte("date_evenement", f"{annee}-12-31")

    result = query.order("date_evenement", desc=True).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE evenement for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/evenements", response_model=EvenementResponse, status_code=status.HTTP_201_CREATED)
async def create_bien_evenement(
    sci_id: UUID,
    bien_id: str,
    payload: EvenementCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un événement pour un bien (gérant uniquement)."""
    logger.info("creating_evenement", bien_id=bien_id, sci_id=str(sci_id), type=payload.type)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    write_client = _get_write_client()
    result = write_client.table("evenements_bien").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create evenement")

    created = data[0]
    logger.info("evenement_created", event_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE evenement
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}/evenements/{event_id}", response_model=EvenementResponse)
async def update_bien_evenement(
    sci_id: UUID,
    bien_id: str,
    event_id: str,
    payload: EvenementUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un événement (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_evenement", event_id=event_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("evenements_bien")
        .update(update_payload)
        .eq("id", event_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Evenement", event_id)

    logger.info("evenement_updated", event_id=event_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE evenement
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/evenements/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien_evenement(
    sci_id: UUID,
    bien_id: str,
    event_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un événement (gérant uniquement)."""
    logger.info("deleting_evenement", event_id=event_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("evenements_bien").delete().eq("id", event_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("evenement_deleted", event_id=event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# GET obligations for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/obligations")
async def get_bien_obligations(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Retourne le statut des obligations réglementaires d'un bien."""
    from app.services.obligations_service import get_obligations

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    return get_obligations(client, bien_id)


# ──────────────────────────────────────────────────────────────
# AVENANT BAIL — POST /scis/{sci_id}/biens/{bien_id}/baux/{bail_id}/avenant
# ──────────────────────────────────────────────────────────────

AVENANT_TYPES = {"revision_loyer", "modification_charges", "ajout_locataire", "changement_destination"}


class AvenantCreate(BaseModel):
    type_avenant: str
    nouveau_loyer_hc: Optional[float] = None
    nouvelles_charges: Optional[float] = None
    date_effet: date
    motif: str


class AvenantResponse(BaseModel):
    avenant: dict
    bail_updated: dict


@router.post("/{bien_id}/baux/{bail_id}/avenant", response_model=AvenantResponse, status_code=status.HTTP_201_CREATED)
async def create_avenant(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    payload: AvenantCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Create an avenant (amendment) to an existing bail."""
    if payload.type_avenant not in AVENANT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"type_avenant invalide. Valeurs acceptees : {', '.join(sorted(AVENANT_TYPES))}",
        )

    logger.info(
        "creating_avenant",
        bail_id=bail_id,
        bien_id=bien_id,
        sci_id=str(sci_id),
        type_avenant=payload.type_avenant,
    )

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Verify the bail exists
    bail_result = client.table("baux").select("*").eq("id", bail_id).eq("id_bien", bien_id).execute()
    if getattr(bail_result, "error", None) or not bail_result.data:
        raise ResourceNotFoundError("Bail", bail_id)

    bail = bail_result.data[0]

    # Build update payload for the bail based on avenant type
    bail_update: dict = {}
    if payload.type_avenant == "revision_loyer" and payload.nouveau_loyer_hc is not None:
        bail_update["loyer_hc"] = payload.nouveau_loyer_hc
    elif payload.type_avenant == "modification_charges" and payload.nouvelles_charges is not None:
        bail_update["charges_locatives"] = payload.nouvelles_charges

    # Update the bail if there are changes
    if bail_update:
        update_result = (
            client.table("baux")
            .update(bail_update)
            .eq("id", bail_id)
            .execute()
        )
        if getattr(update_result, "error", None):
            raise DatabaseError(str(update_result.error))
        bail.update(bail_update)

    # Store avenant as an evenement_bien
    avenant_metadata = payload.model_dump(mode="json")
    avenant_metadata["ancien_loyer_hc"] = bail_result.data[0].get("loyer_hc")
    avenant_metadata["anciennes_charges"] = bail_result.data[0].get("charges_locatives")

    evenement_row = {
        "id_bien": bien_id,
        "type": "avenant",
        "titre": f"Avenant : {payload.type_avenant.replace('_', ' ')}",
        "description": payload.motif,
        "date_evenement": payload.date_effet.isoformat(),
        "montant": payload.nouveau_loyer_hc,
        "deductible_fiscalement": False,
    }

    write_client = _get_write_client()
    evt_result = write_client.table("evenements_bien").insert(evenement_row).execute()
    if getattr(evt_result, "error", None):
        raise DatabaseError(str(evt_result.error))

    created_event = (evt_result.data or [{}])[0]

    # Create notification for SCI owners
    from app.services.notification_service import create_notification_with_email

    owners = (
        client.table("associes")
        .select("user_id")
        .eq("id_sci", str(sci_id))
        .not_.is_("user_id", "null")
        .execute()
    )
    for owner in (owners.data or []):
        await create_notification_with_email(
            write_client,
            user_id=owner["user_id"],
            notification_type="avenant_bail",
            data={
                "title": f"Avenant bail — {payload.type_avenant.replace('_', ' ')}",
                "message": f"{payload.motif} (effet au {payload.date_effet.isoformat()})",
                "metadata": {
                    "bail_id": bail_id,
                    "bien_id": bien_id,
                    "type_avenant": payload.type_avenant,
                    "dedup_key": f"avenant_{bail_id}_{payload.date_effet.isoformat()}",
                },
            },
        )

    logger.info("avenant_created", bail_id=bail_id, event_id=created_event.get("id"))
    return AvenantResponse(avenant=created_event, bail_updated=bail)


# ──────────────────────────────────────────────────────────────
# SINISTRE PNO — POST /scis/{sci_id}/biens/{bien_id}/sinistre
# ──────────────────────────────────────────────────────────────


class SinistreCreate(BaseModel):
    date_sinistre: date
    description: str
    montant_estime: Optional[float] = None
    numero_dossier: Optional[str] = None


class SinistreResponse(BaseModel):
    evenement: dict
    assurance_pno: Optional[dict] = None


@router.post("/{bien_id}/sinistre", response_model=SinistreResponse, status_code=status.HTTP_201_CREATED)
async def declare_sinistre(
    sci_id: UUID,
    bien_id: str,
    payload: SinistreCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Declare a sinistre (insurance claim) linked to PNO insurance."""
    logger.info("declaring_sinistre", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    bien = _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Fetch PNO insurance for the bien
    pno_result = (
        client.table("assurances_pno")
        .select("*")
        .eq("id_bien", bien_id)
        .execute()
    )
    pno_info = (pno_result.data or [None])[0] if pno_result.data else None

    # Build the titre with numero_dossier if provided
    titre = "Sinistre"
    if payload.numero_dossier:
        titre = f"Sinistre {payload.numero_dossier}"

    # Create evenement for the sinistre
    evenement_row = {
        "id_bien": bien_id,
        "type": "sinistre",
        "titre": titre,
        "description": payload.description,
        "date_evenement": payload.date_sinistre.isoformat(),
        "montant": payload.montant_estime,
        "deductible_fiscalement": False,
    }

    write_client = _get_write_client()
    evt_result = write_client.table("evenements_bien").insert(evenement_row).execute()
    if getattr(evt_result, "error", None):
        raise DatabaseError(str(evt_result.error))

    created_event = (evt_result.data or [{}])[0]

    # Create notification with PNO assureur details
    from app.services.notification_service import create_notification_with_email

    adresse = bien.get("adresse", "un bien")
    assureur = pno_info.get("compagnie", "N/A") if pno_info else "Aucune PNO"

    owners = (
        client.table("associes")
        .select("user_id")
        .eq("id_sci", str(sci_id))
        .not_.is_("user_id", "null")
        .execute()
    )
    for owner in (owners.data or []):
        await create_notification_with_email(
            write_client,
            user_id=owner["user_id"],
            notification_type="sinistre",
            data={
                "title": f"Sinistre declare — {adresse}",
                "message": (
                    f"{payload.description}. "
                    f"Montant estime : {payload.montant_estime or 'N/A'} EUR. "
                    f"Assureur PNO : {assureur}."
                ),
                "metadata": {
                    "bien_id": bien_id,
                    "event_id": created_event.get("id"),
                    "numero_dossier": payload.numero_dossier,
                    "dedup_key": f"sinistre_{bien_id}_{payload.date_sinistre.isoformat()}",
                },
            },
        )

    logger.info("sinistre_declared", event_id=created_event.get("id"), bien_id=bien_id)
    return SinistreResponse(evenement=created_event, assurance_pno=pno_info)
