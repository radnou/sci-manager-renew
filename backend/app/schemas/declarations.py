"""
Schémas Pydantic pour les déclarations fiscales (2065, 2072).
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ──────────────────────────────────────────────────────────────
# 2065
# ──────────────────────────────────────────────────────────────


class BilanActifSchema(BaseModel):
    """Actif du bilan (ce que possède la SCI)."""
    model_config = ConfigDict(from_attributes=True)
    
    immobilisations_corporelles: float = Field(..., description="Valeur des biens immobiliers")
    travaux_en_cours: Optional[float] = Field(None, description="Travaux en cours")
    creances_clients: float = Field(..., description="Loyers impayés")
    autres_creances: Optional[float] = Field(None, description="Autres créances")
    tresorerie_actif: float = Field(..., description="Trésorerie")
    
    @property
    def total(self) -> float:
        return (
            self.immobilisations_corporelles
            + (self.travaux_en_cours or 0)
            + self.creances_clients
            + (self.autres_creances or 0)
            + self.tresorerie_actif
        )


class BilanPassifSchema(BaseModel):
    """Passif du bilan (origine des fonds)."""
    model_config = ConfigDict(from_attributes=True)
    
    capital_social: float = Field(..., description="Capital social")
    reserves: Optional[float] = Field(None, description="Réserves")
    report_a_nouveau: Optional[float] = Field(None, description="Report à nouveau")
    resultat_exercice: float = Field(..., description="Résultat de l'exercice")
    emprunts: float = Field(..., description="Emprunts restants")
    dettes_fournisseurs: Optional[float] = Field(None, description="Dettes fournisseurs")
    autres_dettes: Optional[float] = Field(None, description="Autres dettes")
    
    @property
    def total(self) -> float:
        capitaux = (
            self.capital_social
            + (self.reserves or 0)
            + (self.report_a_nouveau or 0)
            + self.resultat_exercice
        )
        dettes = (
            self.emprunts
            + (self.dettes_fournisseurs or 0)
            + (self.autres_dettes or 0)
        )
        return capitaux + dettes


class Declaration2065Schema(BaseModel):
    """Déclaration 2065 complète."""
    model_config = ConfigDict(from_attributes=True)
    
    sci_id: str = Field(..., description="UUID de la SCI")
    exercice: int = Field(..., ge=2000, le=2100)
    date_cloture: date = Field(..., description="Date de clôture de l'exercice")
    actif: BilanActifSchema
    passif: BilanPassifSchema
    ecart: float = Field(0.0, description="Écart actif - passif (doit être ≈ 0)")


class Declaration2065Create(BaseModel):
    """Payload de création d'une déclaration 2065."""
    exercice: int = Field(..., ge=2000, le=2100)
    tresorerie: Optional[float] = Field(None, description="Montant de trésorerie (si non auto)")
    reserves: Optional[float] = Field(None, description="Montant des réserves (si non auto)")


class Declaration2065Response(BaseModel):
    """Réponse API pour une déclaration 2065."""
    model_config = ConfigDict(from_attributes=True)
    
    sci_id: str
    exercice: int
    date_cloture: str
    actif: dict
    passif: dict
    ecart: float
    message: str = "Bilan équilibré"


# ──────────────────────────────────────────────────────────────
# 2072 (placeholder)
# ──────────────────────────────────────────────────────────────


class Declaration2072Schema(BaseModel):
    """Déclaration 2072 (IR — revenus fonciers)."""
    model_config = ConfigDict(from_attributes=True)
    
    sci_id: str
    exercice: int
    revenus_fonciers: float
    charges_deductibles: float
    interets_emprunt: float
    resultat_fiscal: float


class Declaration2072Create(BaseModel):
    """Payload de création d'une déclaration 2072."""
    exercice: int = Field(..., ge=2000, le=2100)
