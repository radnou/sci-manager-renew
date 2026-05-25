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


"""Nested biens API under /scis/{sci_id}/biens with fiche bien support."""


# ──────────────────────────────────────────────────────────────
# Upload validation constants
# ──────────────────────────────────────────────────────────────

_MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB
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
        url = refreshed.get("file_url") or refreshed.get("url")
        if isinstance(url, str) and url:
            refreshed["url"] = create_document_signed_url(bucket, url)
        refreshed_docs.append(refreshed)
    return refreshed_docs



# ──────────────────────────────────────────────────────────────
# LIST biens for a SCI
# ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[BienResponse])
async def list_sci_biens(
    sci_id: UUID,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """Liste les biens d'une SCI avec statut d'occupation."""
    client = _get_client(request)
    start = (page - 1) * page_size
    end = start + page_size - 1
    result = (
        client.table("biens")
        .select("*")
        .eq("id_sci", str(sci_id))
        .range(start, end)
        .execute()
    )
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
        # Compute rentabilite on the fly from existing columns
        loyer_cc = float(bien.get("loyer_cc") or 0)
        prix = float(bien.get("prix_acquisition") or 0)
        charges = float(bien.get("charges") or 0)
        frais_notaire = float(bien.get("frais_notaire") or 0)
        frais_agence = float(bien.get("frais_agence_acquisition") or 0)
        
        # Prix total d'acquisition (prix + frais)
        prix_total = prix + frais_notaire + frais_agence
        
        # Rentabilité brute : loyer annuel / prix total * 100
        bien["rentabilite_brute"] = round(loyer_cc * 12 / prix_total * 100, 2) if prix_total else 0
        
        # Cashflow annuel : (loyer - charges) * 12
        bien["cashflow_annuel"] = round((loyer_cc - charges) * 12, 2)
        
        # Rentabilité nette : (loyer - charges) * 12 / prix_total * 100
        bien["rentabilite_nette"] = round((loyer_cc - charges) * 12 / prix_total * 100, 2) if prix_total else 0

    return biens


# ──────────────────────────────────────────────────────────────
# CREATE bien for a SCI
# ──────────────────────────────────────────────────────────────

@router.post("/", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
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

    write_client = _get_client(request)
    result = write_client.table("biens").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create bien")

    created = data[0]
    bien_id = str(created.get("id", ""))
    
    # Compute prix_total and rentabilite on-the-fly for the response
    prix = float(payload.prix_acquisition or 0)
    frais_notaire = float(payload.frais_notaire or 0)
    frais_agence = float(payload.frais_agence_acquisition or 0)
    prix_total = prix + frais_notaire + frais_agence
    loyer_cc = float(payload.loyer_cc or 0)
    charges = float(payload.charges or 0)
    
    created["prix_total"] = round(prix_total, 2) if prix_total > 0 else None
    created["rentabilite_brute"] = round(loyer_cc * 12 / prix_total * 100, 2) if prix_total > 0 else 0.0
    created["rentabilite_nette"] = round((loyer_cc - charges) * 12 / prix_total * 100, 2) if prix_total > 0 else 0.0
    created["cashflow_annuel"] = round((loyer_cc - charges) * 12, 2)
    
    logger.info("bien_created_nested", bien_id=bien_id, sci_id=str(sci_id), prix_total=prix_total)

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

    # Crédits immobiliers
    credits_result = (
        client.table("credits_immobiliers")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_debut", desc=True)
        .execute()
    )
    credits_immobiliers = []
    if not getattr(credits_result, "error", None):
        credits_immobiliers = credits_result.data or []

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
    if not loyer_hc:
        loyer_hc = float(bien.get("loyer_cc", 0) or 0)
    frais_annuel = 0
    for f in frais_agence:
        montant = f.get("montant_ou_pourcentage", 0) or 0
        if f.get("type_frais") == "pourcentage":
            frais_annuel += loyer_hc * (montant / 100) * 12
        else:
            frais_annuel += montant * 12

    loyer_mensuel = bien.get("loyer_cc", 0) or bien.get("loyer", 0) or 0
    charges_mensuelles = bien.get("charges", 0) or 0
    prix_acquisition = bien.get("prix_acquisition")

    # Use mensualite from the first active credit, if any
    mensualite_credit = 0.0
    for credit in credits_immobiliers:
        if credit.get("statut", "en_cours") == "en_cours":
            mensualite_credit = float(credit.get("mensualite", 0) or 0)
            break

    rentabilite = calculate_rentabilite(
        prix_acquisition=prix_acquisition,
        loyer_mensuel=loyer_mensuel,
        charges_mensuelles=charges_mensuelles,
        prime_pno_annuelle=prime_pno,
        frais_agence_annuel=frais_annuel,
        mensualite_credit=mensualite_credit,
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
        zone_tendue=bool(bien.get("zone_tendue", False)),
        bail_actif=bail_actif,
        loyers_recents=loyers_recents,
        charges_list=charges_list,
        assurance_pno=assurance_pno,
        frais_agence=frais_agence,
        credits_immobiliers=credits_immobiliers,
        documents=documents,
        rentabilite=RentabiliteCalculee(**rentabilite),
    )


# ──────────────────────────────────────────────────────────────
# UPDATE bien
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}", response_model=BienResponse)
@limiter.limit("30/minute")
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
@limiter.limit("5/minute")
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
