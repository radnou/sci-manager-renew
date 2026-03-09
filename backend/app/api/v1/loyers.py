from __future__ import annotations

from collections import defaultdict
from datetime import date

import structlog
from fastapi import APIRouter, Depends, Response, status
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    SCIManagerException,
    ValidationError,
)
from app.core.security import get_current_user
from app.models.loyers import LoyerCreate, LoyerResponse, LoyerUpdate

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/loyers", tags=["loyers"])


def _get_client():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    result = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return [str(row.get("id_sci")) for row in (result.data or []) if row.get("id_sci")]


def _require_sci_access(user_sci_ids: list[str], id_sci: str) -> None:
    if not id_sci:
        raise DatabaseError("Missing id_sci on scoped resource")
    if id_sci not in user_sci_ids:
        raise AuthorizationError("SCI", id_sci)


def _select_by_sci_scope(client, sci_ids: list[str], date_from: date | None, date_to: date | None):
    if not sci_ids:
        return []

    query = client.table("loyers").select("*")
    if hasattr(query, "in_"):
        query = query.in_("id_sci", sci_ids)
        if date_from:
            query = query.gte("date_loyer", date_from.isoformat())
        if date_to:
            query = query.lte("date_loyer", date_to.isoformat())
        result = query.execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        return result.data or []

    # Test fallback for fake query clients that do not expose `in_`.
    rows: list[dict] = []
    for sci_id in sci_ids:
        scoped_query = client.table("loyers").select("*").eq("id_sci", sci_id)
        if date_from:
            scoped_query = scoped_query.gte("date_loyer", date_from.isoformat())
        if date_to:
            scoped_query = scoped_query.lte("date_loyer", date_to.isoformat())
        result = scoped_query.execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        rows.extend(result.data or [])
    return rows


def _fetch_bien(client, bien_id: str) -> dict:
    result = client.table("biens").select("id,id_sci").eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    rows = result.data or []
    if not rows:
        raise ValidationError(f"Unknown bien id: {bien_id}")

    return rows[0]


def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise ValidationError("date_from must be earlier than or equal to date_to")


def _resolve_loyer_sci_id(client, loyer_row: dict) -> str:
    existing_id_sci = loyer_row.get("id_sci")
    if existing_id_sci:
        return str(existing_id_sci)

    bien_id = loyer_row.get("id_bien")
    if not bien_id:
        raise DatabaseError("Loyer row missing id_bien")

    bien = _fetch_bien(client, str(bien_id))
    resolved_id_sci = bien.get("id_sci")
    if not resolved_id_sci:
        raise DatabaseError(f"Bien {bien_id} missing id_sci")

    return str(resolved_id_sci)


@router.get("", response_model=list[LoyerResponse])
@router.get("/", response_model=list[LoyerResponse])
async def list_loyers(
    id_sci: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info(
        "listing_loyers",
        user_id=user_id,
        id_sci=id_sci,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
    )

    try:
        _validate_date_range(date_from, date_to)
        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)

        if id_sci:
            _require_sci_access(user_sci_ids, id_sci)
            query = client.table("loyers").select("*").eq("id_sci", id_sci)
            if date_from:
                query = query.gte("date_loyer", date_from.isoformat())
            if date_to:
                query = query.lte("date_loyer", date_to.isoformat())
            result = query.execute()
            if getattr(result, "error", None):
                raise DatabaseError(str(result.error))
            return result.data or []

        return _select_by_sci_scope(client, user_sci_ids, date_from, date_to)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("list_loyers_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list loyers")


