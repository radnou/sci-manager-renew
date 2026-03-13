from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BienBase(BaseModel):
    id_sci: str
    adresse: str = Field(min_length=3, max_length=255)
    ville: str = Field(min_length=1, max_length=120)
    code_postal: str = Field(pattern=r"^\d{5}$")
    type_locatif: Literal["nu", "meuble", "mixte"] = "nu"
    loyer_cc: float = Field(ge=0)
    charges: float = Field(default=0, ge=0)
    tmi: float = Field(default=0, ge=0, le=100)
    acquisition_date: date | None = None
    prix_acquisition: float | None = Field(default=None, ge=0)
    surface_m2: float | None = Field(default=None, ge=0)
    nb_pieces: int | None = Field(default=None, ge=0)
    dpe_classe: str | None = Field(default=None, max_length=1, pattern=r"^[A-G]$")
    photo_url: str | None = Field(default=None, max_length=500)


class BienCreate(BienBase):
    pass


class BienUpdate(BaseModel):
    adresse: str | None = Field(default=None, min_length=3, max_length=255)
    ville: str | None = Field(default=None, min_length=1, max_length=120)
    code_postal: str | None = Field(default=None, pattern=r"^\d{5}$")
    type_locatif: Literal["nu", "meuble", "mixte"] | None = None
    loyer_cc: float | None = Field(default=None, ge=0)
    charges: float | None = Field(default=None, ge=0)
    tmi: float | None = Field(default=None, ge=0, le=100)
    acquisition_date: date | None = None
    prix_acquisition: float | None = Field(default=None, ge=0)
    surface_m2: float | None = Field(default=None, ge=0)
    nb_pieces: int | None = Field(default=None, ge=0)
    dpe_classe: str | None = Field(default=None, max_length=1, pattern=r"^[A-G]$")
    photo_url: str | None = Field(default=None, max_length=500)


class BienResponse(BaseModel):
    """Response model — accepts any type_locatif stored in DB (legacy values like T3, studio, etc.)."""
    id: str
    id_sci: str
    adresse: str
    ville: str
    code_postal: str
    type_locatif: str = "nu"
    loyer_cc: float = 0
    charges: float = 0
    tmi: float = 0
    acquisition_date: date | None = None
    prix_acquisition: float | None = None
    surface_m2: float | None = None
    nb_pieces: int | None = None
    dpe_classe: str | None = None
    photo_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    rentabilite_brute: float = 0
    rentabilite_nette: float = 0
    cashflow_annuel: float = 0

    model_config = ConfigDict(from_attributes=True, extra="ignore")
