"""Pydantic schemas for the fiche bien (property detail card) endpoint."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class BailEmbed(BaseModel):
    id: str | int
    date_debut: date
    date_fin: Optional[date] = None
    loyer_hc: float
    charges_locatives: float = 0
    depot_garantie: float = 0
    statut: str = "en_cours"
    locataires: list[dict] = []


class AssurancePnoEmbed(BaseModel):
    id: str | int
    compagnie: str
    numero_contrat: Optional[str] = None
    montant_annuel: float = 0
    date_echeance: date


class FraisAgenceEmbed(BaseModel):
    id: str | int
    nom_agence: str
    contact: Optional[str] = None
    type_frais: str
    montant_ou_pourcentage: float


class DocumentBienEmbed(BaseModel):
    id: str | int
    nom: str
    categorie: str = "autre"
    file_url: str
    file_size: Optional[int] = None
    uploaded_at: datetime


class RentabiliteCalculee(BaseModel):
    brute: float = 0
    nette: float = 0
    cashflow_mensuel: float = 0
    cashflow_annuel: float = 0


class FicheBienResponse(BaseModel):
    id: str | int
    id_sci: str | int
    adresse: str
    ville: str
    code_postal: str
    type_locatif: str = "appartement"
    loyer_cc: float = 0
    charges: float = 0
    surface_m2: Optional[float] = None
    nb_pieces: Optional[int] = None
    dpe_classe: Optional[str] = None
    photo_url: Optional[str] = None
    prix_acquisition: Optional[float] = None
    bail_actif: Optional[BailEmbed] = None
    loyers_recents: list[dict] = []
    charges_list: list[dict] = []
    assurance_pno: Optional[AssurancePnoEmbed] = None
    frais_agence: list[FraisAgenceEmbed] = []
    documents: list[DocumentBienEmbed] = []
    rentabilite: RentabiliteCalculee = RentabiliteCalculee()
