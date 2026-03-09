from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FiscaliteBase(BaseModel):
    id_sci: str
    annee: int = Field(ge=2000, le=2100)
    total_revenus: float = Field(default=0, ge=0)
    total_charges: float = Field(default=0, ge=0)


class FiscaliteCreate(FiscaliteBase):
    @property
    def resultat_fiscal(self) -> float:
        return round(self.total_revenus - self.total_charges, 2)


class FiscaliteUpdate(BaseModel):
    annee: int | None = Field(default=None, ge=2000, le=2100)
    total_revenus: float | None = Field(default=None, ge=0)
    total_charges: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_payload(self):
        if self.annee is None and self.total_revenus is None and self.total_charges is None:
            raise ValueError("At least one fiscality field must be provided")
        return self


class FiscaliteResponse(FiscaliteBase):
    id: str
    resultat_fiscal: float = 0
    regime_fiscal: str | None = None
    nom_sci: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
