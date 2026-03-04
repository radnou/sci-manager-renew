from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LoyerStatus = Literal["en_attente", "paye", "en_retard"]


class LoyerBase(BaseModel):
    id_bien: str
    id_locataire: str | None = None
    date_loyer: date
    montant: float = Field(gt=0)
    statut: LoyerStatus = "en_attente"
    quitus_genere: bool = False


class LoyerCreate(LoyerBase):
    pass


class LoyerUpdate(BaseModel):
    date_loyer: date | None = None
    montant: float | None = Field(default=None, gt=0)
    statut: LoyerStatus | None = None
    quitus_genere: bool | None = None


class LoyerResponse(LoyerBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
