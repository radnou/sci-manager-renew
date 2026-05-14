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

from .biens_core import _refresh_documents_urls, _validate_upload

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


@router.get("/{bien_id}/documents", response_model=list[DocumentBienResponse])
async def list_bien_documents(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """Liste les documents d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    start = (page - 1) * page_size
    end = start + page_size - 1
    result = (
        client.table("documents_bien")
        .select("*")
        .eq("id_bien", bien_id)
        .order("uploaded_at", desc=True)
        .range(start, end)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return _refresh_documents_urls(client, result.data or [])


# ──────────────────────────────────────────────────────────────
# UPLOAD document for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/documents", response_model=DocumentBienResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
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
@limiter.limit("5/minute")
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
