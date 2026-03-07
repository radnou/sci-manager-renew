from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ChargeBase(BaseModel):
    id_bien: str
    type_charge: str = Field(min_length=2, max_length=80)
    montant: float = Field(gt=0)
    date_paiement: date


class ChargeCreate(ChargeBase):
    pass


class ChargeUpdate(BaseModel):
    type_charge: str | None = Field(default=None, min_length=2, max_length=80)
    montant: float | None = Field(default=None, gt=0)
    date_paiement: date | None = None


class ChargeResponse(ChargeBase):
    id: str
    id_sci: str | None = None
    bien_adresse: str | None = None
    bien_ville: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
