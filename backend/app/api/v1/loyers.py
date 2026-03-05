from datetime import date
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import create_client

from app.core.config import settings
from app.core.security import get_current_user
from app.models.loyers import LoyerCreate, LoyerResponse, LoyerUpdate

router = APIRouter(prefix="/loyers", tags=["loyers"])
logger = structlog.get_logger(__name__)


def _get_client() -> Any:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def _extract_rows(result: Any) -> list[dict[str, Any]]:
    if getattr(result, "error", None):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase query failed",
        )
    rows = getattr(result, "data", None)
    if rows is None:
        return []
    return list(rows)


@router.get("/", response_model=list[LoyerResponse])
async def get_loyers(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user_id: str = Depends(get_current_user),
) -> list[LoyerResponse]:
    client = _get_client()
    query = client.table("loyers").select("*").eq("owner_id", user_id)

    if date_from is not None:
        query = query.gte("date_loyer", date_from.isoformat())
    if date_to is not None:
        query = query.lte("date_loyer", date_to.isoformat())

    result = query.execute()
    return [LoyerResponse.model_validate(row) for row in _extract_rows(result)]


@router.get("/{loyer_id}", response_model=LoyerResponse)
async def get_loyer(loyer_id: str, user_id: str = Depends(get_current_user)) -> LoyerResponse:
    client = _get_client()
    result = (
        client.table("loyers")
        .select("*")
        .eq("id", loyer_id)
        .eq("owner_id", user_id)
        .execute()
    )
    rows = _extract_rows(result)
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyer not found")
    return LoyerResponse.model_validate(rows[0])


@router.post("/", response_model=LoyerResponse, status_code=status.HTTP_201_CREATED)
async def create_loyer(
    loyer: LoyerCreate,
    user_id: str = Depends(get_current_user),
) -> LoyerResponse:
    logger.info(
        "creating_loyer",
        user_id=user_id,
        bien_id=loyer.id_bien,
        montant=float(loyer.montant),
        date_loyer=str(loyer.date_loyer),
    )
    client = _get_client()
    payload = loyer.model_dump()
    payload["owner_id"] = user_id
    result = client.table("loyers").insert(payload).execute()
    rows = _extract_rows(result)
    if not rows:
        logger.error("loyer_creation_failed", user_id=user_id, bien_id=loyer.id_bien)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loyer creation failed",
        )
    loyer_id = rows[0].get("id")
    logger.info("loyer_created", user_id=user_id, loyer_id=loyer_id, bien_id=loyer.id_bien)
    return LoyerResponse.model_validate(rows[0])


@router.patch("/{loyer_id}", response_model=LoyerResponse)
async def update_loyer(
    loyer_id: str,
    loyer: LoyerUpdate,
    user_id: str = Depends(get_current_user),
) -> LoyerResponse:
    payload = loyer.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )

    logger.info(
        "updating_loyer",
        user_id=user_id,
        loyer_id=loyer_id,
        fields=list(payload.keys()),
    )
    client = _get_client()
    result = (
        client.table("loyers")
        .update(payload)
        .eq("id", loyer_id)
        .eq("owner_id", user_id)
        .execute()
    )
    rows = _extract_rows(result)
    if not rows:
        logger.warning("loyer_not_found_for_update", user_id=user_id, loyer_id=loyer_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyer not found")
    logger.info("loyer_updated", user_id=user_id, loyer_id=loyer_id)
    return LoyerResponse.model_validate(rows[0])


@router.delete("/{loyer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loyer(loyer_id: str, user_id: str = Depends(get_current_user)) -> None:
    logger.info("deleting_loyer", user_id=user_id, loyer_id=loyer_id)
    client = _get_client()
    result = (
        client.table("loyers")
        .delete()
        .eq("id", loyer_id)
        .eq("owner_id", user_id)
        .execute()
    )
    rows = _extract_rows(result)
    if not rows:
        logger.warning("loyer_not_found_for_delete", user_id=user_id, loyer_id=loyer_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyer not found")
    logger.info("loyer_deleted", user_id=user_id, loyer_id=loyer_id)
