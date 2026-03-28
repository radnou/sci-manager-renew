from pydantic import BaseModel, Field


class QuitusRequest(BaseModel):
    id_loyer: str
    id_bien: str
    nom_locataire: str = Field(min_length=2, max_length=120)
    periode: str = Field(min_length=5, max_length=30)
    montant: float = Field(gt=0)
    loyer_hc: float = Field(default=0, ge=0)
    charges_locatives: float = Field(default=0, ge=0)
    nom_sci: str | None = Field(default=None, min_length=2, max_length=120)
    adresse_bien: str | None = Field(default=None, min_length=4, max_length=160)
    ville_bien: str | None = Field(default=None, min_length=2, max_length=80)


class PublicQuitusRequest(BaseModel):
    nom_proprietaire: str = Field(min_length=2, max_length=120)
    adresse_bien: str = Field(min_length=4, max_length=200)
    nom_locataire: str = Field(min_length=2, max_length=120)
    periode: str = Field(min_length=5, max_length=30)
    loyer_hc: float = Field(gt=0)
    charges_locatives: float = Field(default=0, ge=0)
    montant_paye: float = Field(gt=0)
    date_paiement: str = Field(min_length=10, max_length=10)
    mode_paiement: str = Field(default="virement", max_length=30)


class QuitusResponse(BaseModel):
    filename: str
    pdf_url: str
    size_bytes: int = Field(ge=1)
