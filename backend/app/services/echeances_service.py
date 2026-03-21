"""Echeances engine — generates upcoming deadlines dynamically from existing data."""

from __future__ import annotations

from datetime import date, timedelta

import structlog

from app.core.exceptions import DatabaseError

logger = structlog.get_logger(__name__)

# Diagnostic validity periods
_DPE_VALIDITY_YEARS = 10
_ELECTRICITE_VALIDITY_YEARS = 6
_GAZ_VALIDITY_YEARS = 6
_AMIANTE_VALIDITY_YEARS = 3  # conservative (if positive)
_PLOMB_VALIDITY_YEARS = 1    # if positive


def _parse_date(date_str: str | None) -> date | None:
    """Parse ISO date string safely."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(str(date_str)[:10])
    except (ValueError, TypeError):
        return None


def _calc_urgence(date_echeance: str) -> str:
    """Calculate urgency level based on deadline date relative to today."""
    today = date.today()
    d = _parse_date(date_echeance)
    if d is None:
        return "normale"
    if d < today:
        return "depassee"
    if d < today + timedelta(days=30):
        return "critique"
    if d < today + timedelta(days=90):
        return "urgente"
    if d < today + timedelta(days=180):
        return "normale"
    return "lointaine"


class EcheancesService:
    """Generate all upcoming deadlines dynamically from existing data."""

    def get_echeances(self, client, user_id: str, sci_id: str | None = None) -> dict:
        """Return echeances list + resume counts for a user's SCIs."""
        echeances: list[dict] = []
        sci_ids = self._get_user_sci_ids(client, user_id, sci_id)

        for sid in sci_ids:
            sci = self._get_sci(client, sid)
            if not sci:
                continue
            echeances += self._check_ag_annuelle(sci)
            echeances += self._check_declarations_fiscales(sci)

            biens = self._get_biens(client, sid)
            for bien in biens:
                echeances += self._check_pno(client, bien)
                echeances += self._check_diagnostics(bien)

                baux = self._get_baux_actifs(client, bien["id"])
                for bail in baux:
                    echeances += self._check_fin_bail(bail, bien)
                    echeances += self._check_revision_irl(bail, bien)

        # Calculate urgency and sort
        for e in echeances:
            e["urgence"] = _calc_urgence(e["date_echeance"])

        echeances.sort(key=lambda e: e["date_echeance"])

        resume = {
            "depassee": len([e for e in echeances if e["urgence"] == "depassee"]),
            "critique": len([e for e in echeances if e["urgence"] == "critique"]),
            "urgente": len([e for e in echeances if e["urgence"] == "urgente"]),
            "normale": len([e for e in echeances if e["urgence"] == "normale"]),
            "lointaine": len([e for e in echeances if e["urgence"] == "lointaine"]),
        }

        return {"echeances": echeances, "resume": resume}

    # ── Data access helpers ────────────────────────────────────────

    def _get_user_sci_ids(self, client, user_id: str, sci_id: str | None = None) -> list[str]:
        """Return SCI ids the user has access to, optionally filtered."""
        result = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))
        ids = [str(row["id_sci"]) for row in (result.data or []) if row.get("id_sci")]
        if sci_id:
            ids = [i for i in ids if i == sci_id]
        return ids

    def _get_sci(self, client, sci_id: str) -> dict | None:
        """Fetch a single SCI by id."""
        result = client.table("sci").select("*").eq("id", sci_id).execute()
        if getattr(result, "error", None) or not result.data:
            return None
        return result.data[0]

    def _get_biens(self, client, sci_id: str) -> list[dict]:
        """Fetch all biens for a SCI."""
        result = client.table("biens").select("*").eq("id_sci", sci_id).execute()
        if getattr(result, "error", None):
            return []
        return result.data or []

    def _get_baux_actifs(self, client, bien_id: str) -> list[dict]:
        """Fetch active baux for a bien."""
        result = (
            client.table("baux")
            .select("*")
            .eq("id_bien", bien_id)
            .eq("statut", "en_cours")
            .execute()
        )
        if getattr(result, "error", None):
            return []
        return result.data or []

    # ── Deadline checks ────────────────────────────────────────────

    def _check_ag_annuelle(self, sci: dict) -> list[dict]:
        """AG due within 6 months of fiscal year end (Dec 31 by default)."""
        echeances: list[dict] = []
        today = date.today()
        sci_id = str(sci.get("id", ""))
        sci_nom = sci.get("nom", "SCI")

        # Fiscal year end = Dec 31 of last year or current year
        # AG must be held within 6 months of fiscal year end
        for year in [today.year - 1, today.year]:
            fiscal_year_end = date(year, 12, 31)
            ag_deadline = fiscal_year_end + timedelta(days=183)  # ~6 months

            # Only generate if the deadline is somewhat relevant (not too far past)
            if ag_deadline < today - timedelta(days=365):
                continue

            echeances.append({
                "type": "ag_annuelle",
                "entite": sci_nom,
                "titre": f"Assemblée générale annuelle {year}",
                "description": f"L'AG annuelle pour l'exercice {year} doit se tenir dans les 6 mois suivant la clôture de l'exercice.",
                "date_echeance": ag_deadline.isoformat(),
                "urgence": "",  # calculated later
                "reference_legale": "Art. 1856 du Code civil",
                "consequence": "Risque d'irrégularité des décisions sociales et de contestation par les associés.",
                "action_url": f"/scis/{sci_id}/assemblees-generales",
            })

        return echeances

    def _check_declarations_fiscales(self, sci: dict) -> list[dict]:
        """2072 due ~May 3, 2044 due ~May 31 of the current year."""
        echeances: list[dict] = []
        today = date.today()
        sci_id = str(sci.get("id", ""))
        sci_nom = sci.get("nom", "SCI")
        regime = sci.get("regime_fiscal", "IR")
        year = today.year

        # Déclaration 2072 — all SCIs
        echeances.append({
            "type": "declaration_2072",
            "entite": sci_nom,
            "titre": f"Déclaration 2072 — Revenus {year - 1}",
            "description": f"Déclaration des résultats de la SCI pour l'exercice {year - 1}.",
            "date_echeance": date(year, 5, 3).isoformat(),
            "urgence": "",
            "reference_legale": "Art. 238 bis du CGI",
            "consequence": "Majoration de 10 % en cas de retard, mise en demeure fiscale.",
            "action_url": f"/scis/{sci_id}/fiscalite",
        })

        # Déclaration 2044 — only IR regime
        if regime == "IR":
            echeances.append({
                "type": "declaration_2044",
                "entite": sci_nom,
                "titre": f"Déclaration 2044 — Revenus fonciers {year - 1}",
                "description": f"Déclaration des revenus fonciers pour l'exercice {year - 1} (régime IR).",
                "date_echeance": date(year, 5, 31).isoformat(),
                "urgence": "",
                "reference_legale": "Art. 28 du CGI",
                "consequence": "Majoration de 10 % et pénalités de retard.",
                "action_url": f"/scis/{sci_id}/fiscalite",
            })

        return echeances

    def _check_pno(self, client, bien: dict) -> list[dict]:
        """PNO expiration from assurances_pno.date_echeance."""
        echeances: list[dict] = []
        bien_id = str(bien.get("id", ""))
        sci_id = str(bien.get("id_sci", ""))
        adresse = bien.get("adresse", "Bien")

        result = (
            client.table("assurances_pno")
            .select("date_echeance, compagnie")
            .eq("id_bien", bien_id)
            .execute()
        )
        for pno in (result.data or []):
            date_echeance = pno.get("date_echeance")
            if not date_echeance:
                continue
            compagnie = pno.get("compagnie", "")
            echeances.append({
                "type": "pno_expiration",
                "entite": adresse,
                "titre": f"Assurance PNO — {compagnie or 'renouvellement'}",
                "description": f"L'assurance propriétaire non-occupant pour {adresse} expire le {date_echeance}.",
                "date_echeance": str(date_echeance),
                "urgence": "",
                "reference_legale": "Loi ALUR art. 9-1 (loi n°89-462)",
                "consequence": "Défaut d'assurance : responsabilité civile engagée, non-couverture sinistre.",
                "action_url": f"/scis/{sci_id}/biens/{bien_id}",
            })

        return echeances

    def _check_diagnostics(self, bien: dict) -> list[dict]:
        """Check DPE, electricite, gaz, amiante, plomb diagnostic expiration."""
        echeances: list[dict] = []
        bien_id = str(bien.get("id", ""))
        sci_id = str(bien.get("id_sci", ""))
        adresse = bien.get("adresse", "Bien")

        diag_checks = [
            ("dpe_date", _DPE_VALIDITY_YEARS, "DPE", "Diagnostic de performance énergétique"),
            ("diagnostic_electricite_date", _ELECTRICITE_VALIDITY_YEARS, "Électricité", "Diagnostic électricité"),
            ("diagnostic_gaz_date", _GAZ_VALIDITY_YEARS, "Gaz", "Diagnostic gaz"),
            ("diagnostic_amiante_date", _AMIANTE_VALIDITY_YEARS, "Amiante", "Diagnostic amiante (DTA)"),
            ("diagnostic_plomb_date", _PLOMB_VALIDITY_YEARS, "Plomb", "Diagnostic plomb (CREP)"),
        ]

        for field, validity_years, label, description in diag_checks:
            diag_date_str = bien.get(field)
            if not diag_date_str:
                continue
            diag_date = _parse_date(diag_date_str)
            if not diag_date:
                continue

            expiry = diag_date + timedelta(days=validity_years * 365)
            echeances.append({
                "type": f"diagnostic_{label.lower().replace('é', 'e')}",
                "entite": adresse,
                "titre": f"{label} — renouvellement",
                "description": f"{description} pour {adresse}, réalisé le {diag_date_str}. Validité : {validity_years} ans.",
                "date_echeance": expiry.isoformat(),
                "urgence": "",
                "reference_legale": "Code de la construction et de l'habitation",
                "consequence": f"Diagnostic {label} expiré : obligation de renouvellement avant mise en location.",
                "action_url": f"/scis/{sci_id}/biens/{bien_id}",
            })

        return echeances

    def _check_fin_bail(self, bail: dict, bien: dict) -> list[dict]:
        """Check bail.date_fin for upcoming lease expiry."""
        date_fin = bail.get("date_fin")
        if not date_fin:
            return []

        bien_id = str(bien.get("id", ""))
        sci_id = str(bien.get("id_sci", ""))
        adresse = bien.get("adresse", "Bien")

        return [{
            "type": "fin_bail",
            "entite": adresse,
            "titre": f"Fin de bail — {adresse}",
            "description": f"Le bail pour {adresse} arrive à échéance le {date_fin}. Préparer le renouvellement ou le congé.",
            "date_echeance": str(date_fin),
            "urgence": "",
            "reference_legale": "Loi n°89-462 du 6 juillet 1989, art. 10",
            "consequence": "Renouvellement tacite si aucune action. Congé à délivrer 6 mois avant (nu) ou 3 mois (meublé).",
            "action_url": f"/scis/{sci_id}/biens/{bien_id}",
        }]

    def _check_revision_irl(self, bail: dict, bien: dict) -> list[dict]:
        """Check anniversary of bail.date_debut for IRL revision."""
        date_debut = bail.get("date_debut")
        if not date_debut:
            return []

        debut = _parse_date(date_debut)
        if not debut:
            return []

        today = date.today()
        bien_id = str(bien.get("id", ""))
        sci_id = str(bien.get("id_sci", ""))
        adresse = bien.get("adresse", "Bien")

        # Find the next anniversary
        # Start from current year and check next occurrence
        for year_offset in range(0, 2):
            anniversary = debut.replace(year=today.year + year_offset)
            if anniversary >= today:
                return [{
                    "type": "revision_irl",
                    "entite": adresse,
                    "titre": f"Révision IRL — {adresse}",
                    "description": f"Date anniversaire du bail pour {adresse}. Vérifier l'indice IRL et appliquer la révision de loyer.",
                    "date_echeance": anniversary.isoformat(),
                    "urgence": "",
                    "reference_legale": "Loi n°89-462, art. 17-1",
                    "consequence": "Prescription annuelle : la révision non appliquée dans l'année est perdue.",
                    "action_url": f"/scis/{sci_id}/biens/{bien_id}",
                }]

        return []
