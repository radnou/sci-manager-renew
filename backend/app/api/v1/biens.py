from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Response, status
from app.core.supabase_client import get_supabase_service_client
from app.core.exceptions import AuthorizationError, DatabaseError, ResourceNotFoundError
from app.core.security import get_current_user
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.services.sci_service import SCIService
from app.services.subscription_service import SubscriptionService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/biens", tags=["biens"])


def _get_client():
    return get_supabase_service_client()


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    result = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return [str(row.get("id_sci")) for row in (result.data or []) if row.get("id_sci")]


def _select_by_sci_scope(client, table_name: str, sci_ids: list[str]):
    if not sci_ids:
        return []

    query = client.table(table_name).select("*")
    if hasattr(query, "in_"):
        result = query.in_("id_sci", sci_ids).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        return result.data or []

    # Test fallback for fake query clients that do not expose `in_`.
    rows: list[dict] = []
    for sci_id in sci_ids:
        result = client.table(table_name).select("*").eq("id_sci", sci_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        rows.extend(result.data or [])
    return rows


def _require_sci_access(user_sci_ids: list[str], id_sci: str) -> None:
    if not id_sci:
        raise DatabaseError("Missing id_sci on scoped resource")
    if id_sci not in user_sci_ids:
        raise AuthorizationError("SCI", id_sci)


@router.get("", response_model=list[BienResponse])
@router.get("/", response_model=list[BienResponse])
async def list_biens(id_sci: str | None = None, user_id: str = Depends(get_current_user)):
    client = _get_client()
    user_sci_ids = _get_user_sci_ids(client, user_id)

    if id_sci:
        _require_sci_access(user_sci_ids, id_sci)
        result = client.table("biens").select("*").eq("id_sci", id_sci).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        return result.data or []

    return _select_by_sci_scope(client, "biens", user_sci_ids)


@router.post("", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
async def create_bien(payload: BienCreate, user_id: str = Depends(get_current_user)):
    logger.info("creating_bien", user_id=user_id, adresse=payload.adresse)

    summary = SubscriptionService.enforce_limit(user_id, "biens")
    client = _get_client()
    user_sci_ids = _get_user_sci_ids(client, user_id)
    _require_sci_access(user_sci_ids, payload.id_sci)

    row = payload.model_dump(mode="json")
    # Calculate rentabilite for response only (not DB columns)
    rentabilite = SCIService.calculate_rentabilite(row)

    result = client.table("biens").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create bien")

    created = data[0]
    created.update(rentabilite)
    logger.info("bien_created", bien_id=created.get("id"), plan_key=summary.get("plan_key"))
    return created


@router.patch("/{bien_id}", response_model=BienResponse)
async def update_bien(bien_id: str, payload: BienUpdate, user_id: str = Depends(get_current_user)):
    update_payload = payload.model_dump(exclude_unset=True, mode="json")

    logger.info("updating_bien", bien_id=bien_id, user_id=user_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client()
    user_sci_ids = _get_user_sci_ids(client, user_id)
    existing_result = client.table("biens").select("*").eq("id", bien_id).execute()
    if getattr(existing_result, "error", None):
        raise DatabaseError(str(existing_result.error))

    existing_rows = existing_result.data or []
    if not existing_rows:
        raise ResourceNotFoundError("Bien", bien_id)

    existing = existing_rows[0]
    existing_sci_id = str(existing.get("id_sci") or "")
    _require_sci_access(user_sci_ids, existing_sci_id)

    # Calculate rentabilite for response only (not DB columns)
    rentabilite = {}
    if any(key in update_payload for key in ("loyer_cc", "charges", "prix_acquisition")):
        merged = {**existing, **update_payload}
        rentabilite = SCIService.calculate_rentabilite(merged)

    result = client.table("biens").update(update_payload).eq("id", bien_id).execute()

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Bien", bien_id)

    updated = data[0]
    if rentabilite:
        updated.update(rentabilite)
    logger.info("bien_updated", bien_id=bien_id)
    return updated


@router.delete("/{bien_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien(bien_id: str, user_id: str = Depends(get_current_user)):
    logger.info("deleting_bien", bien_id=bien_id, user_id=user_id)

    client = _get_client()
    user_sci_ids = _get_user_sci_ids(client, user_id)
    existing_result = client.table("biens").select("id,id_sci").eq("id", bien_id).execute()
    if getattr(existing_result, "error", None):
        raise DatabaseError(str(existing_result.error))

    existing_rows = existing_result.data or []
    if not existing_rows:
        raise ResourceNotFoundError("Bien", bien_id)

    existing_sci_id = str(existing_rows[0].get("id_sci") or "")
    _require_sci_access(user_sci_ids, existing_sci_id)

    result = client.table("biens").delete().eq("id", bien_id).execute()

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("bien_deleted", bien_id=bien_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
