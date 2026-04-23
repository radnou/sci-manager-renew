"""
Service de génération de la déclaration 2065 — Bilan simplifié SCI.

La déclaration 2065 est obligatoire pour les SCI soumises à l'IS
(impôt sur les sociétés) ou celles qui optent pour le régime réel d'imposition.

Champs obligatoires :
- Actif immobilisé (biens + travaux)
- Créances (loyers impayés)
- Trésorerie
- Capitaux propres (capital social + réserves)
- Résultat exercice
- Dettes (emprunts + crédits)
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

import structlog
from fastapi import HTTPException, status

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.supabase_client import get_supabase_service_client
from app.models.sci import SCIResponse

logger = structlog.get_logger(__name__)

# ──────────────────────────────────────────────────────────────
# Modèles Pydantic
# ──────────────────────────────────────────────────────────────


class BilanActif:
    """Actif du bilan (ce que possède la SCI)."""

    immobilisations_corporelles: Decimal  # Biens immobiliers
    travaux_en_cours: Optional[Decimal] = None
    créances_clients: Decimal  # Loyers impayés
    autres_créances: Optional[Decimal] = None
    trésorerie_actif: Decimal  # Compte bancaire

    @property
    def total_actif(self) -> Decimal:
        return (
            self.immobilisations_corporelles
            + (self.travaux_en_cours or Decimal("0"))
            + self.créances_clients
            + (self.autres_créances or Decimal("0"))
            + self.trésorerie_actif
        )


class BilanPassif:
    """Passif du bilan (origine des fonds)."""

    capital_social: Decimal
    réserves: Optional[Decimal] = None
    report_à_nouveau: Optional[Decimal] = None
    résultat_exercice: Decimal
    emprunts: Decimal
    dettes_fournisseurs: Optional[Decimal] = None
    autres_dettes: Optional[Decimal] = None

    @property
    def total_passif(self) -> Decimal:
        capitaux_propres = (
            self.capital_social
            + (self.réserves or Decimal("0"))
            + (self.report_à_nouveau or Decimal("0"))
            + self.résultat_exercice
        )
        dettes = (
            self.emprunts
            + (self.dettes_fournisseurs or Decimal("0"))
            + (self.autres_dettes or Decimal("0"))
        )
        return capitaux_propres + dettes


class Declaration2065:
    """Déclaration 2065 complète."""

    sci_id: UUID
    exercice: int  # Année fiscale
    date_cloture: date
    actif: BilanActif
    passif: BilanPassif
    écart: Decimal  # Doit être = 0

    def __post_init__(self):
        self.écart = self.actif.total_actif - self.passif.total_passif
        if abs(self.écart) > Decimal("0.01"):
            raise ValidationError(
                f"Bilan déséquilibré : écart de {self.écart} €. "
                "Vérifiez les montants saisis."
            )


# ──────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────


class Declaration2065Service:
    """Service de génération et validation de la déclaration 2065."""

    def __init__(self):
        self.client = get_supabase_service_client()

    async def get_bilan_data(self, sci_id: UUID, exercice: int) -> dict:
        """Récupère les données comptables pour le bilan.

        Sources :
        - Biens : table `biens` (valeur d'acquisition)
        - Loyers impayés : table `loyers` (statut = impayé)
        - Crédits : table `credits` (solde restant)
        - Résultat : table `fiscalite` (résultat fiscal)
        """
        logger.info("get_bilan_data", sci_id=str(sci_id), exercice=exercice)

        # 1. Biens immobiliers (actif)
        biens_result = (
            self.client.table("biens")
            .select("acquisition_prix, travaux_montant")
            .eq("id_sci", str(sci_id))
            .execute()
        )
        biens = biens_result.data or []
        immobilisations = sum(
            Decimal(str(b.get("acquisition_prix", 0) or 0)) for b in biens
        )
        travaux = sum(
            Decimal(str(b.get("travaux_montant", 0) or 0)) for b in biens
        )

        # 2. Loyers impayés (créances)
        loyers_result = (
            self.client.table("loyers")
            .select("montant")
            .eq("id_sci", str(sci_id))
            .eq("statut", "impayé")
            .gte("date_loyer", f"{exercice}-01-01")
            .lte("date_loyer", f"{exercice}-12-31")
            .execute()
        )
        créances = sum(
            Decimal(str(l.get("montant", 0) or 0)) for l in (loyers_result.data or [])
        )

        # 3. Crédits (dettes)
        credits_result = (
            self.client.table("credits")
            .select("montant_mensuel, duree_mois, date_debut")
            .eq("id_sci", str(sci_id))
            .execute()
        )
        # Calcul solde restant (simplifié)
        emprunts = Decimal("0")
        for cr in credits_result.data or []:
            mensualité = Decimal(str(cr.get("montant_mensuel", 0) or 0))
            durée = cr.get("duree_mois", 0) or 0
            # Approximation : 50% du capital restant (à affiner)
            emprunts += mensualité * durée * Decimal("0.5")

        # 4. Résultat fiscal
        fiscal_result = (
            self.client.table("fiscalite")
            .select("resultat_fiscal")
            .eq("id_sci", str(sci_id))
            .eq("annee", exercice)
            .execute()
        )
        fiscal_data = fiscal_result.data
        résultat = Decimal(str(fiscal_data[0]["resultat_fiscal"])) if fiscal_data else Decimal("0")

        # 5. Capital social (SCI)
        sci_result = (
            self.client.table("sci")
            .select("capital_social")
            .eq("id", str(sci_id))
            .execute()
        )
        capital = Decimal(str(sci_result.data[0].get("capital_social", 0))) if sci_result.data else Decimal("0")

        return {
            "immobilisations": immobilisations.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "travaux": travaux.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "créances": créances.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "emprunts": emprunts.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "résultat": résultat.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "capital": capital.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }

    async def generate_declaration(
        self,
        sci_id: UUID,
        exercice: int,
        trésorerie: Optional[Decimal] = None,
        réserves: Optional[Decimal] = None,
    ) -> Declaration2065:
        """Génère une déclaration 2065 pré-remplie."""
        data = await self.get_bilan_data(sci_id, exercice)

        # Récupérer la date de clôture
        sci_result = (
            self.client.table("sci")
            .select("date_cloture_exercice")
            .eq("id", str(sci_id))
            .execute()
        )
        date_cloture_str = sci_result.data[0].get("date_cloture_exercice") if sci_result.data else None
        date_cloture = (
            date.fromisoformat(date_cloture_str)
            if date_cloture_str
            else date(exercice, 12, 31)
        )

        actif = BilanActif(
            immobilisations_corporelles=data["immobilisations"],
            travaux_en_cours=data["travaux"] if data["travaux"] > 0 else None,
            créances_clients=data["créances"],
            trésorerie_actif=trésorerie or Decimal("0"),
        )

        passif = BilanPassif(
            capital_social=data["capital"],
            réserves=réserves,
            résultat_exercice=data["résultat"],
            emprunts=data["emprunts"],
        )

        declaration = Declaration2065(
            sci_id=sci_id,
            exercice=exercice,
            date_cloture=date_cloture,
            actif=actif,
            passif=passif,
        )

        logger.info(
            "declaration_2065_generated",
            sci_id=str(sci_id),
            exercice=exercice,
            total_actif=str(actif.total_actif),
        )

        return declaration

    async def save_declaration(self, declaration: Declaration2065) -> dict:
        """Sauvegarde la déclaration en base."""
        payload = {
            "id_sci": str(declaration.sci_id),
            "exercice": declaration.exercice,
            "date_cloture": declaration.date_cloture.isoformat(),
            "actif_immobilisations": float(declaration.actif.immobilisations_corporelles),
            "actif_creances": float(declaration.actif.créances_clients),
            "actif_tresorerie": float(declaration.actif.trésorerie_actif),
            "passif_capital": float(declaration.passif.capital_social),
            "passif_resultat": float(declaration.passif.résultat_exercice),
            "passif_emprunts": float(declaration.passif.emprunts),
            "ecart": float(declaration.écart),
        }

        result = self.client.table("declarations_2065").upsert(payload).execute()

        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        logger.info("declaration_2065_saved", sci_id=str(declaration.sci_id))
        return result.data[0] if result.data else payload


# ──────────────────────────────────────────────────────────────
# Fonction utilitaire
# ──────────────────────────────────────────────────────────────


async def generate_2065_pdf(declaration: Declaration2065) -> bytes:
    """Génère le PDF CERFA 2065 (placeholder — à implémenter avec ReportLab/weasyprint).

    TODO :
    1. Template PDF officiel DGFiP
    2. Mapping champs → positions PDF
    3. Génération avec pypdf ou reportlab
    """
    logger.warning("generate_2065_pdf_not_implemented")
    raise NotImplementedError(
        "Génération PDF 2065 en cours de développement. "
        "Utilisez les données JSON pour pré-remplir le formulaire DGFiP."
    )
