from __future__ import annotations

import csv
import io
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.core.security import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


def _get_client():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    result = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return [str(row.get("id_sci")) for row in (result.data or []) if row.get("id_sci")]


@router.get("/loyers/csv")
async def export_loyers_csv(user: dict = Depends(get_current_user)):
    """Export all loyers as CSV for the current user."""
    client = _get_client()
    user_id = user["sub"]
    user_sci_ids = _get_user_sci_ids(client, user_id)

    if not user_sci_ids:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date_loyer", "montant", "statut", "id_bien", "id_sci"])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=loyers_export.csv"},
        )

    result = (
        client.table("loyers")
        .select("date_loyer, montant, statut, id_bien, id_sci")
        .in_("id_sci", user_sci_ids)
        .order("date_loyer", desc=True)
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date_loyer", "montant", "statut", "id_bien", "id_sci"])

    for row in result.data or []:
        writer.writerow([
            row.get("date_loyer", ""),
            row.get("montant", ""),
            row.get("statut", ""),
            row.get("id_bien", ""),
            row.get("id_sci", ""),
        ])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=loyers_{timestamp}.csv"},
    )


@router.get("/biens/csv")
async def export_biens_csv(user: dict = Depends(get_current_user)):
    """Export all biens as CSV for the current user."""
    client = _get_client()
    user_id = user["sub"]
    user_sci_ids = _get_user_sci_ids(client, user_id)

    if not user_sci_ids:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["nom", "adresse", "type_bien", "loyer_mensuel", "charges", "id_sci"])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=biens_export.csv"},
        )

    result = (
        client.table("biens")
        .select("nom, adresse, type_bien, loyer_mensuel, charges, id_sci")
        .in_("id_sci", user_sci_ids)
        .order("nom")
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["nom", "adresse", "type_bien", "loyer_mensuel", "charges", "id_sci"])

    for row in result.data or []:
        writer.writerow([
            row.get("nom", ""),
            row.get("adresse", ""),
            row.get("type_bien", ""),
            row.get("loyer_mensuel", ""),
            row.get("charges", ""),
            row.get("id_sci", ""),
        ])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=biens_{timestamp}.csv"},
    )
