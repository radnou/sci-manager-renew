from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LocataireBase(BaseModel):
    id_bien: str
    nom: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    date_debut: date
    date_fin: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("date_fin must be later than or equal to date_debut")
        return self


class LocataireCreate(LocataireBase):
    pass


class LocataireUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    date_debut: date | None = None
    date_fin: date | None = None


class LocataireResponse(LocataireBase):
    id: str
    id_sci: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
