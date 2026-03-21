from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EVENEMENT_TYPES = Literal[
    "reparation", "travaux", "sinistre", "visite",
    "controle", "diagnostic", "autre",
]


class EvenementCreate(BaseModel):
    type: EVENEMENT_TYPES
    titre: str = Field(min_length=1, max_length=200)
    description: str | None = None
    date_evenement: date
    montant: float | None = Field(default=None, ge=0)
    prestataire: str | None = Field(default=None, max_length=200)
    deductible_fiscalement: bool = False


class EvenementUpdate(BaseModel):
    type: EVENEMENT_TYPES | None = None
    titre: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    date_evenement: date | None = None
    montant: float | None = Field(default=None, ge=0)
    prestataire: str | None = Field(default=None, max_length=200)
    deductible_fiscalement: bool | None = None


class EvenementResponse(BaseModel):
    id: str
    id_bien: str
    type: str
    titre: str
    description: str | None = None
    date_evenement: date
    montant: float | None = None
    prestataire: str | None = None
    deductible_fiscalement: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
