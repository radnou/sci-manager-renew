from typing import Optional

from pydantic import BaseModel


class FraisAgenceCreate(BaseModel):
    nom_agence: str
    contact: Optional[str] = None
    type_frais: str  # 'pourcentage' or 'fixe'
    montant_ou_pourcentage: float


class FraisAgenceUpdate(BaseModel):
    nom_agence: Optional[str] = None
    contact: Optional[str] = None
    type_frais: Optional[str] = None
    montant_ou_pourcentage: Optional[float] = None


class FraisAgenceResponse(BaseModel):
    id: str | int
    id_bien: str | int
    nom_agence: str
    contact: Optional[str] = None
    type_frais: str
    montant_ou_pourcentage: float
