"""
Endpoints GDPR pour conformité RGPD (Art. 15, 17, 20)

- Export de données (portabilité - Art. 20)
- Suppression de compte (droit à l'oubli - Art. 17)
- Résumé des données (droit d'accès - Art. 15)
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.audit_log import AuditLogger
from app.core.exceptions import SCIManagerException
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_user_client
from app.services.storage_service import storage_service

router = APIRouter(prefix="/gdpr", tags=["gdpr"])
GDPR_EXPORT_TTL_SECONDS = 60 * 30
logger = structlog.get_logger(__name__)


class DataExportResponse(BaseModel):
    success: bool
    message: str
    export_url: str | None = None
    expires_at: str | None = None


class DataSummaryResponse(BaseModel):
    user_id: str
    email: str
    created_at: str
    data_summary: dict[str, Any]


class AccountDeleteResponse(BaseModel):
    success: bool
    message: str


@router.get("/data-export", response_model=DataExportResponse)
@limiter.limit("3/hour")
async def export_user_data(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> DataExportResponse:
    """
    Export complet des données utilisateur (RGPD Art. 20 - Portabilité)

    Retourne toutes les données personnelles dans un format structuré JSON :
    - Informations de compte
    - SCI associées
    - Biens immobiliers
    - Loyers
    - Associés
    - Charges
    - Données fiscales
    """
    try:
        client = get_supabase_user_client(request)

        # Récupérer toutes les données utilisateur
        export_data = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "data": {},
        }

        # 1. Informations utilisateur (via auth)
        auth_user = client.auth.admin.get_user_by_id(user_id)
        export_data["data"]["user"] = {
            "id": auth_user.user.id,
            "email": auth_user.user.email,
            "created_at": auth_user.user.created_at,
            "email_confirmed_at": auth_user.user.email_confirmed_at
        }

        # 2. Associés (pour obtenir les SCI IDs)
        associes_response = client.table("associes").select("*").eq("user_id", user_id).execute()
        associes_rows = associes_response.data or []
        export_data["data"]["associes"] = associes_rows

        # Obtenir la liste des SCI IDs
        sci_ids = [a["id_sci"] for a in associes_rows if a.get("id_sci")]

        if sci_ids:
            # 3. Biens immobiliers
            biens_response = client.table("biens").select("*").in_("id_sci", sci_ids).execute()
            biens_rows = biens_response.data or []
            export_data["data"]["biens"] = biens_rows

            bien_ids = [b["id"] for b in biens_rows if b.get("id")]

            if bien_ids:
                # 4. Loyers
                loyers_response = client.table("loyers").select("*").in_("id_bien", bien_ids).execute()
                export_data["data"]["loyers"] = loyers_response.data or []

                # 5. Charges
                charges_response = client.table("charges").select("*").in_("id_bien", bien_ids).execute()
                export_data["data"]["charges"] = charges_response.data or []

                # 6. Baux
                baux_response = client.table("baux").select("*").in_("id_bien", bien_ids).execute()
                export_data["data"]["baux"] = baux_response.data or []

                # 7. Locataires
                locataires_response = client.table("locataires").select("*").in_("id_bien", bien_ids).execute()
                export_data["data"]["locataires"] = locataires_response.data or []

                # 8. Documents
                documents_response = client.table("documents_bien").select("*").in_("id_bien", bien_ids).execute()
                export_data["data"]["documents"] = documents_response.data or []

            # 9. Données fiscales
            fiscalite_response = client.table("fiscalite").select("*").in_("id_sci", sci_ids).execute()
            export_data["data"]["fiscalite"] = fiscalite_response.data or []

        # 10. Notifications (user-level)
        notifications_response = client.table("notifications").select("*").eq("user_id", user_id).execute()
        export_data["data"]["notifications"] = notifications_response.data or []

        # 11. Notification preferences (user-level)
        notif_prefs_response = client.table("notification_preferences").select("*").eq("user_id", user_id).execute()
        export_data["data"]["notification_preferences"] = notif_prefs_response.data or []

        export_bytes = json.dumps(export_data, ensure_ascii=False, default=str).encode("utf-8")
        file_name = f"gdpr-export-{uuid4().hex}.json"
        file_path = f"gdpr/{user_id}/{file_name}"
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=GDPR_EXPORT_TTL_SECONDS)

        await storage_service.create_bucket_if_not_exists()
        await storage_service.upload_file(
            file_path=file_path,
            file_content=export_bytes,
            content_type="application/json",
        )
        signed_url = await storage_service.create_signed_url(file_path, GDPR_EXPORT_TTL_SECONDS)

        try:
            client.table("gdpr_exports").insert(
                {
                    "user_id": user_id,
                    "file_path": file_path,
                    "size_bytes": len(export_bytes),
                    "expires_at": expires_at.isoformat(),
                }
            ).execute()
        except Exception:
            # Ne pas bloquer l'export si le tracking metadata échoue.
            pass

        await AuditLogger.log_gdpr_event(
            event="data_export",
            user_id=user_id,
            request=request,
            details={
                "data_size_bytes": len(export_bytes),
                "file_path": file_path,
                "expires_at": expires_at.isoformat(),
            },
        )

        return DataExportResponse(
            success=True,
            message="Export des données réalisé avec succès",
            export_url=signed_url,
            expires_at=expires_at.isoformat(),
        )

    except Exception as e:
        logger.error("gdpr_data_export_failed", user_id=user_id, error=str(e), exc_info=True)
        await AuditLogger.log_gdpr_event(
            event="data_export_failed",
            user_id=user_id,
            request=request,
            details={"error": str(e)},
        )
        raise SCIManagerException(
            "Échec de l'export des données.",
            status_code=500,
            code="gdpr_export_failed",
        )


@router.get("/data-summary", response_model=DataSummaryResponse)
@limiter.limit("10/hour")
async def get_data_summary(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> DataSummaryResponse:
    """
    Résumé des données stockées (RGPD Art. 15 - Droit d'accès)

    Retourne un résumé des données personnelles stockées sans données sensibles.
    """
    try:
        client = get_supabase_user_client(request)

        # Informations utilisateur
        auth_user = client.auth.admin.get_user_by_id(user_id)

        # Compteurs
        associes_count = client.table("associes").select("id", count="exact").eq("user_id", user_id).execute()
        associes_rows = client.table("associes").select("id_sci").eq("user_id", user_id).execute().data or []
        sci_ids = [a["id_sci"] for a in associes_rows if a.get("id_sci")]

        biens_count = 0
        loyers_count = 0
        if sci_ids:
            biens_count = client.table("biens").select("id", count="exact").in_("id_sci", sci_ids).execute().count
            bien_rows = client.table("biens").select("id").in_("id_sci", sci_ids).execute().data or []
            bien_ids = [b["id"] for b in bien_rows if b.get("id")]
            if bien_ids:
                loyers_count = client.table("loyers").select("id", count="exact").in_("id_bien", bien_ids).execute().count

        return DataSummaryResponse(
            user_id=user_id,
            email=str(auth_user.user.email),
            created_at=str(auth_user.user.created_at),
            data_summary={
                "sci_count": len(sci_ids),
                "biens_count": biens_count,
                "loyers_count": loyers_count,
                "associes_count": associes_count.count,
                "account_created": str(auth_user.user.created_at),
                "last_sign_in": str(auth_user.user.last_sign_in_at),
            },
        )

    except Exception as e:
        logger.error("gdpr_data_summary_failed", user_id=user_id, error=str(e), exc_info=True)
        raise SCIManagerException(
            "Échec de la récupération du résumé de données.",
            status_code=500,
            code="gdpr_summary_failed",
        )


@router.delete("/account", response_model=AccountDeleteResponse)
@limiter.limit("2/day")
async def delete_user_account(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> AccountDeleteResponse:
    """
    Suppression définitive du compte (RGPD Art. 17 - Droit à l'oubli)

    ⚠️ ATTENTION: Action irréversible !

    Supprime :
    - Le compte utilisateur
    - Toutes les données SCI
    - Tous les biens
    - Tous les loyers
    - Toutes les charges
    - Toutes les données fiscales

    EXCEPTION: Les données de facturation sont ANONYMISÉES (pas supprimées)
    pour respecter l'obligation légale de conservation de 10 ans.
    """
    try:
        client = get_supabase_user_client(request)

        # Log AVANT suppression (important pour audit)
        await AuditLogger.log_gdpr_event(
            event="account_delete_requested",
            user_id=user_id,
            request=request,
            details={"ip": request.client.host if request.client else None},
        )

        # 1. Récupérer les IDs avant suppression
        associes_response = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
        associes_rows = associes_response.data or []
        sci_ids = [a["id_sci"] for a in associes_rows if a.get("id_sci")]

        bien_ids = []
        if sci_ids:
            biens_response = client.table("biens").select("id").in_("id_sci", sci_ids).execute()
            bien_rows = biens_response.data or []
            bien_ids = [b["id"] for b in bien_rows if b.get("id")]

        # 2. Suppression en cascade (dans l'ordre inverse des dépendances)

        # User-level tables first (no FK dependency on biens/sci)
        client.table("notifications").delete().eq("user_id", user_id).execute()
        client.table("notification_preferences").delete().eq("user_id", user_id).execute()

        if bien_ids:
            # Clean up storage files for documents before deleting records
            try:
                docs_response = client.table("documents_bien").select("id,url").in_("id_bien", bien_ids).execute()
                doc_rows = docs_response.data or []
                for doc in doc_rows:
                    doc_url = doc.get("url")
                    if doc_url:
                        # Extract storage path from URL (format: .../object/public/documents/<path>)
                        try:
                            path_marker = "/object/public/documents/"
                            if path_marker in str(doc_url):
                                storage_path = str(doc_url).split(path_marker, 1)[1]
                                client.storage.from_("documents").remove([storage_path])
                        except Exception:
                            pass  # Best-effort storage cleanup
            except Exception:
                pass  # Don't block deletion if document cleanup fails

            # Documents
            client.table("documents_bien").delete().in_("id_bien", bien_ids).execute()
            # Locataires
            client.table("locataires").delete().in_("id_bien", bien_ids).execute()
            # Baux
            client.table("baux").delete().in_("id_bien", bien_ids).execute()
            # Loyers
            client.table("loyers").delete().in_("id_bien", bien_ids).execute()
            # Charges
            client.table("charges").delete().in_("id_bien", bien_ids).execute()

        if sci_ids:
            # Biens
            client.table("biens").delete().in_("id_sci", sci_ids).execute()
            # Données fiscales
            client.table("fiscalite").delete().in_("id_sci", sci_ids).execute()

        # Associés
        client.table("associes").delete().eq("user_id", user_id).execute()

        # 3. ANONYMISER (pas supprimer) les données de facturation Stripe
        # Les données de facturation doivent être conservées 10 ans (Code Général des Impôts)
        try:
            client.table("subscriptions").update(
                {
                    "status": "deleted",
                    "stripe_customer_id": None,
                }
            ).eq("user_id", user_id).execute()
        except Exception:
            # Reste best-effort pour ne pas bloquer la suppression RGPD.
            pass

        try:
            exports_response = client.table("gdpr_exports").select("file_path").eq("user_id", user_id).execute()
            export_rows = exports_response.data or []
            for row in export_rows:
                file_path = row.get("file_path")
                if file_path:
                    await storage_service.delete_file(str(file_path))
            client.table("gdpr_exports").delete().eq("user_id", user_id).execute()
        except Exception:
            # Ne pas bloquer si nettoyage des exports échoue.
            pass

        # 4. Supprimer le compte auth (dernière étape)
        client.auth.admin.delete_user(user_id)

        # Log final (avec user_id avant qu'il soit supprimé)
        await AuditLogger.log_gdpr_event(
            event="account_deleted",
            user_id=user_id,
            request=request,
            details={"deleted_sci_count": len(sci_ids), "deleted_biens_count": len(bien_ids)},
        )

        return AccountDeleteResponse(
            success=True,
            message="Compte supprimé définitivement. Vos données de facturation ont été anonymisées conformément à la loi.",
        )

    except Exception as e:
        logger.error("gdpr_account_delete_failed", user_id=user_id, error=str(e), exc_info=True)
        await AuditLogger.log_gdpr_event(
            event="account_delete_failed",
            user_id=user_id,
            request=request,
            details={"error": str(e)},
        )
        raise SCIManagerException(
            "Échec de la suppression du compte.",
            status_code=500,
            code="gdpr_account_delete_failed",
        )
