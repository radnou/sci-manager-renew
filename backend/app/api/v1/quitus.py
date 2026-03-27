from __future__ import annotations

import re
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.config import settings
from app.core.exceptions import ExternalServiceError, FeatureDisabledError, SCIManagerException, ValidationError
from app.core.external_services import run_with_retry
from app.core.supabase_client import get_supabase_service_client, get_supabase_user_client
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.models.quitus import PublicQuitusRequest, QuitusRequest, QuitusResponse
from app.services.quitus_service import QuitusService, get_next_quittance_number
from app.services.storage_service import storage_service
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/quitus", tags=["quitus"])

_LEGACY_QUITUS_FILENAME_RE = re.compile(r"^quitus-(?P<token>[a-f0-9]{32})\.pdf$", re.IGNORECASE)
_SCOPED_QUITUS_FILENAME_RE = re.compile(
    r"^quitus-(?P<sci_id>.+)-(?P<token>[a-f0-9]{32})\.pdf$",
    re.IGNORECASE,
)


def _validate_filename(filename: str) -> str:
    if (
        not filename
        or "/" in filename
        or "\\" in filename
        or filename.startswith(".")
        or ".." in filename
    ):
        raise ValidationError("Nom de fichier invalide.")
    return filename


def _build_inline_filename(periode: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", periode.lower()).strip("-")
    return f"quittance-{slug or 'periode'}.pdf"


def _verify_bien_ownership(request: Request, user_id: str, id_bien: str) -> str:
    client = get_supabase_user_client(request)
    sci_check = client.table("biens").select("id_sci").eq("id", id_bien).execute()
    if not sci_check.data:
        raise HTTPException(status_code=404, detail="Bien non trouvé")
    sci_id = sci_check.data[0]["id_sci"]
    member_check = client.table("associes").select("id").eq("id_sci", sci_id).eq("user_id", user_id).execute()
    if not member_check.data:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce bien")
    return str(sci_id)


def _verify_loyer_belongs_to_bien(request: Request, id_loyer: str, id_bien: str) -> None:
    client = get_supabase_user_client(request)
    loyer_check = client.table("loyers").select("id_bien").eq("id", id_loyer).execute()
    if not loyer_check.data:
        raise HTTPException(status_code=404, detail="Loyer non trouvé")
    if str(loyer_check.data[0]["id_bien"]) != id_bien:
        raise HTTPException(status_code=403, detail="Le loyer n'appartient pas à ce bien")


def _build_quitus_filename(sci_id: str) -> str:
    return f"quitus-{sci_id}-{uuid4().hex}.pdf"


def _extract_quitus_sci_id(filename: str) -> str | None:
    if _LEGACY_QUITUS_FILENAME_RE.fullmatch(filename):
        return None

    match = _SCOPED_QUITUS_FILENAME_RE.fullmatch(filename)
    if not match:
        raise ValidationError("Nom de fichier invalide.")
    return match.group("sci_id")


def _verify_quitus_download_access(request: Request, user_id: str, sci_id: str) -> None:
    client = get_supabase_user_client(request)
    member_check = client.table("associes").select("id").eq("id_sci", sci_id).eq("user_id", user_id).execute()
    if not member_check.data:
        raise HTTPException(status_code=403, detail="Accès non autorisé à cette quittance")


def _fetch_enrichment_data(request: Request, sci_id: str, id_bien: str, id_loyer: str) -> dict:
    """Fetch SCI, bail, and locataire data from DB for PDF enrichment.

    Returns dict with keys: sci_data, bail_data, locataires, loyer_data, quittance_numero.
    Gracefully degrades — missing data results in None values, never raises.
    """
    client = get_supabase_user_client(request)
    result: dict = {
        "sci_data": None,
        "bail_data": None,
        "locataires": None,
        "loyer_data": None,
        "quittance_numero": None,
    }

    # 1. SCI data
    try:
        sci_result = client.table("sci").select("*").eq("id", sci_id).execute()
        if sci_result.data:
            result["sci_data"] = sci_result.data[0]
    except Exception:
        pass

    # 2. Loyer data (for date_paiement, mode_paiement)
    try:
        loyer_result = client.table("loyers").select("*").eq("id", id_loyer).execute()
        if loyer_result.data:
            result["loyer_data"] = loyer_result.data[0]
    except Exception:
        pass

    # 3. Active bail for this bien
    try:
        baux_result = client.table("baux").select("*").eq("id_bien", id_bien).execute()
        baux_rows = baux_result.data or []
        # Pick active bail (statut=en_cours) or the most recent one
        active_bail = None
        for bail in baux_rows:
            if str(bail.get("statut", "")).lower() == "en_cours":
                active_bail = bail
                break
        if not active_bail and baux_rows:
            active_bail = baux_rows[-1]

        if active_bail:
            result["bail_data"] = active_bail

            # 4. Locataires via bail_locataires junction table
            bail_id = str(active_bail.get("id", ""))
            if bail_id:
                try:
                    bl_result = client.table("bail_locataires").select("id_locataire").eq("id_bail", bail_id).execute()
                    loc_ids = [str(row.get("id_locataire")) for row in (bl_result.data or []) if row.get("id_locataire")]
                    if loc_ids:
                        locs = []
                        for lid in loc_ids:
                            loc_result = client.table("locataires").select("*").eq("id", lid).execute()
                            if loc_result.data:
                                locs.append(loc_result.data[0])
                        if locs:
                            result["locataires"] = locs
                except Exception:
                    pass
    except Exception:
        pass

    # 5. Sequential quittance number
    try:
        loyer_data = result.get("loyer_data") or {}
        loyer_date_str = loyer_data.get("date_loyer")
        if loyer_date_str:
            if isinstance(loyer_date_str, str):
                loyer_date = date.fromisoformat(loyer_date_str)
            else:
                loyer_date = loyer_date_str
        else:
            loyer_date = date.today()

        result["quittance_numero"] = get_next_quittance_number(client, sci_id, loyer_date)
    except Exception:
        pass

    return result


@router.post("/public-generate")
@limiter.limit("5/minute")
async def public_generate_quitus(request: Request, payload: PublicQuitusRequest):
    """Generate a simple quittance PDF without authentication.

    Public lead magnet tool — stateless, no DB, no storage.
    Rate limited to 5/minute per IP.
    """
    import re

    pdf_bytes = QuitusService.generate_public_quitus_pdf(payload)
    slug = re.sub(r"[^a-z0-9]+", "-", payload.periode.lower()).strip("-")
    filename = f"quittance-{slug or 'periode'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/generate", response_model=QuitusResponse)
