"""Service de calcul du résumé fiscal — IR régime réel, ventilation par bien, lignes CERFA 2044."""

from __future__ import annotations

from dataclasses import dataclass, field


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

    nom: str
    part_pct: float
    quote_part_resultat: float


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

        # 1. Fetch SCI data
        sci_rows = self._execute_select(
            client.table("sci")
            .select("nom, siren, regime_fiscal")
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

        # 2. Fetch associés with parts
        associe_rows = self._execute_select(
            client.table("associes")
            .select("nom, part")
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

            # Ligne 221: travaux / entretien
            detail.ligne_221_travaux = round(
                charges_by_type.get("entretien", 0.0)
                + charges_by_type.get("travaux", 0.0),
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

            # Ligne 220: also capture 'assurance' charges (not just PNO table)
            detail.ligne_220_assurance = round(
                detail.ligne_220_assurance
                + charges_by_type.get("assurance", 0.0),
                2,
            )

            # Detect unmapped charge types and generate alertes
            mapped_types = {"entretien", "travaux", "taxe_fonciere", "copropriete", "syndic",
                           "interets_emprunt", "interets", "credit", "assurance"}
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

        # 6. Quote-part per associé
        associes_qp: list[AssocieQuotePart] = []
        total_parts = sum(self._safe_float(a.get("part")) for a in associe_rows)

        if total_parts > 0:
            for a in associe_rows:
                part = self._safe_float(a.get("part"))
                pct = round((part / total_parts) * 100, 2)
                qp = round(resultat_global * (part / total_parts), 2)
                associes_qp.append(AssocieQuotePart(
                    nom=a.get("nom") or "Associé",
                    part_pct=pct,
                    quote_part_resultat=qp,
                ))
        else:
            alertes.append("Aucun associé avec parts renseignées — quote-parts non calculables.")

        if not associe_rows:
            alertes.append("Aucun associé enregistré pour cette SCI.")

        return ResumeFiscalResult(
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
        )
