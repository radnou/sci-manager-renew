from datetime import date
from typing import Optional

from pydantic import BaseModel


class FraisAgenceCreate(BaseModel):
    type_frais: str  # 'gestion_locative', 'mise_en_location', 'autre'
    montant: float
    date_frais: date
    description: Optional[str] = None


class FraisAgenceUpdate(BaseModel):
    type_frais: Optional[str] = None
    montant: Optional[float] = None
    date_frais: Optional[date] = None
    description: Optional[str] = None


class FraisAgenceResponse(BaseModel):
    id: int
    id_bien: int
    type_frais: str
    montant: float
    date_frais: date
    description: Optional[str] = None
