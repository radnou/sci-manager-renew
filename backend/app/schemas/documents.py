from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentBienCreate(BaseModel):
    nom: str
    categorie: str = "autre"  # 'bail', 'quittance', 'diagnostic', 'assurance', 'autre'


class DocumentBienResponse(BaseModel):
    id: str | int
    id_bien: str | int
    nom: str
    categorie: str
    url: str
    created_at: datetime
