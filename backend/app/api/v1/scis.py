from __future__ import annotations

from collections import defaultdict
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field
from app.core.config import settings
from app.core.supabase_client import get_supabase_user_client
from app.core.exceptions import DatabaseError, ResourceNotFoundError, UpgradeRequiredError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.security import get_current_user
from app.models.biens import BienResponse
from app.models.loyers import LoyerResponse
from app.models.sci import SCICreate, SCIResponse, SCIUpdate
from app.services.email_service import email_service
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/scis", tags=["scis"])
logger = structlog.get_logger(__name__)


class AssocieOverview(BaseModel):
    id: str
    user_id: str | None = None
    nom: str
    email: str | None = None
    part: float | None = None
    role: str | None = None

    model_config = ConfigDict(extra="ignore")


class SCIOverview(BaseModel):
    id: str
    nom: str
    siren: str | None = None
    regime_fiscal: str = "IR"
    statut: str
    associes_count: int = Field(default=0, ge=0)
    biens_count: int = Field(default=0, ge=0)
    loyers_count: int = Field(default=0, ge=0)
    user_role: str | None = None
    user_part: float | None = None
    associes: list[AssocieOverview] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ChargeOverview(BaseModel):
    id: str
    id_bien: str
    type_charge: str
    montant: float
    date_paiement: str

    model_config = ConfigDict(extra="ignore")


class FiscaliteOverview(BaseModel):
    id: str
    id_sci: str
    annee: int
    total_revenus: float = 0
    total_charges: float = 0
    resultat_fiscal: float = 0

    model_config = ConfigDict(extra="ignore")


class SCIDetail(SCIOverview):
    charges_count: int = Field(default=0, ge=0)
    total_monthly_rent: float = 0
    total_monthly_property_charges: float = 0
    total_recorded_charges: float = 0
    paid_loyers_total: float = 0
    pending_loyers_total: float = 0
    biens: list[BienResponse] = Field(default_factory=list)
    recent_loyers: list[LoyerResponse] = Field(default_factory=list)
    recent_charges: list[ChargeOverview] = Field(default_factory=list)
    fiscalite: list[FiscaliteOverview] = Field(default_factory=list)


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _execute_select(query):
    result = query.execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return result.data or []


def _select_by_ids(client, table_name: str, ids: list[str], fields: str = "*") -> list[dict]:
    return _select_by_field_values(client, table_name, "id", ids, fields=fields)


def _select_by_field_values(
    client,
    table_name: str,
    field_name: str,
    values: list[str],
    fields: str = "*",
) -> list[dict]:
    if not values:
        return []

    query = client.table(table_name).select(fields)
    if hasattr(query, "in_"):
        return _execute_select(query.in_(field_name, values))

    rows: list[dict] = []
    for value in values:
        rows.extend(_execute_select(client.table(table_name).select(fields).eq(field_name, value)))
    return rows


def _select_by_scope(client, table_name: str, sci_ids: list[str], fields: str = "*") -> list[dict]:
    return _select_by_field_values(client, table_name, "id_sci", sci_ids, fields=fields)


def _get_user_memberships(client, user_id: str) -> list[dict]:
    return _execute_select(client.table("associes").select("*").eq("user_id", user_id))


def _derive_sci_status(biens_count: int, loyers_count: int) -> str:
    if biens_count == 0:
        return "configuration"
    if loyers_count == 0:
        return "mise_en_service"
    return "exploitation"


def _sort_rows_desc(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get(key) or ""), reverse=True)


