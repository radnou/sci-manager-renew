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
    url: str
    file_size: Optional[int] = None
    uploaded_at: datetime


class RentabiliteCalculee(BaseModel):
    brute: float = 0
    nette: float = 0
    cashflow_mensuel: float = 0
    cashflow_annuel: float = 0
    cashflow_apres_credit_mensuel: float = 0
    cashflow_apres_credit_annuel: float = 0


class CreditImmobilierEmbed(BaseModel):
    id: str | int
    banque: str
    numero_contrat: Optional[str] = None
    montant_emprunte: float
    taux_nominal: float
    taux_assurance: float = 0
    duree_mois: int
    date_debut: date
    mensualite: float
    capital_restant_du: Optional[float] = None
    type_credit: str = "amortissable"
    statut: str = "en_cours"


class FicheBienResponse(BaseModel):
    id: str | int
    id_sci: str | int
    adresse: str
    ville: str
    code_postal: str
    type_locatif: str = "appartement"
    type_bien: Optional[str] = None
    loyer_cc: float = 0
    charges: float = 0
    surface_m2: Optional[float] = None
    nb_pieces: Optional[int] = None
    dpe_classe: Optional[str] = None
    photo_url: Optional[str] = None
    prix_acquisition: Optional[float] = None
    statut: Optional[str] = None
    zone_tendue: bool = False
    bail_actif: Optional[BailEmbed] = None
    loyers_recents: list[dict] = []
    charges_list: list[dict] = []
    assurance_pno: Optional[AssurancePnoEmbed] = None
    frais_agence: list[FraisAgenceEmbed] = []
    credits_immobiliers: list[CreditImmobilierEmbed] = []
    documents: list[DocumentBienEmbed] = []
    rentabilite: RentabiliteCalculee = RentabiliteCalculee()
