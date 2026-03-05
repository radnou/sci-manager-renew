from pydantic import BaseModel, Field


class QuitusRequest(BaseModel):
    id_loyer: str
    id_bien: str
    nom_locataire: str = Field(min_length=2, max_length=120)
    periode: str = Field(min_length=5, max_length=30)
    montant: float = Field(gt=0)
    nom_sci: str | None = Field(default=None, min_length=2, max_length=120)
    adresse_bien: str | None = Field(default=None, min_length=4, max_length=160)
    ville_bien: str | None = Field(default=None, min_length=2, max_length=80)


class QuitusResponse(BaseModel):
    filename: str
    pdf_url: str
    size_bytes: int = Field(ge=1)
