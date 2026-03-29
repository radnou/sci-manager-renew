"""Pydantic schemas for credits immobiliers (mortgage/loan tracking)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


TypeCredit = Literal["amortissable", "in_fine", "relais"]
StatutCredit = Literal["en_cours", "rembourse", "restructure"]


class CreditImmobilierCreate(BaseModel):
    banque: str = Field(max_length=200)
    numero_contrat: Optional[str] = Field(default=None, max_length=100)
    montant_emprunte: float = Field(gt=0)
    taux_nominal: float = Field(ge=0)
    taux_assurance: float = Field(default=0, ge=0)
    duree_mois: int = Field(gt=0)
    date_debut: date
    mensualite: float = Field(gt=0)
    capital_restant_du: Optional[float] = None
    type_credit: TypeCredit = "amortissable"
    statut: StatutCredit = "en_cours"
    notes: Optional[str] = None


class CreditImmobilierUpdate(BaseModel):
    banque: Optional[str] = Field(default=None, max_length=200)
    numero_contrat: Optional[str] = Field(default=None, max_length=100)
    montant_emprunte: Optional[float] = Field(default=None, gt=0)
    taux_nominal: Optional[float] = Field(default=None, ge=0)
    taux_assurance: Optional[float] = Field(default=None, ge=0)
    duree_mois: Optional[int] = Field(default=None, gt=0)
    date_debut: Optional[date] = None
    mensualite: Optional[float] = Field(default=None, gt=0)
    capital_restant_du: Optional[float] = None
    type_credit: Optional[TypeCredit] = None
    statut: Optional[StatutCredit] = None
    notes: Optional[str] = None


class CreditImmobilierResponse(BaseModel):
    id: str | int
    id_bien: str | int
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
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreditImmobilierEmbed(BaseModel):
    """Lightweight embed for fiche bien response."""
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


class AmortissementRow(BaseModel):
    mois: int
    date: str
    mensualite: float
    capital: float
    interets: float
    assurance: float
    capital_restant: float