@limiter.limit("15/minute")
async def generate_quitus(
    request: Request, payload: QuitusRequest, user_id: str = Depends(get_current_user)
):
    SubscriptionService.ensure_feature_enabled(user_id, "quitus_enabled")
    sci_id = _verify_bien_ownership(request, user_id, payload.id_bien)
    _verify_loyer_belongs_to_bien(request, payload.id_loyer, payload.id_bien)

    enrichment = _fetch_enrichment_data(request, sci_id, payload.id_bien, payload.id_loyer)

    pdf_bytes = QuitusService.generate_quitus_pdf(
        payload,
        sci_data=enrichment["sci_data"],
        bail_data=enrichment["bail_data"],
        locataires=enrichment["locataires"],
        quittance_numero=enrichment["quittance_numero"],
    )
    filename = _build_quitus_filename(sci_id)
    storage_path = f"quitus/{sci_id}/{filename}"

    await storage_service.create_bucket_if_not_exists()
    await storage_service.upload_file(
        file_path=storage_path,
        file_content=pdf_bytes,
        content_type="application/pdf",
    )

    return {
        "filename": filename,
        "pdf_url": f"/api/v1/quitus/files/{filename}",
        "size_bytes": len(pdf_bytes),
    }


@router.post("/render")
@limiter.limit("20/minute")
async def render_quitus(request: Request, payload: QuitusRequest, user_id: str = Depends(get_current_user)):
    SubscriptionService.ensure_feature_enabled(user_id, "quitus_enabled")
    sci_id = _verify_bien_ownership(request, user_id, payload.id_bien)
    _verify_loyer_belongs_to_bien(request, payload.id_loyer, payload.id_bien)
    if not settings.feature_pdf_render_direct:
        raise FeatureDisabledError(
            "La prévisualisation PDF directe est désactivée.",
            flag_name="feature_pdf_render_direct",
        )

    enrichment = _fetch_enrichment_data(request, sci_id, payload.id_bien, payload.id_loyer)

    pdf_bytes = QuitusService.generate_quitus_pdf(
        payload,
        sci_data=enrichment["sci_data"],
        bail_data=enrichment["bail_data"],
        locataires=enrichment["locataires"],
        quittance_numero=enrichment["quittance_numero"],
    )
    filename = _build_inline_filename(payload.periode)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/files/{filename}")
