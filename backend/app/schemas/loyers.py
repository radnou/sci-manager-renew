from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date


class LoyerBase(BaseModel):
    id_bien: Optional[UUID]
    date_loyer: Optional[date]
    montant: Optional[float]
    quitus_genere: Optional[bool] = False


class LoyerCreate(LoyerBase):
    id_bien: UUID
    date_loyer: date
    montant: float


class Loyer(LoyerBase):
    id: UUID

    class Config:
        orm_mode = True
