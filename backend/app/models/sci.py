from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SCIBase(BaseModel):
    nom: str = Field(min_length=2, max_length=120)
    siren: str | None = Field(default=None, pattern=r"^\d{9}$")
    regime_fiscal: str = Field(default="IR", pattern=r"^(IR|IS)$")
    adresse_siege: str | None = Field(default=None, max_length=500)
    date_creation: str | None = Field(default=None)
    capital_social: float | None = Field(default=None, ge=0)
    objet_social: str | None = Field(default=None, max_length=2000)
    rcs_ville: str | None = Field(default=None, max_length=100)


class SCICreate(SCIBase):
    pass


class SCIUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=120)
    siren: str | None = Field(default=None, pattern=r"^\d{9}$")
    regime_fiscal: str | None = Field(default=None, pattern=r"^(IR|IS)$")
    adresse_siege: str | None = Field(default=None, max_length=500)
    date_creation: str | None = Field(default=None)
    capital_social: float | None = Field(default=None, ge=0)
    objet_social: str | None = Field(default=None, max_length=2000)
    rcs_ville: str | None = Field(default=None, max_length=100)


class AssocieCreate(BaseModel):
    id_sci: str
    user_id: str
    nom: str = Field(min_length=2, max_length=120)
    email: EmailStr
    part: float = Field(gt=0, le=100)
    role: str = Field(default="associe", min_length=2, max_length=30)


class SCIResponse(SCIBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
