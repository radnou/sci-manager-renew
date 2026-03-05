from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client

from app.core.config import settings
from app.core.security import get_current_user
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.services.sci_service import SCIService

router = APIRouter(prefix="/biens", tags=["biens"])
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


def _to_response(row: dict[str, Any]) -> BienResponse:
    metrics = SCIService.calculate_rentabilite(row)
    payload = {**row, **metrics}
    return BienResponse.model_validate(payload)


@router.get("/", response_model=list[BienResponse])
async def get_biens(user_id: str = Depends(get_current_user)) -> list[BienResponse]:
    client = _get_client()
    result = client.table("biens").select("*").eq("owner_id", user_id).execute()
    return [_to_response(row) for row in _extract_rows(result)]


@router.get("/{bien_id}", response_model=BienResponse)
async def get_bien(bien_id: str, user_id: str = Depends(get_current_user)) -> BienResponse:
    client = _get_client()
    result = (
        client.table("biens")
        .select("*")
        .eq("id", bien_id)
        .eq("owner_id", user_id)
        .execute()
    )
    rows = _extract_rows(result)
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bien not found")
    return _to_response(rows[0])


@router.post("/", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
async def create_bien(
    bien: BienCreate,
    user_id: str = Depends(get_current_user),
) -> BienResponse:
    logger.info(
        "creating_bien",
        user_id=user_id,
        adresse=bien.adresse,
        type_locatif=bien.type_locatif,
    )
    client = _get_client()
    payload = bien.model_dump()
    payload["owner_id"] = user_id
    result = client.table("biens").insert(payload).execute()
    rows = _extract_rows(result)
    if not rows:
        logger.error("bien_creation_failed", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bien creation failed",
        )
    bien_id = rows[0].get("id")
    logger.info("bien_created", user_id=user_id, bien_id=bien_id)
    return _to_response(rows[0])


@router.patch("/{bien_id}", response_model=BienResponse)
async def update_bien(
    bien_id: str,
    bien: BienUpdate,
    user_id: str = Depends(get_current_user),
) -> BienResponse:
    update_payload = bien.model_dump(exclude_none=True)
    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )

    logger.info(
        "updating_bien",
        user_id=user_id,
        bien_id=bien_id,
        fields=list(update_payload.keys()),
    )
    client = _get_client()
    result = (
        client.table("biens")
        .update(update_payload)
        .eq("id", bien_id)
        .eq("owner_id", user_id)
        .execute()
    )
    rows = _extract_rows(result)
    if not rows:
        logger.warning("bien_not_found_for_update", user_id=user_id, bien_id=bien_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bien not found")
    logger.info("bien_updated", user_id=user_id, bien_id=bien_id)
    return _to_response(rows[0])


@router.delete("/{bien_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien(bien_id: str, user_id: str = Depends(get_current_user)) -> None:
    logger.info("deleting_bien", user_id=user_id, bien_id=bien_id)
    client = _get_client()
    result = (
        client.table("biens")
        .delete()
        .eq("id", bien_id)
        .eq("owner_id", user_id)
        .execute()
    )
    rows = _extract_rows(result)
    if not rows:
        logger.warning("bien_not_found_for_delete", user_id=user_id, bien_id=bien_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bien not found")
    logger.info("bien_deleted", user_id=user_id, bien_id=bien_id)
