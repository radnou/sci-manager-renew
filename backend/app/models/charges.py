from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Categories de charges deductibles conformes a l'Article 31 CGI
CHARGE_TYPES = Literal[
    "copropriete",           # Charges de copropriete deductibles
    "taxe_fonciere",         # Taxe fonciere
    "assurance_pno",         # Assurance proprietaire non-occupant
    "frais_gestion",         # Frais de gestion (agence ou forfait 20 EUR/local)
    "interets_emprunt",      # Interets d'emprunt immobilier
    "travaux_entretien",     # Travaux d'entretien et reparation
    "travaux_amelioration",  # Travaux d'amelioration
    "prime_assurance",       # Primes d'assurance (autre que PNO)
    "frais_procedure",       # Frais de procedure (contentieux locataire)
    "indemnite_eviction",    # Indemnite d'eviction / frais de relogement
    "autre_deductible",      # Autre charge deductible (a preciser)
]


class ChargeBase(BaseModel):
    id_bien: str
    type_charge: CHARGE_TYPES
    montant: float = Field(gt=0)
    date_paiement: date


class ChargeCreate(ChargeBase):
    pass


class ChargeUpdate(BaseModel):
    type_charge: CHARGE_TYPES | None = None
    montant: float | None = Field(default=None, gt=0)
    date_paiement: date | None = None


class ChargeResponse(ChargeBase):
    id: str
    id_sci: str | None = None
    bien_adresse: str | None = None
    bien_ville: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
