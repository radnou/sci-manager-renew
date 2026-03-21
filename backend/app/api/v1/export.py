from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from app.core.supabase_client import get_supabase_user_client
from app.core.exceptions import DatabaseError
from app.core.security import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    result = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return [str(row.get("id_sci")) for row in (result.data or []) if row.get("id_sci")]


def _period_to_date(period: Optional[str]) -> Optional[str]:
    """Convert a period string like '6m', '12m', '24m' to an ISO date cutoff."""
    if not period:
        return None
    months_map = {"6m": 6, "12m": 12, "24m": 24}
    months = months_map.get(period)
    if months is None:
        return None
    cutoff = datetime.now() - timedelta(days=months * 30)
    return cutoff.strftime("%Y-%m-%d")


@router.get("/loyers/csv")
async def export_loyers_csv(
    request: Request,
    user_id: str = Depends(get_current_user),
    period: Optional[str] = Query(None, description="Period filter: 6m, 12m, 24m"),
    sci_id: Optional[str] = Query(None, description="Filter by SCI ID"),
):
    """Export loyers as CSV for the current user, optionally filtered by period and SCI."""
    client = get_supabase_user_client(request)
    user_sci_ids = _get_user_sci_ids(client, user_id)

    # If sci_id provided, validate it belongs to user and narrow the filter
    if sci_id:
        if sci_id not in user_sci_ids:
            user_sci_ids = []
        else:
            user_sci_ids = [sci_id]

    if not user_sci_ids:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date_loyer", "montant", "statut", "bien", "sci"])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=loyers_export.csv"},
        )

    query = (
        client.table("loyers")
        .select("date_loyer, montant, statut, id_bien, id_sci, biens(adresse), sci(nom)")
        .in_("id_sci", user_sci_ids)
        .order("date_loyer", desc=True)
    )

    cutoff = _period_to_date(period)
    if cutoff:
        query = query.gte("date_loyer", cutoff)

    result = query.execute()

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date_loyer", "montant", "statut", "bien", "sci"])

    for row in result.data or []:
        bien_name = (row.get("biens") or {}).get("adresse", "") or row.get("id_bien", "")
        sci_name = (row.get("sci") or {}).get("nom", "") or row.get("id_sci", "")
        writer.writerow([
            row.get("date_loyer", ""),
            row.get("montant", ""),
            row.get("statut", ""),
            bien_name,
            sci_name,
        ])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=loyers_{timestamp}.csv"},
    )


@router.get("/biens/csv")
async def export_biens_csv(
    request: Request,
    user_id: str = Depends(get_current_user),
    sci_id: Optional[str] = Query(None, description="Filter by SCI ID"),
):
    """Export biens as CSV for the current user, optionally filtered by SCI."""
    client = get_supabase_user_client(request)
    user_sci_ids = _get_user_sci_ids(client, user_id)

    # If sci_id provided, validate it belongs to user and narrow the filter
    if sci_id:
        if sci_id not in user_sci_ids:
            user_sci_ids = []
        else:
            user_sci_ids = [sci_id]

    db_columns = ["adresse", "ville", "code_postal", "type_locatif", "loyer_cc", "charges", "surface_m2", "nb_pieces", "dpe_classe", "id_sci"]
    csv_headers = ["adresse", "ville", "code_postal", "type_locatif", "loyer_cc", "charges", "surface_m2", "nb_pieces", "dpe_classe", "sci"]

    if not user_sci_ids:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(csv_headers)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=biens_export.csv"},
        )

    select_fields = "adresse, ville, code_postal, type_locatif, loyer_cc, charges, surface_m2, nb_pieces, dpe_classe, id_sci, sci(nom)"
    result = (
        client.table("biens")
        .select(select_fields)
        .in_("id_sci", user_sci_ids)
        .order("adresse")
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(csv_headers)

    for row in result.data or []:
        sci_name = (row.get("sci") or {}).get("nom", "") or row.get("id_sci", "")
        values = [row.get(col, "") for col in db_columns[:-1]]  # all except id_sci
        values.append(sci_name)
        writer.writerow(values)

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=biens_{timestamp}.csv"},
    )
