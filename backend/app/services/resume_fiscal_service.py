"""Service de calcul du résumé fiscal — IR régime réel, ventilation par bien, lignes CERFA 2044."""

from __future__ import annotations

import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)


@dataclass
class BienFiscalDetail:
    """Détail fiscal d'un bien avec correspondance lignes CERFA 2044."""

    bien_id: str
    adresse: str
    ville: str
    ligne_211_loyers_bruts: float = 0.0
    ligne_215_frais_gestion: float = 20.0  # forfait 20 € par bien
    ligne_220_assurance: float = 0.0
    ligne_221_travaux: float = 0.0
    ligne_224_taxe_fonciere: float = 0.0
    ligne_227_copropriete: float = 0.0
    ligne_229_total_charges: float = 0.0
    ligne_230_interets_emprunt: float = 0.0
    ligne_240_resultat_net: float = 0.0


@dataclass
class AssocieQuotePart:
    """Quote-part du résultat fiscal attribuée à un associé."""

    associe_id: str = ""
    nom: str = ""
    email: str = ""
    part_pct: float = 0.0
    quote_part_resultat: float = 0.0
    case_4ba: float = 0.0  # Bénéfice foncier
    case_4bb: float = 0.0  # Déficit imputable revenu global
    case_4bc: float = 0.0  # Déficit reportable revenus fonciers
    case_4bd: float = 0.0  # Déficits antérieurs


@dataclass
class DeficitAnterieur:
    """Déficit antérieur reportable pour le suivi sur 10 ans."""

    annee: int
    montant_initial: float
    total_impute: float
    solde_restant: float
    annee_prescription: int


@dataclass
class ResumeFiscalResult:
    """Résultat complet du résumé fiscal pour une SCI sur un exercice."""

    sci_nom: str
    sci_siren: str
    regime_fiscal: str
    annee: int
    biens: list[BienFiscalDetail] = field(default_factory=list)
    total_revenus: float = 0.0
    total_charges: float = 0.0
    total_interets: float = 0.0
    resultat_global: float = 0.0
    associes: list[AssocieQuotePart] = field(default_factory=list)
    alertes: list[str] = field(default_factory=list)

    # SCI identification fields (for CERFA-style PDF)
    sci_adresse_siege: str = ""
    sci_capital_social: float = 0.0
    sci_nom_gerant: str = ""
    nb_biens: int = 0
    nb_associes: int = 0

    # Phase 2: Micro-foncier comparison (art. 32 CGI)
    micro_foncier_eligible: bool = False
    micro_foncier_abattement: float = 0.0
    micro_foncier_resultat: float = 0.0
    regime_recommande: str = "reel"
    economie_regime_recommande: float = 0.0

    # Phase 2: Déficit foncier (art. 156-I-3° CGI)
    is_deficit: bool = False
    deficit_total: float = 0.0
    deficit_interets_emprunt: float = 0.0
    deficit_imputable_revenu_global: float = 0.0
    deficit_reportable_foncier: float = 0.0

    # Phase 3: Déficits antérieurs tracker
    deficits_anterieurs: list[DeficitAnterieur] = field(default_factory=list)
    total_deficits_anterieurs_imputes: float = 0.0