@limiter.limit("30/minute")
async def download_quitus(request: Request, filename: str, user_id: str = Depends(get_current_user)):
    SubscriptionService.ensure_feature_enabled(user_id, "quitus_enabled")
    safe_filename = _validate_filename(filename)
    sci_id = _extract_quitus_sci_id(safe_filename)
    if sci_id is not None:
        _verify_quitus_download_access(request, user_id, sci_id)
        storage_path = f"quitus/{sci_id}/{safe_filename}"
    else:
        storage_path = f"quitus/{user_id}/{safe_filename}"

    try:
        pdf_bytes = await storage_service.download_file(storage_path)
    except Exception as exc:
        # Supabase client errors for missing files are mapped to 404 for UX.
        if "not found" in str(exc).lower():
            raise SCIManagerException(
                "Quittance introuvable.",
                status_code=404,
                code="resource_not_found",
            ) from exc
        raise ExternalServiceError("Storage", "Failed to download quitus file") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_filename}"'},
    )


@router.post("/send-email/{filename}", status_code=200)
@limiter.limit("10/minute")
async def send_quittance_email(
    request: Request,
    filename: str,
    bien_id: str,
    user_id: str = Depends(get_current_user),
):
    """Send a generated quittance PDF to the tenant by email."""
    import base64

    import resend
    import structlog

    logger = structlog.get_logger()

    # Validate filename and verify ownership
    safe_filename = _validate_filename(filename)
    sci_id = _verify_bien_ownership(request, user_id, bien_id)

    # Also verify filename belongs to this SCI
    file_sci_id = _extract_quitus_sci_id(safe_filename)
    if file_sci_id is not None and str(file_sci_id) != str(sci_id):
        raise SCIManagerException(
            "Cette quittance n'appartient pas à cette SCI.",
            status_code=403,
            code="access_denied",
        )

    SubscriptionService.ensure_feature_enabled(user_id, "quitus_enabled")

    # Download PDF from storage
    storage_path = f"quitus/{sci_id}/{safe_filename}"
    try:
        pdf_bytes = await storage_service.download_file(storage_path)
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise SCIManagerException(
                "Quittance introuvable dans le stockage.",
                status_code=404,
                code="resource_not_found",
            ) from exc
        raise ExternalServiceError("Storage", "Failed to download quitus file") from exc

    # Find active bail for this bien
    client = get_supabase_user_client(request)
    baux_resp = (
        client.table("baux")
        .select("id")
        .eq("id_bien", bien_id)
        .eq("statut", "en_cours")
        .limit(1)
        .execute()
    )
    if not baux_resp.data:
        raise SCIManagerException(
            "Aucun bail actif trouvé pour ce bien.",
            status_code=404,
            code="resource_not_found",
        )

    bail_id = str(baux_resp.data[0]["id"])

    # Get locataires via bail_locataires junction table
    loc_resp = (
        client.table("bail_locataires")
        .select("locataires(id, nom, email)")
        .eq("id_bail", bail_id)
        .execute()
    )

    tenant_email = None
    tenant_name = None
    for entry in loc_resp.data or []:
        loc = entry.get("locataires")
        if loc and loc.get("email"):
            tenant_email = loc["email"]
            tenant_name = loc.get("nom", "Locataire")
            break

    if not tenant_email:
        raise ValidationError(
            "Aucun email renseigné pour le locataire. "
            "Ajoutez l'email dans l'onglet Bail."
        )

    # Send email via Resend with PDF attachment
    resend.api_key = settings.resend_api_key
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    payload = {
        "from": settings.resend_from_email,
        "to": tenant_email,
        "subject": f"Votre quittance de loyer — {safe_filename.replace('.pdf', '')}",
        "html": (
            f"<p>Bonjour {tenant_name},</p>"
            f"<p>Veuillez trouver ci-joint votre quittance de loyer.</p>"
            f"<p>Cordialement,<br>Votre gestionnaire SCI</p>"
        ),
        "attachments": [{"filename": safe_filename, "content": pdf_b64}],
    }

    try:
        await run_with_retry(
            operation="resend.send_quittance_to_tenant",
            func=lambda: resend.Emails.send(payload),
            context={"filename": safe_filename, "to": tenant_email},
        )
    except Exception as e:
        logger.warning("quittance_email_failed", filename=safe_filename, error=str(e))
        raise ExternalServiceError("Resend", f"Quittance email send failed: {str(e)}")

    logger.info("quittance_email_sent", filename=safe_filename, to=tenant_email)
    return {"message": f"Quittance envoyée à {tenant_email}"}