@router.post("", response_model=LoyerResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=LoyerResponse, status_code=status.HTTP_201_CREATED)
async def create_loyer(
    payload: LoyerCreate,
    id_sci: str | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info("creating_loyer", user_id=user_id, bien_id=payload.id_bien, montant=payload.montant)
    try:
        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        bien = _fetch_bien(client, payload.id_bien)
        bien_sci_id = str(bien.get("id_sci") or "")

        target_sci_id = id_sci or bien_sci_id
        if not target_sci_id:
            raise ValidationError("Unable to resolve SCI from bien")

        if id_sci and id_sci != bien_sci_id:
            raise ValidationError("id_sci does not match bien ownership")

        _require_sci_access(user_sci_ids, target_sci_id)

        row = payload.model_dump(mode="json")
        row["id_sci"] = target_sci_id

        result = client.table("loyers").insert(row).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        data = result.data or []
        if not data:
            raise DatabaseError("Unable to create loyer")

        created = data[0]
        logger.info("loyer_created", loyer_id=created.get("id"))
        return created
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("create_loyer_failed", user_id=user_id, bien_id=payload.id_bien, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create loyer")


@router.patch("/{loyer_id}", response_model=LoyerResponse)
async def update_loyer(loyer_id: str, payload: LoyerUpdate, user_id: str = Depends(get_current_user)):
    update_payload = payload.model_dump(exclude_unset=True, mode="json")

    logger.info("updating_loyer", loyer_id=loyer_id, user_id=user_id, fields=list(update_payload.keys()))

    try:
        if not update_payload:
            raise ValidationError("No update fields provided")

        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing_result = client.table("loyers").select("*").eq("id", loyer_id).execute()
        if getattr(existing_result, "error", None):
            raise DatabaseError(str(existing_result.error))

        existing_rows = existing_result.data or []
        if not existing_rows:
            raise ResourceNotFoundError("Loyer", loyer_id)

        existing_sci_id = _resolve_loyer_sci_id(client, existing_rows[0])
        _require_sci_access(user_sci_ids, existing_sci_id)

        result = client.table("loyers").update(update_payload).eq("id", loyer_id).execute()

        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        data = result.data or []
        if not data:
            raise ResourceNotFoundError("Loyer", loyer_id)

        logger.info("loyer_updated", loyer_id=loyer_id)
        return data[0]
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("update_loyer_failed", user_id=user_id, loyer_id=loyer_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update loyer")


@router.delete("/{loyer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loyer(loyer_id: str, user_id: str = Depends(get_current_user)):
    logger.info("deleting_loyer", loyer_id=loyer_id, user_id=user_id)
    try:
        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing_result = client.table("loyers").select("*").eq("id", loyer_id).execute()
        if getattr(existing_result, "error", None):
            raise DatabaseError(str(existing_result.error))

        existing_rows = existing_result.data or []
        if not existing_rows:
            raise ResourceNotFoundError("Loyer", loyer_id)

        existing_sci_id = _resolve_loyer_sci_id(client, existing_rows[0])
        _require_sci_access(user_sci_ids, existing_sci_id)

        result = client.table("loyers").delete().eq("id", loyer_id).execute()

        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        logger.info("loyer_deleted", loyer_id=loyer_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("delete_loyer_failed", user_id=user_id, loyer_id=loyer_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete loyer")


@router.get("/stats")
async def loyer_stats(
    months: int = 12,
    user: dict = Depends(get_current_user),
):
    """Return monthly aggregated loyer stats for the current user."""
    client = _get_client()
    user_id = user["sub"]
    user_sci_ids = _get_user_sci_ids(client, user_id)

    if not user_sci_ids:
        return {"months": []}

    result = (
        client.table("loyers")
        .select("date_loyer, montant, statut")
        .in_("id_sci", user_sci_ids)
        .order("date_loyer", desc=True)
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    monthly: dict[str, dict] = defaultdict(lambda: {"total": 0, "paid": 0, "late": 0, "pending": 0})

    for row in result.data or []:
        date_str = row.get("date_loyer", "")
        if not date_str:
            continue
        month_key = date_str[:7]  # YYYY-MM
        amount = row.get("montant", 0) or 0
        status_val = row.get("statut", "en_attente")

        monthly[month_key]["total"] += amount
        if status_val == "paye":
            monthly[month_key]["paid"] += amount
        elif status_val == "en_retard":
            monthly[month_key]["late"] += amount
        else:
            monthly[month_key]["pending"] += amount

    sorted_months = sorted(monthly.keys(), reverse=True)[:months]

    return {
        "months": [
            {
                "month": m,
                "total": monthly[m]["total"],
                "paid": monthly[m]["paid"],
                "late": monthly[m]["late"],
                "pending": monthly[m]["pending"],
                "collection_rate": round(monthly[m]["paid"] / monthly[m]["total"] * 100, 1)
                if monthly[m]["total"] > 0
                else 0,
            }
            for m in sorted(sorted_months)
        ]
    }
