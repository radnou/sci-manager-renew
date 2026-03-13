from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AssurancePnoCreate(BaseModel):
    compagnie: str = Field(max_length=200)
    numero_contrat: Optional[str] = Field(default=None, max_length=100)
    montant_annuel: float = Field(default=0, ge=0)
    date_echeance: date


class AssurancePnoUpdate(BaseModel):
    compagnie: Optional[str] = Field(default=None, max_length=200)
    numero_contrat: Optional[str] = Field(default=None, max_length=100)
    montant_annuel: Optional[float] = Field(default=None, ge=0)
    date_echeance: Optional[date] = None


class AssurancePnoResponse(BaseModel):
    id: str | int
    id_bien: str | int
    compagnie: str
    numero_contrat: Optional[str] = None
    montant_annuel: float = 0
    date_echeance: date