def _sum_numeric(rows: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        try:
            total += float(value)
        except (TypeError, ValueError):
            continue
    return round(total, 2)


def _build_sci_overview(
    sci_row: dict,
    memberships: list[dict],
    associes_rows: list[dict],
    biens_rows: list[dict],
    loyers_rows: list[dict],
) -> SCIOverview | None:
    sci_id = str(sci_row.get("id") or "")
    if not sci_id:
        return None

    related_associes = [row for row in associes_rows if str(row.get("id_sci") or "") == sci_id]
    related_biens = [row for row in biens_rows if str(row.get("id_sci") or "") == sci_id]
    related_loyers = [row for row in loyers_rows if str(row.get("id_sci") or "") == sci_id]
    membership = next((row for row in memberships if str(row.get("id_sci") or "") == sci_id), {})

    return SCIOverview(
        id=sci_id,
        nom=str(sci_row.get("nom") or f"SCI {sci_id[:8]}"),
        siren=sci_row.get("siren"),
        regime_fiscal=str(sci_row.get("regime_fiscal") or "IR"),
        statut=_derive_sci_status(len(related_biens), len(related_loyers)),
        associes_count=len(related_associes),
        biens_count=len(related_biens),
        loyers_count=len(related_loyers),
        user_role=membership.get("role"),
        user_part=membership.get("part"),
        associes=[AssocieOverview(**associe) for associe in related_associes],
    )


@router.get("", response_model=list[SCIOverview])
@router.get("/", response_model=list[SCIOverview])
async def list_scis(request: Request, user_id: str = Depends(get_current_user)):
    client = _get_client(request)

    memberships = _get_user_memberships(client, user_id)
    sci_ids = [str(row.get("id_sci")) for row in memberships if row.get("id_sci")]
    if not sci_ids:
        return []

    sci_rows = _select_by_ids(client, "sci", sci_ids)
    associes_rows = _select_by_scope(client, "associes", sci_ids)
    biens_rows = _select_by_scope(client, "biens", sci_ids, fields="id,id_sci")
    loyers_rows = _select_by_scope(client, "loyers", sci_ids, fields="id,id_sci")

    overviews: list[SCIOverview] = []
    for sci_row in sci_rows:
        overview = _build_sci_overview(sci_row, memberships, associes_rows, biens_rows, loyers_rows)
        if overview:
            overviews.append(overview)

    overviews.sort(key=lambda sci: sci.nom.lower())
    return overviews


@router.get("/{sci_id}", response_model=SCIDetail)
async def get_sci_detail(sci_id: str, request: Request, user_id: str = Depends(get_current_user)):
    client = _get_client(request)

    memberships = _get_user_memberships(client, user_id)
    user_sci_ids = [str(row.get("id_sci")) for row in memberships if row.get("id_sci")]
    if sci_id not in user_sci_ids:
        raise ResourceNotFoundError("SCI", sci_id)

    sci_rows = _execute_select(client.table("sci").select("*").eq("id", sci_id))
    if not sci_rows:
        raise ResourceNotFoundError("SCI", sci_id)

    associes_rows = _execute_select(client.table("associes").select("*").eq("id_sci", sci_id))
    biens_rows = _execute_select(client.table("biens").select("*").eq("id_sci", sci_id))
    loyers_rows = _execute_select(client.table("loyers").select("*").eq("id_sci", sci_id))
    fiscalite_rows = _execute_select(client.table("fiscalite").select("*").eq("id_sci", sci_id))

    bien_ids = [str(row.get("id")) for row in biens_rows if row.get("id")]
    charges_rows = _select_by_field_values(client, "charges", "id_bien", bien_ids)

    if not loyers_rows and bien_ids:
        loyers_rows = _select_by_field_values(client, "loyers", "id_bien", bien_ids)
        for loyer_row in loyers_rows:
            loyer_row.setdefault("id_sci", sci_id)

    overview = _build_sci_overview(sci_rows[0], memberships, associes_rows, biens_rows, loyers_rows)
    if not overview:
        raise ResourceNotFoundError("SCI", sci_id)

    paid_loyers = [row for row in loyers_rows if str(row.get("statut") or "").lower() == "paye"]
    pending_loyers = [row for row in loyers_rows if str(row.get("statut") or "").lower() != "paye"]

    return SCIDetail(
        **overview.model_dump(),
        charges_count=len(charges_rows),
        total_monthly_rent=_sum_numeric(biens_rows, "loyer_cc"),
        total_monthly_property_charges=_sum_numeric(biens_rows, "charges"),
        total_recorded_charges=_sum_numeric(charges_rows, "montant"),
        paid_loyers_total=_sum_numeric(paid_loyers, "montant"),
        pending_loyers_total=_sum_numeric(pending_loyers, "montant"),
        biens=[BienResponse(**bien) for bien in biens_rows],
        recent_loyers=[LoyerResponse(**loyer) for loyer in _sort_rows_desc(loyers_rows, "date_loyer")[:8]],
        recent_charges=[ChargeOverview(**charge) for charge in _sort_rows_desc(charges_rows, "date_paiement")[:8]],
        fiscalite=[FiscaliteOverview(**fiscalite) for fiscalite in _sort_rows_desc(fiscalite_rows, "annee")[:4]],
    )


@router.post("", response_model=SCIResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SCIResponse, status_code=status.HTTP_201_CREATED)
async def create_sci(payload: SCICreate, request: Request, user_id: str = Depends(get_current_user)):
    logger.info("creating_sci", user_id=user_id, nom=payload.nom)

    summary = SubscriptionService.enforce_limit(user_id, "scis")
    plan_key = str(summary.get("plan_key") or "")
    features = summary.get("features") or {}
    if summary.get("current_scis", 0) > 0 and not features.get("multi_sci_enabled", False):
        raise UpgradeRequiredError(
            "Le plan actif n'autorise pas la gestion de plusieurs SCI.",
            plan_key=plan_key,
        )

    client = _get_client(request)
    result = client.table("sci").insert(payload.model_dump(mode="json")).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    rows = result.data or []
    if not rows:
        raise DatabaseError("Unable to create SCI")

    created = rows[0]

    # Fetch user email from Supabase Auth for a meaningful associé name
    _associe_nom = "Gérant"
    try:
        _user_resp = client.auth.admin.get_user_by_id(user_id)
        if _user_resp and getattr(_user_resp, "user", None):
            _associe_nom = _user_resp.user.email or "Gérant"
    except Exception:
        pass

    associe_result = client.table("associes").insert(
        {
            "id_sci": created["id"],
            "user_id": user_id,
            "nom": _associe_nom,
            "email": None,
            "part": 100,
            "role": "gerant",
        }
    ).execute()
    if getattr(associe_result, "error", None):
        raise DatabaseError(str(associe_result.error))

    logger.info("sci_created", user_id=user_id, sci_id=created.get("id"), plan_key=plan_key)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE a SCI
# ──────────────────────────────────────────────────────────────

async def _require_gerant_for_sci(sci_id: str, request: Request, user_id: str = Depends(get_current_user)) -> str:
    """Verify user is gérant of the given SCI. Returns user_id."""
    client = _get_client(request)
    rows = _execute_select(
        client.table("associes").select("role").eq("id_sci", sci_id).eq("user_id", user_id)
    )
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SCI non trouvée")
    if rows[0].get("role") != "gerant":
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Réservé au gérant")
    return user_id


@router.patch("/{sci_id}", response_model=SCIResponse)
async def update_sci(
    sci_id: str,
    payload: SCIUpdate,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Met à jour une SCI (gérant uniquement)."""
    await _require_gerant_for_sci(sci_id, request, user_id)

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise ResourceNotFoundError("SCI", sci_id)

    client = _get_client(request)
    result = client.table("sci").update(updates).eq("id", sci_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    rows = result.data or []
    if not rows:
        raise ResourceNotFoundError("SCI", sci_id)

    logger.info("sci_updated", sci_id=sci_id, fields=list(updates.keys()))
    return rows[0]


# ──────────────────────────────────────────────────────────────
# DELETE a SCI
# ──────────────────────────────────────────────────────────────

@router.delete("/{sci_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sci(
    sci_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Supprime une SCI et toutes ses données associées (gérant uniquement)."""
    await _require_gerant_for_sci(sci_id, request, user_id)

    client = _get_client(request)

    # Delete biens-linked tables via bien IDs first
    biens_rows = _execute_select(client.table("biens").select("id").eq("id_sci", sci_id))
    bien_ids = [str(row["id"]) for row in biens_rows if row.get("id")]
    if bien_ids:
        for bid in bien_ids:
            try:
                baux_rows = _execute_select(client.table("baux").select("id").eq("id_bien", bid))
                bail_ids = [str(b["id"]) for b in baux_rows if b.get("id")]
                if bail_ids:
                    for bail_id in bail_ids:
                        client.table("bail_locataires").delete().eq("id_bail", bail_id).execute()
            except Exception:
                pass
        for table in ["charges", "loyers", "baux", "locataires", "documents_bien", "assurances_pno", "frais_agence"]:
            for bid in bien_ids:
                try:
                    client.table(table).delete().eq("id_bien", bid).execute()
                except Exception:
                    pass

    # Delete direct children by id_sci
    for table in ["biens", "associes", "fiscalite", "notifications", "notification_preferences"]:
        try:
            client.table(table).delete().eq("id_sci", sci_id).execute()
        except Exception:
            pass

    # Finally delete the SCI itself
    result = client.table("sci").delete().eq("id", sci_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("sci_deleted", sci_id=sci_id)


# ──────────────────────────────────────────────────────────────
# LIST associes of a SCI
# ──────────────────────────────────────────────────────────────

@router.get("/{sci_id}/associes", response_model=list[AssocieOverview])
async def list_sci_associes(
    sci_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les associés d'une SCI (membre requis)."""
    client = _get_client(request)
    rows = _execute_select(client.table("associes").select("*").eq("id_sci", sci_id))
    return [AssocieOverview(**row) for row in rows]


# ──────────────────────────────────────────────────────────────
# INVITE associe to a SCI
# ──────────────────────────────────────────────────────────────

class InviteAssociePayload(BaseModel):
    nom: str
    email: str | None = None
    part: float = 0
    role: str = "associe"


class InviteAssocieResponse(AssocieOverview):
    email_sent: bool = False


@router.post("/{sci_id}/associes", response_model=InviteAssocieResponse, status_code=status.HTTP_201_CREATED)
async def invite_sci_associe(
    sci_id: str,
    payload: InviteAssociePayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Invite un associé à la SCI (gérant uniquement)."""
    logger.info("inviting_associe", sci_id=sci_id, nom=payload.nom)

    client = _get_client(request)
    row = payload.model_dump(mode="json")
    row["id_sci"] = sci_id

    result = client.table("associes").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create associe")

    created = data[0]
    logger.info("associe_invited", associe_id=created.get("id"), sci_id=sci_id)

    # Best-effort email invitation
    email_sent = False
    if payload.email:
        # Fetch SCI name for the email
        sci_nom = "votre SCI"
        try:
            sci_rows = _execute_select(
                client.table("sci").select("nom").eq("id", sci_id)
            )
            if sci_rows:
                sci_nom = sci_rows[0].get("nom") or sci_nom
        except Exception:
            pass

        # Fetch inviter name from their own associé record
        inviter_nom = "Le gérant"
        try:
            inviter_rows = _execute_select(
                client.table("associes")
                .select("nom")
                .eq("id_sci", sci_id)
                .eq("user_id", membership.user_id)
            )
            if inviter_rows and inviter_rows[0].get("nom"):
                inviter_nom = inviter_rows[0]["nom"]
        except Exception:
            pass

        email_sent = await email_service.send_associe_invitation(
            to_email=payload.email,
            sci_nom=sci_nom,
            inviter_nom=inviter_nom,
            role=payload.role,
            frontend_url=settings.frontend_url,
        )

    return InviteAssocieResponse(**created, email_sent=email_sent)


# ──────────────────────────────────────────────────────────────
# LIST all documents for a SCI (aggregated across all biens)
# ──────────────────────────────────────────────────────────────


class SciDocumentItem(BaseModel):
    id: str | int
    id_bien: str | int
    bien_adresse: str | None = None
    nom: str
    categorie: str = "autre"
    url: str
    uploaded_at: str | None = None

    model_config = ConfigDict(extra="ignore")


@router.get("/{sci_id}/documents", response_model=list[SciDocumentItem])
async def list_sci_documents(
    sci_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste tous les documents d'une SCI (tous les biens confondus)."""
    client = _get_client(request)

    # Get all bien IDs for this SCI
    biens_result = client.table("biens").select("id, adresse").eq("id_sci", sci_id).execute()
    if getattr(biens_result, "error", None):
        raise DatabaseError(str(biens_result.error))

    biens = biens_result.data or []
    if not biens:
        return []

    bien_ids = [str(b["id"]) for b in biens]
    bien_map = {str(b["id"]): b.get("adresse", "") for b in biens}

    # Fetch all documents for these biens in one query
    docs_result = (
        client.table("documents_bien")
        .select("*")
        .in_("id_bien", bien_ids)
        .order("uploaded_at", desc=True)
        .execute()
    )
    if getattr(docs_result, "error", None):
        raise DatabaseError(str(docs_result.error))

    docs = docs_result.data or []
    # Enrich with bien address
    for doc in docs:
        doc["bien_adresse"] = bien_map.get(str(doc.get("id_bien", "")), "")

    return docs
