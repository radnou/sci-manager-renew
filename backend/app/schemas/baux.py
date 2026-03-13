"""Pydantic schemas for bail (lease) CRUD operations."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class BailCreate(BaseModel):
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float = Field(ge=0)
    charges_locatives: float = Field(default=0, ge=0)
    depot_garantie: float = Field(default=0, ge=0)
    indice_irl_reference: Optional[str] = Field(default="IRL", max_length=50)
    locataire_ids: list[str] = []

    @model_validator(mode='after')
    def check_dates(self):
        if self.date_fin and self.date_debut and self.date_fin <= self.date_debut:
            raise ValueError("date_fin doit être postérieure à date_debut")
        return self


class BailUpdate(BaseModel):
    date_fin: Optional[date] = None
    loyer_hc: Optional[float] = Field(default=None, ge=0)
    charges_locatives: Optional[float] = Field(default=None, ge=0)
    depot_garantie: Optional[float] = Field(default=None, ge=0)
    statut: Optional[str] = Field(default=None, max_length=30)
    indice_irl_reference: Optional[str] = Field(default=None, max_length=50)


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
