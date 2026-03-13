from __future__ import annotations

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
from app.models.associes import AssocieCreate, AssocieResponse, AssocieUpdate

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/associes", tags=["associes"])


def _get_client():
    return get_supabase_service_client()


def _execute_select(query):
    result = query.execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return result.data or []


def _get_user_memberships(client, user_id: str) -> list[dict]:
    return _execute_select(client.table("associes").select("*").eq("user_id", user_id))


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    return [str(row.get("id_sci")) for row in _get_user_memberships(client, user_id) if row.get("id_sci")]


def _require_sci_access(user_sci_ids: list[str], id_sci: str) -> None:
    if not id_sci:
        raise DatabaseError("Missing id_sci on scoped resource")
    if id_sci not in user_sci_ids:
        raise AuthorizationError("SCI", id_sci)


def _fetch_associe(client, associe_id: str) -> dict:
    rows = _execute_select(client.table("associes").select("*").eq("id", associe_id))
    if not rows:
        raise ResourceNotFoundError("Associe", associe_id)
    return rows[0]


def _fetch_associes(client, sci_ids: list[str]) -> list[dict]:
    if not sci_ids:
        return []

    query = client.table("associes").select("*")
    if hasattr(query, "in_"):
        return _execute_select(query.in_("id_sci", sci_ids))

    rows: list[dict] = []
    for sci_id in sci_ids:
        rows.extend(_execute_select(client.table("associes").select("*").eq("id_sci", sci_id)))
    return rows


def _ensure_total_parts_within_bounds(client, id_sci: str, part: float, associe_id: str | None = None) -> None:
    rows = _execute_select(client.table("associes").select("id,part").eq("id_sci", id_sci))
    total = 0.0
    for row in rows:
        if associe_id and str(row.get("id") or "") == associe_id:
            continue
        try:
            total += float(row.get("part") or 0)
        except (TypeError, ValueError):
            continue

    if round(total + float(part), 2) > 100:
        raise ValidationError("La répartition du capital ne peut pas dépasser 100%.")


def _serialize_associe(row: dict) -> dict:
    return {
        **row,
        "is_account_member": bool(row.get("user_id")),
    }


@router.get("", response_model=list[AssocieResponse])
@router.get("/", response_model=list[AssocieResponse])
async def list_associes(
    id_sci: str | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info("listing_associes", user_id=user_id, id_sci=id_sci)

    try:
        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        if id_sci:
            _require_sci_access(user_sci_ids, id_sci)
            user_sci_ids = [id_sci]

        rows = _fetch_associes(client, user_sci_ids)
        rows.sort(key=lambda row: str(row.get("nom") or "").lower())
        return [_serialize_associe(row) for row in rows]
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("list_associes_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list associes")


@router.post("", response_model=AssocieResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AssocieResponse, status_code=status.HTTP_201_CREATED)
async def create_associe(payload: AssocieCreate, user_id: str = Depends(get_current_user)):
    logger.info("creating_associe", user_id=user_id, id_sci=payload.id_sci, nom=payload.nom)

    try:
        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        _require_sci_access(user_sci_ids, payload.id_sci)
        _ensure_total_parts_within_bounds(client, payload.id_sci, payload.part)

        result = client.table("associes").insert(payload.model_dump(mode="json")).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create associe")

        return _serialize_associe(rows[0])
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("create_associe_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create associe")


@router.patch("/{associe_id}", response_model=AssocieResponse)
async def update_associe(
    associe_id: str,
    payload: AssocieUpdate,
    user_id: str = Depends(get_current_user),
):
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info(
        "updating_associe",
        associe_id=associe_id,
        user_id=user_id,
        fields=list(update_payload.keys()),
    )

    try:
        if not update_payload:
            raise ValidationError("No update fields provided")

        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_associe(client, associe_id)
        id_sci = str(existing.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        next_part = float(update_payload["part"]) if "part" in update_payload else float(existing.get("part") or 0)
        _ensure_total_parts_within_bounds(client, id_sci, next_part, associe_id=associe_id)

        result = client.table("associes").update(update_payload).eq("id", associe_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise ResourceNotFoundError("Associe", associe_id)

        return _serialize_associe(rows[0])
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("update_associe_failed", associe_id=associe_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update associe")


@router.delete("/{associe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_associe(associe_id: str, user_id: str = Depends(get_current_user)):
    logger.info("deleting_associe", associe_id=associe_id, user_id=user_id)

    try:
        client = _get_client()
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_associe(client, associe_id)
        id_sci = str(existing.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        sci_associes = _execute_select(client.table("associes").select("id").eq("id_sci", id_sci))
        if len(sci_associes) <= 1:
            raise ValidationError("La SCI doit conserver au moins un associé.")

        if existing.get("role") == "gerant":
            gerants = _execute_select(
                client.table("associes").select("id").eq("id_sci", id_sci).eq("role", "gerant")
            )
            if len(gerants) <= 1:
                raise ValidationError("Impossible de supprimer le dernier gérant de la SCI.")

        if str(existing.get("user_id") or "") == user_id:
            raise ValidationError("Supprime ou transfère d'abord l'accès du compte depuis un autre associé.")

        result = client.table("associes").delete().eq("id", associe_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("delete_associe_failed", associe_id=associe_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete associe")
