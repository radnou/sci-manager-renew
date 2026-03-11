"""Pydantic schemas for bail (lease) CRUD operations."""

from datetime import date
from typing import Optional

from pydantic import BaseModel


class BailCreate(BaseModel):
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float
    charges_provisions: float = 0
    depot_garantie: float = 0
    revision_indice: Optional[str] = "IRL"
    locataire_ids: list[int] = []  # For colocation


class BailUpdate(BaseModel):
    date_fin: Optional[date] = None
    loyer_hc: Optional[float] = None
    charges_provisions: Optional[float] = None
    depot_garantie: Optional[float] = None
    statut: Optional[str] = None
    revision_indice: Optional[str] = None


class BailResponse(BaseModel):
    id: int
    id_bien: int
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float
    charges_provisions: float = 0
    depot_garantie: float = 0
    revision_indice: Optional[str] = None
    statut: str = "en_cours"
    locataires: list[dict] = []
