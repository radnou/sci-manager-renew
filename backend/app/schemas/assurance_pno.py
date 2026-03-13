from datetime import date
from typing import Optional

from pydantic import BaseModel


class AssurancePnoCreate(BaseModel):
    compagnie: str
    numero_contrat: Optional[str] = None
    montant_annuel: float = 0
    date_echeance: date


class AssurancePnoUpdate(BaseModel):
    compagnie: Optional[str] = None
    numero_contrat: Optional[str] = None
    montant_annuel: Optional[float] = None
    date_echeance: Optional[date] = None


class AssurancePnoResponse(BaseModel):
    id: str | int
    id_bien: str | int
    compagnie: str
    numero_contrat: Optional[str] = None
    montant_annuel: float = 0
    date_echeance: date
