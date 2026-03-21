from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LoyerStatus = Literal["en_attente", "paye", "en_retard"]


class LoyerBase(BaseModel):
    date_loyer: date
    montant: float = Field(gt=0)
    statut: LoyerStatus = "en_attente"
    quitus_genere: bool = False
    date_paiement: date | None = None
    mode_paiement: str | None = None


class LoyerCreate(LoyerBase):
    """Create payload — id_bien is optional because the nested endpoint provides it from the URL."""
    id_bien: str | None = None
    id_locataire: str | None = None


class LoyerUpdate(BaseModel):
    date_loyer: date | None = None
    montant: float | None = Field(default=None, gt=0)
    statut: LoyerStatus | None = None
    quitus_genere: bool | None = None
    date_paiement: date | None = None
    mode_paiement: str | None = None


class LoyerResponse(LoyerBase):
    id: str
    id_bien: str
    id_locataire: str | None = None
    id_sci: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
