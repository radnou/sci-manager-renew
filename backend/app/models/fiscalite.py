from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FiscaliteBase(BaseModel):
    id_sci: str
    annee: int = Field(ge=2000, le=2100)
    total_revenus: float = Field(default=0, ge=0)
    total_charges: float = Field(default=0, ge=0)
    # Charge decomposition (optional)
    interets_emprunt: float | None = Field(default=None, ge=0)
    travaux: float | None = Field(default=None, ge=0)
    frais_gestion: float | None = Field(default=None, ge=0)
    assurance: float | None = Field(default=None, ge=0)
    taxe_fonciere: float | None = Field(default=None, ge=0)
    copropriete: float | None = Field(default=None, ge=0)


class FiscaliteCreate(FiscaliteBase):
    @property
    def resultat_fiscal(self) -> float:
        return round(self.total_revenus - self.total_charges, 2)


class FiscaliteUpdate(BaseModel):
    annee: int | None = Field(default=None, ge=2000, le=2100)
    total_revenus: float | None = Field(default=None, ge=0)
    total_charges: float | None = Field(default=None, ge=0)
    interets_emprunt: float | None = Field(default=None, ge=0)
    travaux: float | None = Field(default=None, ge=0)
    frais_gestion: float | None = Field(default=None, ge=0)
    assurance: float | None = Field(default=None, ge=0)
    taxe_fonciere: float | None = Field(default=None, ge=0)
    copropriete: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_payload(self):
        fields = [
            self.annee, self.total_revenus, self.total_charges,
            self.interets_emprunt, self.travaux, self.frais_gestion,
            self.assurance, self.taxe_fonciere, self.copropriete,
        ]
        if all(f is None for f in fields):
            raise ValueError("At least one fiscality field must be provided")
        return self


class FiscaliteResponse(FiscaliteBase):
    id: str
    resultat_fiscal: float = 0
    regime_fiscal: str | None = None
    nom_sci: str | None = None
    disclaimer: str = "Résumé fiscal simplifié — consultez votre comptable pour la déclaration définitive"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
