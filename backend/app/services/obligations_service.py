"""Service for regulatory obligation checking on a bien."""

from __future__ import annotations

from datetime import date, timedelta

import structlog

logger = structlog.get_logger(__name__)

# DPE validity: 10 years
_DPE_VALIDITY_DAYS = 10 * 365
# Amiante: no expiry if negative, 3 years if positive (we use 3 years as conservative)
_AMIANTE_VALIDITY_DAYS = 3 * 365
# Electricite: 6 years for location
_ELECTRICITE_VALIDITY_DAYS = 6 * 365
# Gaz: 6 years for location
_GAZ_VALIDITY_DAYS = 6 * 365
# Plomb (CREP): 6 years if positive, unlimited if negative (we use 6 years)
_PLOMB_VALIDITY_DAYS = 6 * 365


def get_obligations(client, bien_id: str) -> dict:
    """Check regulatory obligations for a bien.

    Checks:
    1. PNO valid = assurance_pno.date_echeance > today
    2. DPE valid = biens.dpe_classe IS NOT NULL AND biens.dpe_date within 10 years
    3. Bail actif = baux.statut = 'en_cours'
    4. Locataire rattache = bail_locataires exists for active bail
    5. Depot de garantie = bail.depot_garantie > 0
    6. Diagnostic dates validity

    Returns:
        {
            pno: {valid, detail},
            dpe: {valid, detail},
            bail: {valid, detail},
            locataire: {valid, detail},
            depot_garantie: {valid, detail},
            diagnostics: {amiante: {...}, electricite: {...}, gaz: {...}, plomb: {...}}
        }
    """
    today = date.today()

    # Fetch bien data (includes diagnostic dates)
    bien_result = client.table("biens").select("*").eq("id", bien_id).execute()
    bien = (bien_result.data or [{}])[0] if bien_result.data else {}

    # 1. PNO
    pno_result = (
        client.table("assurances_pno")
        .select("date_echeance, compagnie")
        .eq("id_bien", bien_id)
        .order("date_echeance", desc=True)
        .limit(1)
        .execute()
    )
    pno_data = (pno_result.data or [{}])[0] if pno_result.data else {}
    pno_echeance = pno_data.get("date_echeance")
    pno_valid = False
    pno_detail = "Aucune assurance PNO enregistrée"
    if pno_echeance:
        echeance_date = _parse_date(pno_echeance)
        if echeance_date and echeance_date > today:
            pno_valid = True
            pno_detail = f"Valide jusqu'au {pno_echeance} ({pno_data.get('compagnie', '')})"
        else:
            pno_detail = f"Expirée le {pno_echeance}"

    # 2. DPE
    dpe_classe = bien.get("dpe_classe")
    dpe_date_str = bien.get("dpe_date")
    dpe_valid = False
    dpe_detail = "Aucun DPE enregistré"
    if dpe_classe:
        if dpe_date_str:
            dpe_date = _parse_date(dpe_date_str)
            if dpe_date and (today - dpe_date).days <= _DPE_VALIDITY_DAYS:
                dpe_valid = True
                dpe_detail = f"Classe {dpe_classe}, réalisé le {dpe_date_str} (valide 10 ans)"
            else:
                dpe_detail = f"Classe {dpe_classe}, réalisé le {dpe_date_str} — expiré (>10 ans)"
        else:
            dpe_detail = f"Classe {dpe_classe} renseignée, date du diagnostic manquante"

    # 3. Bail actif
    bail_result = (
        client.table("baux")
        .select("id, date_debut, date_fin, depot_garantie")
        .eq("id_bien", bien_id)
        .eq("statut", "en_cours")
        .limit(1)
        .execute()
    )
    bail_data = (bail_result.data or [{}])[0] if bail_result.data else {}
    bail_id = bail_data.get("id")
    bail_valid = bail_id is not None
    bail_detail = "Aucun bail actif" if not bail_valid else f"Bail actif du {bail_data.get('date_debut')} au {bail_data.get('date_fin')}"

    # 4. Locataire rattache
    locataire_valid = False
    locataire_detail = "Aucun locataire rattaché"
    if bail_id:
        loc_result = (
            client.table("bail_locataires")
            .select("id_locataire")
            .eq("id_bail", bail_id)
            .execute()
        )
        loc_count = len(loc_result.data or [])
        if loc_count > 0:
            locataire_valid = True
            locataire_detail = f"{loc_count} locataire(s) rattaché(s)"
        else:
            locataire_detail = "Bail actif sans locataire rattaché"

    # 5. Depot de garantie
    depot_valid = False
    depot_detail = "Aucun dépôt de garantie"
    if bail_id:
        depot = bail_data.get("depot_garantie", 0) or 0
        if depot > 0:
            depot_valid = True
            depot_detail = f"Dépôt de garantie : {depot:.2f} EUR"
        else:
            depot_detail = "Bail actif sans dépôt de garantie enregistré"

    # 6. Diagnostic dates
    diagnostics = {}
    diag_fields = {
        "amiante": ("diagnostic_amiante_date", _AMIANTE_VALIDITY_DAYS, "Amiante (DTA)"),
        "electricite": ("diagnostic_electricite_date", _ELECTRICITE_VALIDITY_DAYS, "Électricité"),
        "gaz": ("diagnostic_gaz_date", _GAZ_VALIDITY_DAYS, "Gaz"),
        "plomb": ("diagnostic_plomb_date", _PLOMB_VALIDITY_DAYS, "Plomb (CREP)"),
    }
    for key, (field, validity_days, label) in diag_fields.items():
        diag_date_str = bien.get(field)
        if not diag_date_str:
            diagnostics[key] = {"valid": False, "detail": f"{label} : aucune date enregistrée"}
        else:
            diag_date = _parse_date(diag_date_str)
            if diag_date and (today - diag_date).days <= validity_days:
                diagnostics[key] = {
                    "valid": True,
                    "detail": f"{label} : réalisé le {diag_date_str} (valide {validity_days // 365} ans)",
                }
            else:
                diagnostics[key] = {
                    "valid": False,
                    "detail": f"{label} : réalisé le {diag_date_str} — expiré",
                }

    return {
        "pno": {"valid": pno_valid, "detail": pno_detail},
        "dpe": {"valid": dpe_valid, "detail": dpe_detail},
        "bail": {"valid": bail_valid, "detail": bail_detail},
        "locataire": {"valid": locataire_valid, "detail": locataire_detail},
        "depot_garantie": {"valid": depot_valid, "detail": depot_detail},
        "diagnostics": diagnostics,
    }


def _parse_date(date_str: str) -> date | None:
    """Parse a date string (YYYY-MM-DD) safely."""
    try:
        return date.fromisoformat(str(date_str)[:10])
    except (ValueError, TypeError):
        return None