class ResumeFiscalService:
    """Calcule le résumé fiscal d'une SCI pour une année donnée (IR régime réel)."""

    @staticmethod
    def _safe_float(value) -> float:
        """Convert a value to float safely, treating None as 0."""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _execute_select(query) -> list[dict]:
        result = query.execute()
        if getattr(result, "error", None):
            return []
        return result.data or []

    def _load_prior_deficits(self, sci_id: str, annee: int, client) -> list[dict]:
        """Load prior year deficits that are still reportable (not prescribed, with remaining balance)."""
        try:
            rows = self._execute_select(
                client.table("deficit_reportable")
                .select("*")
                .eq("id_sci", sci_id)
                .gt("solde_restant", 0)
                .gt("annee_prescription", annee)
                .order("annee_constatation")
            )
            return rows
        except Exception:
            logger.warning("deficit_reportable_load_failed", sci_id=sci_id, annee=annee)
            return []

    def _save_deficit(self, sci_id: str, annee: int, result: ResumeFiscalResult, client) -> None:
        """Save current year deficit to deficit_reportable table (upsert)."""
        if not result.is_deficit:
            return
        try:
            total_reportable = result.deficit_interets_emprunt + result.deficit_reportable_foncier
            if total_reportable <= 0:
                return

            row = {
                "id_sci": sci_id,
                "annee_constatation": annee,
                "deficit_interets": result.deficit_interets_emprunt,
                "deficit_charges": result.deficit_reportable_foncier,
                "impute_revenu_global": result.deficit_imputable_revenu_global,
                "total_impute_foncier": 0,
                "solde_restant": total_reportable,
                "annee_prescription": annee + 10,
            }
            client.table("deficit_reportable").upsert(
                row, on_conflict="id_sci,annee_constatation"
            ).execute()
        except Exception:
            logger.warning("deficit_reportable_save_failed", sci_id=sci_id, annee=annee)

    def _impute_prior_deficits(
        self, prior_rows: list[dict], resultat_brut_positif: float, client
    ) -> tuple[list[DeficitAnterieur], float]:
        """Impute prior deficits against positive rental income (FIFO).

        Returns the list of DeficitAnterieur and total amount imputed.
        """
        deficits: list[DeficitAnterieur] = []
        remaining_income = resultat_brut_positif
        total_imputed = 0.0

        for row in prior_rows:
            solde = self._safe_float(row.get("solde_restant"))
            annee_c = int(row.get("annee_constatation", 0))
            annee_p = int(row.get("annee_prescription", 0))
            initial = self._safe_float(row.get("deficit_interets")) + self._safe_float(row.get("deficit_charges"))
            prev_imputed = self._safe_float(row.get("total_impute_foncier"))

            if solde <= 0:
                deficits.append(DeficitAnterieur(
                    annee=annee_c,
                    montant_initial=initial,
                    total_impute=prev_imputed,
                    solde_restant=0,
                    annee_prescription=annee_p,
                ))
                continue

            impute_now = min(solde, remaining_income)
            new_solde = round(solde - impute_now, 2)
            new_total_imputed = round(prev_imputed + impute_now, 2)

            if impute_now > 0:
                remaining_income = round(remaining_income - impute_now, 2)
                total_imputed = round(total_imputed + impute_now, 2)

                # Update the DB row
                try:
                    row_id = row.get("id")
                    if row_id:
                        client.table("deficit_reportable").update({
                            "total_impute_foncier": new_total_imputed,
                            "solde_restant": new_solde,
                        }).eq("id", row_id).execute()
                except Exception:
                    logger.warning("deficit_imputation_update_failed", row_id=row.get("id"))

            deficits.append(DeficitAnterieur(
                annee=annee_c,
                montant_initial=initial,
                total_impute=new_total_imputed,
                solde_restant=new_solde,
                annee_prescription=annee_p,
            ))

        return deficits, total_imputed

    def calculate(self, sci_id: str, annee: int, client) -> ResumeFiscalResult:
        """Calculate the résumé fiscal for a given SCI and year.

        Args:
            sci_id: UUID of the SCI.
            annee: Fiscal year (e.g. 2025).
            client: Supabase client (user or service) for DB queries.

        Returns:
            A fully populated ResumeFiscalResult.
        """
        alertes: list[str] = []

        # 1. Fetch SCI data (with extended fields for CERFA)
        sci_rows = self._execute_select(
            client.table("sci")
            .select("nom, siren, regime_fiscal, adresse_siege, capital_social, nom_gerant")
            .eq("id", sci_id)
        )
        if not sci_rows:
            return ResumeFiscalResult(
                sci_nom="SCI inconnue",
                sci_siren="",
                regime_fiscal="",
                annee=annee,
                alertes=["SCI introuvable."],
            )

        sci = sci_rows[0]
        sci_nom = sci.get("nom") or "SCI"
        sci_siren = sci.get("siren") or ""
        regime_fiscal = sci.get("regime_fiscal") or "IR"
        sci_adresse_siege = sci.get("adresse_siege") or ""
        sci_capital_social = self._safe_float(sci.get("capital_social"))
        sci_nom_gerant = sci.get("nom_gerant") or ""

        # 2. Fetch associés with parts (include id and email for report-2042)
        associe_rows = self._execute_select(
            client.table("associes")
            .select("id, nom, email, part")
            .eq("id_sci", sci_id)
        )

        # 3. Fetch all biens for this SCI
        bien_rows = self._execute_select(
            client.table("biens")
            .select("id, adresse, ville, type_locatif, prix_acquisition")
            .eq("id_sci", sci_id)
        )

        if not bien_rows:
            alertes.append("Aucun bien enregistré pour cette SCI.")

        # 4. For each bien, calculate CERFA lines
        biens_detail: list[BienFiscalDetail] = []
        total_revenus = 0.0
        total_charges = 0.0
        total_interets = 0.0

        for bien in bien_rows:
            bien_id = str(bien.get("id", ""))
            adresse = bien.get("adresse") or "Adresse inconnue"
            ville = bien.get("ville") or ""

            detail = BienFiscalDetail(
                bien_id=bien_id,
                adresse=adresse,
                ville=ville,
            )

            # Ligne 211: loyers encaissés (paid loyers for the year)
            loyer_rows = self._execute_select(
                client.table("loyers")
                .select("montant, statut, date_loyer")
                .eq("id_bien", bien_id)
                .eq("statut", "paye")
                .gte("date_loyer", f"{annee}-01-01")
                .lte("date_loyer", f"{annee}-12-31")
            )
            detail.ligne_211_loyers_bruts = round(
                sum(self._safe_float(r.get("montant")) for r in loyer_rows), 2
            )

            if not loyer_rows:
                alertes.append(f"Aucun loyer encaissé pour {adresse} ({ville}) en {annee}.")

            # Ligne 215: frais de gestion forfaitaire = 20 € par bien
            detail.ligne_215_frais_gestion = 20.0

            # Fetch charges for this bien and this year
            charge_rows = self._execute_select(
                client.table("charges")
                .select("type_charge, montant, date_paiement")
                .eq("id_bien", bien_id)
                .gte("date_paiement", f"{annee}-01-01")
                .lte("date_paiement", f"{annee}-12-31")
            )

            # Build a lookup by type_charge
            charges_by_type: dict[str, float] = {}
            for c in charge_rows:
                t = (c.get("type_charge") or "").lower()
                charges_by_type[t] = charges_by_type.get(t, 0.0) + self._safe_float(c.get("montant"))

            # Ligne 221: travaux / entretien (all variants)
            detail.ligne_221_travaux = round(
                charges_by_type.get("entretien", 0.0)
                + charges_by_type.get("travaux", 0.0)
                + charges_by_type.get("travaux_entretien", 0.0)
                + charges_by_type.get("travaux_amelioration", 0.0),
                2,
            )

            # Ligne 224: taxe foncière
            detail.ligne_224_taxe_fonciere = round(
                charges_by_type.get("taxe_fonciere", 0.0), 2
            )

            # Ligne 227: copropriété (UI uses 'syndic' or 'copropriete')
            detail.ligne_227_copropriete = round(
                charges_by_type.get("copropriete", 0.0)
                + charges_by_type.get("syndic", 0.0),
                2,
            )

            # Ligne 220: assurance PNO (from assurances_pno table)
            pno_rows = self._execute_select(
                client.table("assurances_pno")
                .select("montant_annuel")
                .eq("id_bien", bien_id)
            )
            detail.ligne_220_assurance = round(
                sum(self._safe_float(r.get("montant_annuel")) for r in pno_rows), 2
            )

            # Ligne 230: intérêts d'emprunt (UI uses 'credit', 'interets_emprunt', or 'interets')
            detail.ligne_230_interets_emprunt = round(
                charges_by_type.get("interets_emprunt", 0.0)
                + charges_by_type.get("interets", 0.0)
                + charges_by_type.get("credit", 0.0),
                2,
            )

            # Ligne 220: also capture assurance charges from charges table
            detail.ligne_220_assurance = round(
                detail.ligne_220_assurance
                + charges_by_type.get("assurance", 0.0)
                + charges_by_type.get("assurance_pno", 0.0)
                + charges_by_type.get("prime_assurance", 0.0),
                2,
            )

            # Add frais_gestion and frais_procedure to L221
            detail.ligne_221_travaux = round(
                detail.ligne_221_travaux
                + charges_by_type.get("frais_gestion", 0.0)
                + charges_by_type.get("frais_procedure", 0.0),
                2,
            )

            # Detect unmapped charge types and generate alertes
            mapped_types = {"entretien", "travaux", "travaux_entretien", "travaux_amelioration",
                           "taxe_fonciere", "copropriete", "syndic",
                           "interets_emprunt", "interets", "credit",
                           "assurance", "assurance_pno", "prime_assurance",
                           "frais_gestion", "frais_procedure", "autre_deductible"}
            for ct, montant in charges_by_type.items():
                if ct and ct not in mapped_types and montant > 0:
                    alertes.append(
                        f"{detail.adresse} : charge de type '{ct}' ({montant:.0f} €) non mappée aux lignes CERFA."
                    )

            # Ligne 229: total charges déductibles (hors intérêts)
            detail.ligne_229_total_charges = round(
                detail.ligne_215_frais_gestion
                + detail.ligne_220_assurance
                + detail.ligne_221_travaux
                + detail.ligne_224_taxe_fonciere
                + detail.ligne_227_copropriete,
                2,
            )

            # Ligne 240: résultat net = revenus - charges - intérêts
            detail.ligne_240_resultat_net = round(
                detail.ligne_211_loyers_bruts
                - detail.ligne_229_total_charges
                - detail.ligne_230_interets_emprunt,
                2,
            )

            # Alerte: bien avec revenus mais sans aucune charge
            charges_total = detail.ligne_229_total_charges + detail.ligne_230_interets_emprunt - detail.ligne_215_frais_gestion
            if detail.ligne_211_loyers_bruts > 0 and charges_total <= 0:
                alertes.append(
                    f"{detail.adresse} : aucune charge déductible saisie (hors forfait 20 €). "
                    f"Le résultat fiscal est probablement surestimé."
                )

            biens_detail.append(detail)
            total_revenus += detail.ligne_211_loyers_bruts
            total_charges += detail.ligne_229_total_charges
            total_interets += detail.ligne_230_interets_emprunt

        # 5. Aggregate
        resultat_global = round(total_revenus - total_charges - total_interets, 2)

        # ── Phase 3: Load and impute prior deficits (FIFO) ─────────────
        deficits_anterieurs: list[DeficitAnterieur] = []
        total_deficits_anterieurs_imputes = 0.0

        if resultat_global > 0:
            prior_rows = self._load_prior_deficits(sci_id, annee, client)
            if prior_rows:
                deficits_anterieurs, total_deficits_anterieurs_imputes = self._impute_prior_deficits(
                    prior_rows, resultat_global, client
                )
                # Adjust the result after imputation
                resultat_global = round(resultat_global - total_deficits_anterieurs_imputes, 2)
        else:
            # Even if deficit, load prior deficits for display
            prior_rows = self._load_prior_deficits(sci_id, annee, client)
            for row in prior_rows:
                initial = self._safe_float(row.get("deficit_interets")) + self._safe_float(row.get("deficit_charges"))
                deficits_anterieurs.append(DeficitAnterieur(
                    annee=int(row.get("annee_constatation", 0)),
                    montant_initial=initial,
                    total_impute=self._safe_float(row.get("total_impute_foncier")),
                    solde_restant=self._safe_float(row.get("solde_restant")),
                    annee_prescription=int(row.get("annee_prescription", 0)),
                ))

        # 6. Quote-part per associé
        associes_qp: list[AssocieQuotePart] = []
        total_parts = sum(self._safe_float(a.get("part")) for a in associe_rows)

        # ── Phase 2: Déficit foncier (art. 156-I-3° CGI) ─────────────
        is_deficit = resultat_global < 0
        deficit_total = 0.0
        deficit_interets_emprunt_val = 0.0
        deficit_imputable_revenu_global = 0.0
        deficit_reportable_foncier = 0.0

        if is_deficit:
            deficit_total = round(abs(resultat_global), 2)

            # Intérêts d'emprunt: only deductible against rental income
            deficit_interets = round(min(total_interets, deficit_total), 2)

            # Other charges: deductible against global income up to 10 700 EUR
            deficit_hors_interets = round(deficit_total - deficit_interets, 2)
            deficit_imputable_revenu_global = round(min(deficit_hors_interets, 10_700), 2)
            deficit_reportable_foncier = round(
                deficit_hors_interets - deficit_imputable_revenu_global, 2
            )
            deficit_interets_emprunt_val = deficit_interets

        if total_parts > 0:
            for a in associe_rows:
                part = self._safe_float(a.get("part"))
                pct = round((part / total_parts) * 100, 2)
                qp = round(resultat_global * (part / total_parts), 2)

                # Cases 2042
                case_4ba = round(max(qp, 0), 2)
                case_4bb = 0.0
                case_4bc = 0.0
                case_4bd = round(total_deficits_anterieurs_imputes * (part / total_parts), 2)

                if qp < 0:
                    qp_deficit = abs(qp)
                    # Proportional split of deficit components
                    ratio = part / total_parts
                    case_4bb = round(deficit_imputable_revenu_global * ratio, 2)
                    case_4bc = round(
                        (deficit_interets_emprunt_val + deficit_reportable_foncier) * ratio, 2
                    )

                associes_qp.append(AssocieQuotePart(
                    associe_id=str(a.get("id") or ""),
                    nom=a.get("nom") or "Associé",
                    email=a.get("email") or "",
                    part_pct=pct,
                    quote_part_resultat=qp,
                    case_4ba=case_4ba,
                    case_4bb=case_4bb,
                    case_4bc=case_4bc,
                    case_4bd=case_4bd,
                ))
        else:
            alertes.append("Aucun associé avec parts renseignées — quote-parts non calculables.")

        if not associe_rows:
            alertes.append("Aucun associé enregistré pour cette SCI.")

        # ── Phase 2: Micro-foncier comparison (art. 32 CGI) ────────────
        # Eligible if total revenus bruts <= 15 000 EUR
        micro_foncier_eligible = total_revenus <= 15_000
        if micro_foncier_eligible:
            micro_foncier_abattement = round(total_revenus * 0.30, 2)
            micro_foncier_resultat = round(total_revenus - micro_foncier_abattement, 2)
        else:
            micro_foncier_abattement = 0.0
            micro_foncier_resultat = 0.0

        # Comparison: which regime yields lower taxable income?
        if micro_foncier_eligible:
            economie_reel = round(micro_foncier_resultat - resultat_global, 2)
            # economie_reel > 0 means réel produces lower taxable income
            regime_recommande = "reel" if economie_reel > 0 else "micro"
            economie_regime_recommande = abs(economie_reel)
        else:
            regime_recommande = "reel"
            economie_regime_recommande = 0.0

        result = ResumeFiscalResult(
            sci_nom=sci_nom,
            sci_siren=sci_siren,
            regime_fiscal=regime_fiscal,
            annee=annee,
            biens=biens_detail,
            total_revenus=round(total_revenus, 2),
            total_charges=round(total_charges, 2),
            total_interets=round(total_interets, 2),
            resultat_global=resultat_global,
            associes=associes_qp,
            alertes=alertes,
            # SCI identification
            sci_adresse_siege=sci_adresse_siege,
            sci_capital_social=sci_capital_social,
            sci_nom_gerant=sci_nom_gerant,
            nb_biens=len(biens_detail),
            nb_associes=len(associe_rows),
            # Micro-foncier
            micro_foncier_eligible=micro_foncier_eligible,
            micro_foncier_abattement=micro_foncier_abattement,
            micro_foncier_resultat=micro_foncier_resultat,
            regime_recommande=regime_recommande,
            economie_regime_recommande=economie_regime_recommande,
            # Déficit foncier
            is_deficit=is_deficit,
            deficit_total=deficit_total,
            deficit_interets_emprunt=deficit_interets_emprunt_val,
            deficit_imputable_revenu_global=deficit_imputable_revenu_global,
            deficit_reportable_foncier=deficit_reportable_foncier,
            # Déficits antérieurs
            deficits_anterieurs=deficits_anterieurs,
            total_deficits_anterieurs_imputes=total_deficits_anterieurs_imputes,
        )

        # Save current year deficit to tracker
        if is_deficit:
            self._save_deficit(sci_id, annee, result, client)

        return result
