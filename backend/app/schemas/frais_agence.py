from typing import Literal, Optional

from pydantic import BaseModel, Field


class FraisAgenceCreate(BaseModel):
    nom_agence: str = Field(max_length=200)
    contact: Optional[str] = Field(default=None, max_length=200)
    type_frais: Literal["pourcentage", "fixe"]
    montant_ou_pourcentage: float = Field(ge=0)


class FraisAgenceUpdate(BaseModel):
    nom_agence: Optional[str] = Field(default=None, max_length=200)
    contact: Optional[str] = Field(default=None, max_length=200)
    type_frais: Optional[str] = Field(default=None, max_length=20)
    montant_ou_pourcentage: Optional[float] = Field(default=None, ge=0)


class FraisAgenceResponse(BaseModel):
    id: str | int
    id_bien: str | int
    nom_agence: str
    contact: Optional[str] = None
    type_frais: str
    montant_ou_pourcentage: float
