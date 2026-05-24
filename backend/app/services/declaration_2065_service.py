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

from dataclasses import dataclass

import structlog
from fastapi import HTTPException, status

from app.core.exceptions import DatabaseError, ResourceNotFoundError, ValidationError
from app.core.supabase_client import get_supabase_service_client
from app.models.sci import SCIResponse

logger = structlog.get_logger(__name__)

# ──────────────────────────────────────────────────────────────
# Modèles Pydantic
# ──────────────────────────────────────────────────────────────


@dataclass
class BilanActif:
    """Actif du bilan (ce que possède la SCI)."""

    immobilisations_corporelles: Decimal  # Biens immobiliers
    travaux_en_cours: Optional[Decimal] = None
    créances_clients: Decimal = Decimal("0")  # Loyers impayés
    autres_créances: Optional[Decimal] = None
    trésorerie_actif: Decimal = Decimal("0")  # Compte bancaire

    @property
    def total_actif(self) -> Decimal:
        return (
            self.immobilisations_corporelles
            + (self.travaux_en_cours or Decimal("0"))
            + self.créances_clients
            + (self.autres_créances or Decimal("0"))
            + self.trésorerie_actif
        )


@dataclass
class BilanPassif:
    """Passif du bilan (origine des fonds)."""

    capital_social: Decimal = Decimal("0")
    réserves: Optional[Decimal] = None
    report_à_nouveau: Optional[Decimal] = None
    résultat_exercice: Decimal = Decimal("0")
    emprunts: Decimal = Decimal("0")
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


@dataclass
class Declaration2065:
    """Déclaration 2065 complète."""

    sci_id: UUID
    exercice: int  # Année fiscale
    date_cloture: date
    actif: BilanActif
    passif: BilanPassif
    écart: Decimal = Decimal("0")  # Doit être = 0

    def __post_init__(self):
        self.écart = self.actif.total_actif - self.passif.total_passif
        if abs(self.écart) > Decimal("0.01"):
            # MVP : logger un warning au lieu de bloquer
            # Le gestionnaire débutant n'a pas encore toutes les données
            import warnings
            warnings.warn(
                f"Bilan déséquilibré : écart de {self.écart} €. "
                "Le gestionnaire devra compléter les données.",
                stacklevel=2,
            )


# ──────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────


