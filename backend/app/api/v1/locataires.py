from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, Depends, Response, status
from app.core.supabase_client import get_supabase_service_client
from app.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    SCIManagerException,
    ValidationError,
)
from app.core.security import get_current_user
from app.models.locataires import LocataireCreate, LocataireResponse, LocataireUpdate

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/locataires", tags=["locataires"])


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


def _fetch_accessible_biens(client, sci_ids: list[str]) -> list[dict]:
    if not sci_ids:
        return []

    query = client.table("biens").select("id,id_sci,adresse,ville")
    if hasattr(query, "in_"):
        result = query.in_("id_sci", sci_ids).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        return result.data or []

    rows: list[dict] = []
    for sci_id in sci_ids:
        result = client.table("biens").select("id,id_sci,adresse,ville").eq("id_sci", sci_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        rows.extend(result.data or [])
    return rows


def _fetch_bien(client, bien_id: str) -> dict:
    result = client.table("biens").select("id,id_sci,adresse,ville").eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    rows = result.data or []
    if not rows:
        raise ValidationError(f"Unknown bien id: {bien_id}")

    return rows[0]


def _fetch_locataires_by_bien_ids(client, bien_ids: list[str]):
    if not bien_ids:
        return []

    query = client.table("locataires").select("*")
    if hasattr(query, "in_"):
        result = query.in_("id_bien", bien_ids).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        return result.data or []

    rows: list[dict] = []
    for bien_id in bien_ids:
        result = client.table("locataires").select("*").eq("id_bien", bien_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        rows.extend(result.data or [])
    return rows


def _validate_date_range(date_from: date, date_to: date | None) -> None:
    if date_to and date_to < date_from:
        raise ValidationError("date_fin must be later than or equal to date_debut")


def _enrich_locataire_rows(locataires: list[dict], bien_map: dict[str, dict]) -> list[dict]:
    enriched_rows: list[dict] = []
    for locataire in locataires:
        bien = bien_map.get(str(locataire.get("id_bien") or ""))
        enriched_rows.append(
            {
                **locataire,
                "id_sci": str(bien.get("id_sci")) if bien and bien.get("id_sci") else None,
            }
        )
    return enriched_rows


@router.get("", response_model=list[LocataireResponse])
@router.get("/", response_model=list[LocataireResponse])
async def list_locataires(
    id_sci: str | None = None,
    id_bien: str | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info("listing_locataires", user_id=user_id, id_sci=id_sci, id_bien=id_bien)

    try:
        client = get_supabase_service_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        if id_sci:
            _require_sci_access(user_sci_ids, id_sci)

        accessible_biens = _fetch_accessible_biens(client, user_sci_ids)
        if id_sci:
            accessible_biens = [
                bien for bien in accessible_biens if str(bien.get("id_sci") or "") == id_sci
            ]

        bien_map = {str(bien.get("id")): bien for bien in accessible_biens if bien.get("id")}
        if id_bien:
            if id_bien not in bien_map:
                raise AuthorizationError("Bien", id_bien)
            bien_ids = [id_bien]
        else:
            bien_ids = list(bien_map.keys())

        rows = _fetch_locataires_by_bien_ids(client, bien_ids)
        return _enrich_locataire_rows(rows, bien_map)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("list_locataires_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list locataires")


@router.post("", response_model=LocataireResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=LocataireResponse, status_code=status.HTTP_201_CREATED)
async def create_locataire(payload: LocataireCreate, user_id: str = Depends(get_current_user)):
    logger.info("creating_locataire", user_id=user_id, bien_id=payload.id_bien, nom=payload.nom)

    try:
        _validate_date_range(payload.date_debut, payload.date_fin)
        client = get_supabase_service_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        bien = _fetch_bien(client, payload.id_bien)
        bien_sci_id = str(bien.get("id_sci") or "")
        _require_sci_access(user_sci_ids, bien_sci_id)

        result = client.table("locataires").insert(payload.model_dump(mode="json")).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        data = result.data or []
        if not data:
            raise DatabaseError("Unable to create locataire")

        created = data[0]
        return {**created, "id_sci": bien_sci_id}
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("create_locataire_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create locataire")


@router.patch("/{locataire_id}", response_model=LocataireResponse)
async def update_locataire(
    locataire_id: str,
    payload: LocataireUpdate,
    user_id: str = Depends(get_current_user),
):
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info(
        "updating_locataire",
        locataire_id=locataire_id,
        user_id=user_id,
        fields=list(update_payload.keys()),
    )

    try:
        if not update_payload:
            raise ValidationError("No update fields provided")

        client = get_supabase_service_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing_result = client.table("locataires").select("*").eq("id", locataire_id).execute()
        if getattr(existing_result, "error", None):
            raise DatabaseError(str(existing_result.error))

        existing_rows = existing_result.data or []
        if not existing_rows:
            raise ResourceNotFoundError("Locataire", locataire_id)

        existing = existing_rows[0]
        bien = _fetch_bien(client, str(existing.get("id_bien") or ""))
        bien_sci_id = str(bien.get("id_sci") or "")
        _require_sci_access(user_sci_ids, bien_sci_id)

        next_date_debut = (
            update_payload["date_debut"]
            if "date_debut" in update_payload
            else existing.get("date_debut")
        )
        next_date_fin = (
            update_payload["date_fin"] if "date_fin" in update_payload else existing.get("date_fin")
        )
        _validate_date_range(
            date.fromisoformat(str(next_date_debut)),
            date.fromisoformat(str(next_date_fin)) if next_date_fin else None,
        )

        result = client.table("locataires").update(update_payload).eq("id", locataire_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        data = result.data or []
        if not data:
            raise ResourceNotFoundError("Locataire", locataire_id)

        return {**data[0], "id_sci": bien_sci_id}
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("update_locataire_failed", user_id=user_id, locataire_id=locataire_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update locataire")


@router.delete("/{locataire_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_locataire(locataire_id: str, user_id: str = Depends(get_current_user)):
    logger.info("deleting_locataire", locataire_id=locataire_id, user_id=user_id)

    try:
        client = get_supabase_service_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing_result = client.table("locataires").select("*").eq("id", locataire_id).execute()
        if getattr(existing_result, "error", None):
            raise DatabaseError(str(existing_result.error))

        existing_rows = existing_result.data or []
        if not existing_rows:
            raise ResourceNotFoundError("Locataire", locataire_id)

        bien = _fetch_bien(client, str(existing_rows[0].get("id_bien") or ""))
        bien_sci_id = str(bien.get("id_sci") or "")
        _require_sci_access(user_sci_ids, bien_sci_id)

        result = client.table("locataires").delete().eq("id", locataire_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("delete_locataire_failed", user_id=user_id, locataire_id=locataire_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete locataire")
