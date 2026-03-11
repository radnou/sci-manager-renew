from datetime import date
from typing import Optional

from pydantic import BaseModel


class AssurancePnoCreate(BaseModel):
    assureur: str
    numero_contrat: Optional[str] = None
    prime_annuelle: float = 0
    date_debut: date
    date_fin: Optional[date] = None


class AssurancePnoUpdate(BaseModel):
    assureur: Optional[str] = None
    numero_contrat: Optional[str] = None
    prime_annuelle: Optional[float] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None


class AssurancePnoResponse(BaseModel):
    id: int
    id_bien: int
    assureur: str
    numero_contrat: Optional[str] = None
    prime_annuelle: float = 0
    date_debut: date
    date_fin: Optional[date] = None