class Declaration2065Service:
    """Service de génération et validation de la déclaration 2065."""

    def __init__(self, client=None):
        self.client = client or get_supabase_service_client()

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
            .select("prix_acquisition, frais_notaire, frais_agence_acquisition")
            .eq("id_sci", str(sci_id))
            .execute()
        )
        biens = biens_result.data or []
        immobilisations = Decimal("0")
        if biens:
            immobilisations = sum(
                Decimal(str(b.get("prix_acquisition", 0) or 0)) for b in biens
            )
        travaux = Decimal("0")
        if biens:
            travaux = sum(
                Decimal(str(b.get("frais_notaire", 0) or 0)) +
                Decimal(str(b.get("frais_agence_acquisition", 0) or 0))
                for b in biens
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
        if not isinstance(créances, Decimal):
            créances = Decimal(str(créances))

        # 3. Crédits immobiliers (dettes) — calcul exact du capital restant dû
        # Récupérer d'abord les IDs des biens de cette SCI
        biens_ids_result = (
            self.client.table("biens")
            .select("id")
            .eq("id_sci", str(sci_id))
            .execute()
        )
        biens_ids = [b["id"] for b in (biens_ids_result.data or [])]
        
        emprunts = Decimal("0")
        credits_data = []
        if biens_ids:
            credits_result = (
                self.client.table("credits_immobiliers")
                .select("montant_emprunte, taux_nominal, duree_mois, date_debut, mensualite, capital_restant_du")
                .in_("id_bien", biens_ids)
                .execute()
            )
            credits_data = credits_result.data or []
        for cr in credits_data:
            # Si capital_restant_du est déjà calculé, l'utiliser
            crd = cr.get("capital_restant_du")
            if crd is not None:
                emprunts += Decimal(str(crd))
                continue

            # Sinon, calculer via amortissement linéaire
            capital = Decimal(str(cr.get("montant_emprunte", 0) or 0))
            taux_annuel = Decimal(str(cr.get("taux_nominal", 0) or 0))
            duree = int(cr.get("duree_mois", 0) or 0)
            date_debut = cr.get("date_debut")
            
            if capital <= 0 or duree <= 0 or not date_debut:
                continue
            
            # Taux mensuel
            t = taux_annuel / Decimal("12")
            
            # Nombre de mensualités déjà payées depuis le début
            from datetime import date
            date_debut = date.fromisoformat(str(date_debut))
            today = date.today()
            mois_ecoules = (today.year - date_debut.year) * 12 + (today.month - date_debut.month)
            
            if mois_ecoules <= 0:
                # Le crédit n'a pas encore commencé ou vient de commencer
                emprunts += capital
                continue
            
            if mois_ecoules >= duree:
                # Crédit remboursé (ou presque)
                continue
            
            if t == 0:
                # Crédit à taux 0 : amortissement linéaire simple
                crd = capital - (capital / duree * mois_ecoules)
            else:
                # Formule du capital restant dû
                # CRD(k) = C × ((1+t)^n - (1+t)^k) / ((1+t)^n - 1)
                try:
                    t_dec = t.quantize(Decimal("0.00000001"))
                    n = Decimal(str(duree))
                    k = Decimal(str(mois_ecoules))
                    
                    un_plus_t_n = (Decimal("1") + t_dec) ** n
                    un_plus_t_k = (Decimal("1") + t_dec) ** k
                    
                    crd = capital * (un_plus_t_n - un_plus_t_k) / (un_plus_t_n - Decimal("1"))
                except (ValueError, OverflowError):
                    # Fallback sur l'amortissement linéaire simple
                    crd = capital - (capital / duree * mois_ecoules)
            
            emprunts += crd
            
            # Mettre à jour le capital_restant_du en base (cache)
            try:
                self.client.table("credits_immobiliers").update({
                    "capital_restant_du": float(crd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                }).eq("id", cr["id"]).execute()
            except Exception:
                pass  # Ne pas bloquer si la mise à jour échoue

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
        sci_check = self.client.table("sci").select("id").eq("id", str(sci_id)).execute()
        if getattr(sci_check, "error", None):
            raise DatabaseError(str(sci_check.error))
        if not sci_check.data:
            raise ResourceNotFoundError("SCI", str(sci_id))

        if trésorerie is not None:
            trésorerie = Decimal(str(trésorerie))
        if réserves is not None:
            réserves = Decimal(str(réserves))

        data = await self.get_bilan_data(sci_id, exercice)

        # Récupérer la date de clôture (colonne optionnelle)
        date_cloture = date(exercice, 12, 31)
        try:
            sci_result = (
                self.client.table("sci")
                .select("date_cloture_exercice")
                .eq("id", str(sci_id))
                .execute()
            )
            date_cloture_str = sci_result.data[0].get("date_cloture_exercice") if sci_result.data else None
            if date_cloture_str:
                date_cloture = date.fromisoformat(date_cloture_str)
        except Exception:
            # Colonne inexistante → utiliser 31/12 de l'exercice
            pass

        actif = BilanActif(
            immobilisations_corporelles=data["immobilisations"],
            travaux_en_cours=data["travaux"] if data["travaux"] > 0 else None,
            créances_clients=data["créances"],
            trésorerie_actif=Decimal(str(trésorerie)) if trésorerie is not None else Decimal("0"),
        )

        passif = BilanPassif(
            capital_social=data["capital"],
            réserves=Decimal(str(réserves)) if réserves is not None else None,
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

        try:
            result = self.client.table("declarations_2065").upsert(payload).execute()

            if getattr(result, "error", None):
                raise DatabaseError(str(result.error))

            logger.info("declaration_2065_saved", sci_id=str(declaration.sci_id))
            return result.data[0] if result.data else payload
        except Exception as e:
            # Si la table n'existe pas encore (PGRST205), retourner le payload sans sauvegarder
            if "declarations_2065" in str(e) or "PGRST205" in str(e):
                logger.warning("declarations_2065_table_missing", sci_id=str(declaration.sci_id))
                return payload
            raise


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
