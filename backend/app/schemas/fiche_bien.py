"""Pydantic schemas for the fiche bien (property detail card) endpoint."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class BailEmbed(BaseModel):
    id: int
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float
    charges_provisions: float = 0
    depot_garantie: float = 0
    statut: str = "en_cours"
    locataires: list[dict] = []


class AssurancePnoEmbed(BaseModel):
    id: int
    assureur: str
    numero_contrat: Optional[str] = None
    prime_annuelle: float = 0
    date_debut: date
    date_fin: Optional[date] = None


class FraisAgenceEmbed(BaseModel):
    id: int
    type_frais: str
    montant: float
    date_frais: date
    description: Optional[str] = None


class DocumentBienEmbed(BaseModel):
    id: int
    nom: str
    categorie: str = "autre"
    url: str
    created_at: datetime


class RentabiliteCalculee(BaseModel):
    brute: float = 0
    nette: float = 0
    cashflow_mensuel: float = 0
    cashflow_annuel: float = 0


class FicheBienResponse(BaseModel):
    id: int
    id_sci: int
    adresse: str
    ville: str
    code_postal: str
    type_bien: str = "appartement"
    loyer: float = 0
    charges: float = 0
    surface_m2: Optional[float] = None
    nb_pieces: Optional[int] = None
    dpe_classe: Optional[str] = None
    photo_url: Optional[str] = None
    prix_acquisition: Optional[float] = None
    statut: Optional[str] = None
    bail_actif: Optional[BailEmbed] = None
    loyers_recents: list[dict] = []
    charges_list: list[dict] = []
    assurance_pno: Optional[AssurancePnoEmbed] = None
    frais_agence: list[FraisAgenceEmbed] = []
    documents: list[DocumentBienEmbed] = []
    rentabilite: RentabiliteCalculee = RentabiliteCalculee()
