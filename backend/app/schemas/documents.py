from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentBienCreate(BaseModel):
    nom: str = Field(max_length=200)
    categorie: str = Field(default="autre", max_length=50)  # 'bail', 'quittance', 'diagnostic', 'assurance', 'autre'


class DocumentBienResponse(BaseModel):
    id: str | int
    id_bien: str | int
    nom: str
    categorie: str
    url: str
    uploaded_at: datetime
