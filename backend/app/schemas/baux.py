"""Pydantic schemas for bail (lease) CRUD operations."""

from datetime import date
from typing import Optional

from pydantic import BaseModel


class BailCreate(BaseModel):
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float
    charges_locatives: float = 0
    depot_garantie: float = 0
    indice_irl_reference: Optional[str] = "IRL"
    locataire_ids: list[int] = []  # For colocation


class BailUpdate(BaseModel):
    date_fin: Optional[date] = None
    loyer_hc: Optional[float] = None
    charges_locatives: Optional[float] = None
    depot_garantie: Optional[float] = None
    statut: Optional[str] = None
    indice_irl_reference: Optional[str] = None


class BailResponse(BaseModel):
    id: str | int
    id_bien: str | int
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float
    charges_locatives: float = 0
    depot_garantie: float = 0
    indice_irl_reference: Optional[str] = None
    statut: str = "en_cours"
    locataires: list[dict] = []
