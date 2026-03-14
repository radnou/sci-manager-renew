from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from app.core.supabase_client import get_supabase_user_client
from app.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    SCIManagerException,
    ValidationError,
)
from app.core.security import get_current_user
from app.models.charges import ChargeCreate, ChargeResponse, ChargeUpdate
from app.services.subscription_service import SubscriptionService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/charges", tags=["charges"])


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


def _fetch_accessible_biens(client, sci_ids: list[str]) -> list[dict]:
    if not sci_ids:
        return []

    query = client.table("biens").select("id,id_sci,adresse,ville")
    if hasattr(query, "in_"):
        return _execute_select(query.in_("id_sci", sci_ids))

    rows: list[dict] = []
    for sci_id in sci_ids:
        rows.extend(_execute_select(client.table("biens").select("id,id_sci,adresse,ville").eq("id_sci", sci_id)))
    return rows


def _fetch_bien(client, bien_id: str) -> dict:
    rows = _execute_select(client.table("biens").select("id,id_sci,adresse,ville").eq("id", bien_id))
    if not rows:
        raise ValidationError(f"Unknown bien id: {bien_id}")
    return rows[0]


def _fetch_charge(client, charge_id: str) -> dict:
    rows = _execute_select(client.table("charges").select("*").eq("id", charge_id))
    if not rows:
        raise ResourceNotFoundError("Charge", charge_id)
    return rows[0]


def _fetch_charges_by_bien_ids(client, bien_ids: list[str]) -> list[dict]:
    if not bien_ids:
        return []

    query = client.table("charges").select("*")
    if hasattr(query, "in_"):
        return _execute_select(query.in_("id_bien", bien_ids))

    rows: list[dict] = []
    for bien_id in bien_ids:
        rows.extend(_execute_select(client.table("charges").select("*").eq("id_bien", bien_id)))
    return rows


def _serialize_charge(row: dict, bien_map: dict[str, dict]) -> dict:
    bien = bien_map.get(str(row.get("id_bien") or ""))
    return {
        **row,
        "id_sci": str(bien.get("id_sci")) if bien and bien.get("id_sci") else None,
        "bien_adresse": bien.get("adresse") if bien else None,
        "bien_ville": bien.get("ville") if bien else None,
    }


@router.get("", response_model=list[ChargeResponse])
@router.get("/", response_model=list[ChargeResponse])
async def list_charges(
    request: Request,
    id_sci: str | None = None,
    id_bien: str | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info("listing_charges", user_id=user_id, id_sci=id_sci, id_bien=id_bien)

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "charges_enabled")
        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        if id_sci:
            _require_sci_access(user_sci_ids, id_sci)

        accessible_biens = _fetch_accessible_biens(client, user_sci_ids)
        if id_sci:
            accessible_biens = [bien for bien in accessible_biens if str(bien.get("id_sci") or "") == id_sci]

        bien_map = {str(bien.get("id")): bien for bien in accessible_biens if bien.get("id")}
        if id_bien:
            if id_bien not in bien_map:
                raise AuthorizationError("Bien", id_bien)
            bien_ids = [id_bien]
        else:
            bien_ids = list(bien_map.keys())

        rows = _fetch_charges_by_bien_ids(client, bien_ids)
        rows.sort(key=lambda row: str(row.get("date_paiement") or ""), reverse=True)
        return [_serialize_charge(row, bien_map) for row in rows]
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("list_charges_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list charges")


@router.post("", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_charge(payload: ChargeCreate, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("creating_charge", user_id=user_id, id_bien=payload.id_bien, type_charge=payload.type_charge)

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "charges_enabled")
        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        bien = _fetch_bien(client, payload.id_bien)
        id_sci = str(bien.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        result = client.table("charges").insert(payload.model_dump(mode="json")).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create charge")

        return _serialize_charge(rows[0], {str(bien.get("id")): bien})
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("create_charge_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create charge")


@router.patch("/{charge_id}", response_model=ChargeResponse)
async def update_charge(charge_id: str, payload: ChargeUpdate, request: Request, user_id: str = Depends(get_current_user)):
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_charge", charge_id=charge_id, user_id=user_id, fields=list(update_payload.keys()))

    try:
        if not update_payload:
            raise ValidationError("No update fields provided")

        SubscriptionService.ensure_feature_enabled(user_id, "charges_enabled")
        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_charge(client, charge_id)
        bien = _fetch_bien(client, str(existing.get("id_bien") or ""))
        id_sci = str(bien.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        result = client.table("charges").update(update_payload).eq("id", charge_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise ResourceNotFoundError("Charge", charge_id)

        return _serialize_charge(rows[0], {str(bien.get("id")): bien})
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("update_charge_failed", charge_id=charge_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update charge")


@router.delete("/{charge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_charge(charge_id: str, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("deleting_charge", charge_id=charge_id, user_id=user_id)

    try:
        SubscriptionService.ensure_feature_enabled(user_id, "charges_enabled")
        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_charge(client, charge_id)
        bien = _fetch_bien(client, str(existing.get("id_bien") or ""))
        id_sci = str(bien.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        result = client.table("charges").delete().eq("id", charge_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("delete_charge_failed", charge_id=charge_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete charge")
