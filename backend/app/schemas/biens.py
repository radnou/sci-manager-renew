from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class BienBase(BaseModel):
    id_sci: Optional[UUID] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    type_locatif: Optional[str] = None
    loyer_cc: Optional[float] = None
    charges: Optional[float] = None
    tmi: Optional[float] = None
    occupation_rate: Optional[float] = 0.0


class BienCreate(BaseModel):
    id_sci: UUID
    adresse: str
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    type_locatif: Optional[str] = None
    loyer_cc: Optional[float] = None
    charges: Optional[float] = None
    tmi: Optional[float] = None
    occupation_rate: Optional[float] = 0.0


class Bien(BienBase):
    id: UUID

    class Config:
        orm_mode = True
