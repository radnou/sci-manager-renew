"""Nested biens API under /scis/{sci_id}/biens with fiche bien support."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from app.core.supabase_client import get_supabase_service_client
from app.core.exceptions import DatabaseError, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.models.charges import ChargeCreate, ChargeResponse, ChargeUpdate
from app.models.loyers import LoyerCreate, LoyerResponse
from app.schemas.assurance_pno import AssurancePnoCreate, AssurancePnoResponse, AssurancePnoUpdate
from app.schemas.baux import BailCreate, BailResponse, BailUpdate
from app.schemas.documents import DocumentBienResponse
from app.schemas.fiche_bien import FicheBienResponse, RentabiliteCalculee
from app.schemas.frais_agence import FraisAgenceCreate, FraisAgenceResponse
from app.services.rentabilite_service import calculate_rentabilite

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/biens", tags=["scis-biens"])


def _get_client():
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


# ──────────────────────────────────────────────────────────────
# LIST baux for a bien (history)
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/baux", response_model=list[BailResponse])
async def list_bien_baux(
    sci_id: UUID,
    bien_id: str,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste tous les baux d'un bien (historique complet)."""
    client = _get_client()
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
                .select("locataire_id")
                .eq("bail_id", bail_id)
                .execute()
            )
            if not getattr(loc_result, "error", None) and loc_result.data:
                loc_ids = [row["locataire_id"] for row in loc_result.data]
                for loc_id in loc_ids:
                    loc_detail = (
                        client.table("locataires")
                        .select("id, nom, prenom, email, telephone")
                        .eq("id", loc_id)
                        .execute()
                    )
                    if not getattr(loc_detail, "error", None) and loc_detail.data:
                        locataires.append(loc_detail.data[0])
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un bail pour un bien (gérant uniquement). Expire le bail en_cours existant."""
    logger.info("creating_bail", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

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

    result = client.table("baux").insert(row).execute()
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
        join_row = {"bail_id": bail_id, "locataire_id": loc_id}
        client.table("bail_locataires").insert(join_row).execute()
        loc_detail = (
            client.table("locataires")
            .select("id, nom, prenom, email, telephone")
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
    bail_id: int,
    payload: BailUpdate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un bail (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_bail", bail_id=bail_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client()
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
        .select("locataire_id")
        .eq("bail_id", bail_id)
        .execute()
    )
    locataires = []
    if not getattr(loc_result, "error", None) and loc_result.data:
        for row in loc_result.data:
            loc_detail = (
                client.table("locataires")
                .select("id, nom, prenom, email, telephone")
                .eq("id", row["locataire_id"])
                .execute()
            )
            if not getattr(loc_detail, "error", None) and loc_detail.data:
                locataires.append(loc_detail.data[0])

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
    bail_id: int,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un bail (gérant uniquement)."""
    logger.info("deleting_bail", bail_id=bail_id, bien_id=bien_id)

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Delete join table entries first
    client.table("bail_locataires").delete().eq("bail_id", bail_id).execute()

    result = client.table("baux").delete().eq("id", bail_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("bail_deleted", bail_id=bail_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# ATTACH locataire to bail
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/baux/{bail_id}/locataires", status_code=status.HTTP_201_CREATED)
async def attach_locataire_to_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: int,
    body: dict,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Attache un locataire à un bail (colocation)."""
    locataire_id = body.get("locataire_id")
    if not locataire_id:
        raise DatabaseError("locataire_id is required")

    logger.info("attaching_locataire", bail_id=bail_id, locataire_id=locataire_id)

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Verify bail exists for this bien
    bail_result = client.table("baux").select("id").eq("id", bail_id).eq("id_bien", bien_id).execute()
    if not bail_result.data:
        raise ResourceNotFoundError("Bail", str(bail_id))

    join_row = {"bail_id": bail_id, "locataire_id": locataire_id}
    result = client.table("bail_locataires").insert(join_row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("locataire_attached", bail_id=bail_id, locataire_id=locataire_id)
    return {"bail_id": bail_id, "locataire_id": locataire_id}


# ──────────────────────────────────────────────────────────────
# DETACH locataire from bail
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/baux/{bail_id}/locataires/{locataire_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_locataire_from_bail(
    sci_id: UUID,
    bien_id: str,
    bail_id: int,
    locataire_id: int,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Détache un locataire d'un bail."""
    logger.info("detaching_locataire", bail_id=bail_id, locataire_id=locataire_id)

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("bail_locataires")
        .delete()
        .eq("bail_id", bail_id)
        .eq("locataire_id", locataire_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("locataire_detached", bail_id=bail_id, locataire_id=locataire_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# LIST charges for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/charges", response_model=list[ChargeResponse])
async def list_bien_charges(
    sci_id: UUID,
    bien_id: str,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les charges d'un bien."""
    client = _get_client()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée une charge pour un bien (gérant uniquement)."""
    logger.info("creating_charge", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id
    # Note: charges table has no id_sci column — scoping is via id_bien → biens.id_sci

    result = client.table("charges").insert(row).execute()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour une charge (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_charge", charge_id=charge_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime une charge (gérant uniquement)."""
    logger.info("deleting_charge", charge_id=charge_id, bien_id=bien_id)

    client = _get_client()
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
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les assurances PNO d'un bien."""
    client = _get_client()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée une assurance PNO pour un bien (gérant uniquement)."""
    logger.info("creating_assurance_pno", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    result = client.table("assurances_pno").insert(row).execute()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour une assurance PNO (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_assurance_pno", pno_id=pno_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime une assurance PNO (gérant uniquement)."""
    logger.info("deleting_assurance_pno", pno_id=pno_id, bien_id=bien_id)

    client = _get_client()
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
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les frais d'agence d'un bien."""
    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("frais_agence")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_frais", desc=True)
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un frais d'agence pour un bien (gérant uniquement)."""
    logger.info("creating_frais_agence", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    result = client.table("frais_agence").insert(row).execute()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un frais d'agence (gérant uniquement)."""
    logger.info("deleting_frais_agence", frais_id=frais_id, bien_id=bien_id)

    client = _get_client()
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
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les documents d'un bien."""
    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("documents")
        .select("*")
        .eq("id_bien", bien_id)
        .order("created_at", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# UPLOAD document for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/documents", response_model=DocumentBienResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    sci_id: UUID,
    bien_id: str,
    file: UploadFile = File(...),
    nom: str = Form(...),
    categorie: str = Form("autre"),
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Upload un document pour un bien (gérant uniquement)."""
    logger.info("uploading_document", bien_id=bien_id, sci_id=str(sci_id), nom=nom, categorie=categorie)

    client = _get_client()
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

    # Get public URL
    url = client.storage.from_("documents").get_public_url(storage_path)

    # Insert record into documents table
    row = {
        "id_bien": bien_id,
        "nom": nom,
        "categorie": categorie,
        "url": url,
    }
    result = client.table("documents").insert(row).execute()
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
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un document (gérant uniquement)."""
    logger.info("deleting_document", doc_id=doc_id, bien_id=bien_id)

    client = _get_client()
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("documents").delete().eq("id", doc_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("document_deleted", doc_id=doc_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
