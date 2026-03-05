from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.security import get_current_user
from app.models.biens import BienResponse
from app.models.loyers import LoyerResponse

router = APIRouter(prefix="/scis", tags=["scis"])


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


def _get_client():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


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
async def list_scis(user_id: str = Depends(get_current_user)):
    client = _get_client()

    memberships = _execute_select(client.table("associes").select("*").eq("user_id", user_id))
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
async def get_sci_detail(sci_id: str, user_id: str = Depends(get_current_user)):
    client = _get_client()

    memberships = _execute_select(client.table("associes").select("*").eq("user_id", user_id))
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
