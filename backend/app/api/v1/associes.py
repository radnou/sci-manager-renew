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
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.models.associes import AssocieCreate, AssocieResponse, AssocieUpdate

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/associes", tags=["associes"])





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


def _ensure_total_parts_within_bounds(client, id_sci: str, nb_parts: int, associe_id: str | None = None) -> None:
    sci_rows = _execute_select(client.table("sci").select("nb_parts_total").eq("id", id_sci))
    nb_parts_total = 1000
    if sci_rows and sci_rows[0].get("nb_parts_total") is not None:
        nb_parts_total = int(sci_rows[0]["nb_parts_total"])

    rows = _execute_select(client.table("associes").select("id,nb_parts,part").eq("id_sci", id_sci))
    total = 0
    for row in rows:
        if associe_id and str(row.get("id") or "") == associe_id:
            continue
        row_nb = row.get("nb_parts")
        if row_nb is None and row.get("part") is not None:
            try:
                row_nb = int(round((float(row["part"]) / 100.0) * nb_parts_total))
            except (ValueError, TypeError):
                row_nb = 0
        total += int(row_nb or 0)

    if total + nb_parts > nb_parts_total:
        raise ValidationError(f"La répartition des parts ne peut pas dépasser le total des parts de la SCI ({nb_parts_total}).")


def _serialize_associe(client, row: dict, warning: str | None = None) -> dict:
    id_sci = str(row.get("id_sci") or "")
    nb_parts_total = 1000
    if id_sci:
        try:
            sci_rows = _execute_select(client.table("sci").select("nb_parts_total").eq("id", id_sci))
            if sci_rows and sci_rows[0].get("nb_parts_total") is not None:
                nb_parts_total = int(sci_rows[0]["nb_parts_total"])
        except Exception:
            pass

    nb_parts = row.get("nb_parts")
    if nb_parts is None and row.get("part") is not None:
        try:
            nb_parts = int(round((float(row["part"]) / 100.0) * nb_parts_total))
        except (ValueError, TypeError):
            nb_parts = 0
    elif nb_parts is None:
        nb_parts = 0

    part_percent = round((nb_parts / nb_parts_total) * 100.0, 2) if nb_parts_total > 0 else 0.0

    data = {
        **row,
        "nb_parts": nb_parts,
        "part": part_percent,
        "is_account_member": bool(row.get("user_id")),
    }
    if warning:
        data["warning"] = warning
    return data


def _compute_parts_warning(client, id_sci: str) -> str | None:
    """Return a warning string if total parts for a SCI are below total parts, else None."""
    sci_rows = _execute_select(client.table("sci").select("nb_parts_total").eq("id", id_sci))
    nb_parts_total = 1000
    if sci_rows and sci_rows[0].get("nb_parts_total") is not None:
        nb_parts_total = int(sci_rows[0]["nb_parts_total"])

    rows = _execute_select(client.table("associes").select("nb_parts,part").eq("id_sci", id_sci))
    total = 0
    for row in rows:
        row_nb = row.get("nb_parts")
        if row_nb is None and row.get("part") is not None:
            try:
                row_nb = int(round((float(row["part"]) / 100.0) * nb_parts_total))
            except (ValueError, TypeError):
                row_nb = 0
        total += int(row_nb or 0)
    if total < nb_parts_total:
        return f"Attention : les parts totalisent {total} sur {nb_parts_total} — elles devraient totaliser {nb_parts_total}."
    return None


@router.get("", response_model=list[AssocieResponse])
@router.get("/", response_model=list[AssocieResponse])
async def list_associes(
    request: Request,
    id_sci: str | None = None,
    user_id: str = Depends(get_current_user),
):
    logger.info("listing_associes", user_id=user_id, id_sci=id_sci)

    try:
        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        if id_sci:
            _require_sci_access(user_sci_ids, id_sci)
            user_sci_ids = [id_sci]

        rows = _fetch_associes(client, user_sci_ids)
        rows.sort(key=lambda row: str(row.get("nom") or "").lower())
        return [_serialize_associe(client, row) for row in rows]
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("list_associes_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list associes")


@router.post("", response_model=AssocieResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AssocieResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_associe(payload: AssocieCreate, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("creating_associe", user_id=user_id, id_sci=payload.id_sci, nom=payload.nom)

    try:
        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        _require_sci_access(user_sci_ids, payload.id_sci)

        # Resolve payload nb_parts and part
        payload_dict = payload.model_dump(mode="json")
        sci_rows = _execute_select(client.table("sci").select("nb_parts_total").eq("id", payload.id_sci))
        nb_parts_total = 1000
        if sci_rows and sci_rows[0].get("nb_parts_total") is not None:
            nb_parts_total = int(sci_rows[0]["nb_parts_total"])

        nb_parts = payload.nb_parts
        if nb_parts is None:
            if payload.part is not None:
                nb_parts = int(round((payload.part / 100.0) * nb_parts_total))
            else:
                nb_parts = 100
        payload_dict["nb_parts"] = nb_parts
        payload_dict["part"] = round((nb_parts / nb_parts_total) * 100.0, 2)

        _ensure_total_parts_within_bounds(client, payload.id_sci, nb_parts)

        result = client.table("associes").insert(payload_dict).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create associe")

        warning = _compute_parts_warning(client, payload.id_sci)
        return _serialize_associe(client, rows[0], warning=warning)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("create_associe_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create associe")


@router.patch("/{associe_id}", response_model=AssocieResponse)
@limiter.limit("30/minute")
async def update_associe(
    associe_id: str,
    payload: AssocieUpdate,
    request: Request,
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

        client = get_supabase_user_client(request)
        user_sci_ids = _get_user_sci_ids(client, user_id)
        existing = _fetch_associe(client, associe_id)
        id_sci = str(existing.get("id_sci") or "")
        _require_sci_access(user_sci_ids, id_sci)

        sci_rows = _execute_select(client.table("sci").select("nb_parts_total").eq("id", id_sci))
        nb_parts_total = 1000
        if sci_rows and sci_rows[0].get("nb_parts_total") is not None:
            nb_parts_total = int(sci_rows[0]["nb_parts_total"])

        if "nb_parts" in update_payload:
            next_nb_parts = int(update_payload["nb_parts"])
        elif "part" in update_payload and update_payload["part"] is not None:
            next_nb_parts = int(round((float(update_payload["part"]) / 100.0) * nb_parts_total))
        else:
            existing_nb_parts = existing.get("nb_parts")
            if existing_nb_parts is None and existing.get("part") is not None:
                existing_nb_parts = int(round((float(existing["part"]) / 100.0) * nb_parts_total))
            elif existing_nb_parts is None:
                existing_nb_parts = 100
            next_nb_parts = int(existing_nb_parts)

        update_payload["nb_parts"] = next_nb_parts
        update_payload["part"] = round((next_nb_parts / nb_parts_total) * 100.0, 2)

        _ensure_total_parts_within_bounds(client, id_sci, next_nb_parts, associe_id=associe_id)

        result = client.table("associes").update(update_payload).eq("id", associe_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise ResourceNotFoundError("Associe", associe_id)

        warning = _compute_parts_warning(client, id_sci)
        return _serialize_associe(client, rows[0], warning=warning)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("update_associe_failed", associe_id=associe_id, user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update associe")


@router.delete("/{associe_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_associe(associe_id: str, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("deleting_associe", associe_id=associe_id, user_id=user_id)

    try:
        client = get_supabase_user_client(request)
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
