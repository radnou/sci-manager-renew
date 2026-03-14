from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client
from app.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    SCIManagerException,
    ValidationError,
)
from app.core.security import get_current_user
from app.models.fiscalite import FiscaliteCreate, FiscaliteResponse, FiscaliteUpdate
from app.services.subscription_service import SubscriptionService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/fiscalite", tags=["fiscalite"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    """Service client for INSERT operations — RLS blocks inserts before membership exists."""
    return get_supabase_service_client()


def _execute_select(query):
    result = query.execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return result.data or []


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    rows = _execute_select(client.table("associes").select("id_sci").eq("user_id", user_id))
    return [str(row.get("id_sci")) for row in rows if row.get("id_sci")]


def _require_sci_access(user_sci_ids: list[str], id_sci: str) -> None:
    if not id_sci:
        raise DatabaseError("Missing id_sci on scoped resource")
    if id_sci not in user_sci_ids:
        raise AuthorizationError("SCI", id_sci)


def _fetch_scis(client, sci_ids: list[str]) -> list[dict]:
    if not sci_ids:
        return []

    query = client.table("sci").select("id,nom,regime_fiscal")
    if hasattr(query, "in_"):
        return _execute_select(query.in_("id", sci_ids))

    rows: list[dict] = []
    for sci_id in sci_ids:
        rows.extend(_execute_select(client.table("sci").select("id,nom,regime_fiscal").eq("id", sci_id)))
    return rows


def _fetch_fiscalite(client, fiscalite_id: str) -> dict:
    rows = _execute_select(client.table("fiscalite").select("*").eq("id", fiscalite_id))
    if not rows:
        raise ResourceNotFoundError("Fiscalite", fiscalite_id)
    return rows[0]


def _fetch_fiscalite_rows(client, sci_ids: list[str]) -> list[dict]:
    if not sci_ids:
        return []

    query = client.table("fiscalite").select("*")
    if hasattr(query, "in_"):
        return _execute_select(query.in_("id_sci", sci_ids))

    rows: list[dict] = []
    for sci_id in sci_ids:
        rows.extend(_execute_select(client.table("fiscalite").select("*").eq("id_sci", sci_id)))
    return rows


def _serialize_fiscalite(row: dict, sci_map: dict[str, dict]) -> dict:
    sci = sci_map.get(str(row.get("id_sci") or ""))
    return {
        **row,
        "regime_fiscal": sci.get("regime_fiscal") if sci else None,
        "nom_sci": sci.get("nom") if sci else None,
    }


def _compute_resultat_fiscal(total_revenus: float, total_charges: float) -> float:
    return round(float(total_revenus) - float(total_charges), 2)


@router.get("", response_model=list[FiscaliteResponse])
@router.get("/", response_model=list[FiscaliteResponse])
async def list_fiscalite(
    request: Request,
    id_sci: str | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info("listing_fiscalite", user_id=user_id, id_sci=id_sci)

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "fiscalite_enabled")
        client = _get_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        if id_sci:
            _require_sci_access(user_sci_ids, id_sci)
            user_sci_ids = [id_sci]

        scis = _fetch_scis(client, user_sci_ids)
        sci_map = {str(sci.get("id")): sci for sci in scis if sci.get("id")}
        rows = _fetch_fiscalite_rows(client, user_sci_ids)
        rows.sort(key=lambda row: (int(row.get("annee") or 0), str(row.get("id_sci") or "")), reverse=True)
        return [_serialize_fiscalite(row, sci_map) for row in rows]
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("list_fiscalite_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list fiscalite")


@router.post("", response_model=FiscaliteResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FiscaliteResponse, status_code=status.HTTP_201_CREATED)
async def create_fiscalite(payload: FiscaliteCreate, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("creating_fiscalite", user_id=user_id, id_sci=payload.id_sci, annee=payload.annee)

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "fiscalite_enabled")
        client = _get_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        _require_sci_access(user_sci_ids, payload.id_sci)
        scis = _fetch_scis(client, [payload.id_sci])
        if not scis:
            raise ResourceNotFoundError("SCI", payload.id_sci)

        insert_payload = payload.model_dump(mode="json")
        insert_payload["resultat_fiscal"] = payload.resultat_fiscal
        write_client = _get_write_client()
        result = write_client.table("fiscalite").insert(insert_payload).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create fiscalite")

        return _serialize_fiscalite(rows[0], {str(scis[0].get("id")): scis[0]})
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("create_fiscalite_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create fiscalite")


@router.patch("/{fiscalite_id}", response_model=FiscaliteResponse)
async def update_fiscalite(
    fiscalite_id: str,
    payload: FiscaliteUpdate,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info(
        "updating_fiscalite",
        fiscalite_id=fiscalite_id,
        user_id=user_id,
        fields=list(update_payload.keys()),
    )

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "fiscalite_enabled")
        client = _get_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_fiscalite(client, fiscalite_id)
        id_sci = str(existing.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        total_revenus = float(update_payload.get("total_revenus", existing.get("total_revenus") or 0))
        total_charges = float(update_payload.get("total_charges", existing.get("total_charges") or 0))
        update_payload["resultat_fiscal"] = _compute_resultat_fiscal(total_revenus, total_charges)

        result = client.table("fiscalite").update(update_payload).eq("id", fiscalite_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise ResourceNotFoundError("Fiscalite", fiscalite_id)

        scis = _fetch_scis(client, [id_sci])
        sci_map = {str(sci.get("id")): sci for sci in scis if sci.get("id")}
        return _serialize_fiscalite(rows[0], sci_map)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("update_fiscalite_failed", fiscalite_id=fiscalite_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update fiscalite")


@router.delete("/{fiscalite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fiscalite(fiscalite_id: str, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("deleting_fiscalite", fiscalite_id=fiscalite_id, user_id=user_id)

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "fiscalite_enabled")
        client = _get_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_fiscalite(client, fiscalite_id)
        _require_sci_access(user_sci_ids, str(existing.get("id_sci") or ""))

        result = client.table("fiscalite").delete().eq("id", fiscalite_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("delete_fiscalite_failed", fiscalite_id=fiscalite_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete fiscalite")
