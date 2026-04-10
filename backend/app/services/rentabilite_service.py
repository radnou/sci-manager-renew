"""Service de calcul de rentabilité pour les biens immobiliers."""

PRELEVEMENTS_SOCIAUX_RATE = 0.172  # 17.2% on net foncier income


def calculate_rentabilite(
    prix_acquisition: float | None,
    loyer_mensuel: float,
    charges_mensuelles: float = 0,
    prime_pno_annuelle: float = 0,
    frais_agence_annuel: float = 0,
    taxe_fonciere: float = 0,
    tmi: float = 0,
    mensualite_credit: float = 0,
) -> dict:
    """
    Calcule la rentabilité brute, nette, nette-nette et le cashflow d'un bien.

    Args:
        prix_acquisition: Prix d'achat du bien (requis et > 0 pour un calcul valide).
        loyer_mensuel: Loyer mensuel hors charges.
        charges_mensuelles: Charges mensuelles du bien.
        prime_pno_annuelle: Prime annuelle d'assurance PNO.
        frais_agence_annuel: Total annuel des frais d'agence.
        taxe_fonciere: Taxe foncière annuelle du bien.
        tmi: Taux marginal d'imposition du propriétaire (0-100, e.g. 30 for 30%).
        mensualite_credit: Mensualité du crédit immobilier actif (capital + intérêts + assurance).

    Returns:
        Dictionnaire avec brute, nette, nette_nette, cashflow_mensuel, cashflow_annuel,
        cashflow_apres_credit_mensuel, cashflow_apres_credit_annuel,
        taxe_fonciere, prelevements_sociaux, impot_revenu_foncier.
    """
    if not prix_acquisition or prix_acquisition <= 0:
        return {
            "brute": 0,
            "nette": 0,
            "nette_nette": 0,
            "cashflow_mensuel": 0,
            "cashflow_annuel": 0,
            "cashflow_apres_credit_mensuel": 0,
            "cashflow_apres_credit_annuel": 0,
            "taxe_fonciere": taxe_fonciere,
            "prelevements_sociaux": 0,
            "impot_revenu_foncier": 0,
        }

    loyer_annuel = loyer_mensuel * 12
    brute = (loyer_annuel / prix_acquisition) * 100

    charges_annuelles = (
        (charges_mensuelles * 12)
        + prime_pno_annuelle
        + frais_agence_annuel
        + taxe_fonciere
    )
    revenu_net = loyer_annuel - charges_annuelles
    nette = (revenu_net / prix_acquisition) * 100

    # After-tax: prélèvements sociaux + IR foncier apply only when net foncier is positive
    net_foncier_imposable = max(revenu_net, 0)
    prelevements_sociaux = net_foncier_imposable * PRELEVEMENTS_SOCIAUX_RATE
    impot_revenu_foncier = net_foncier_imposable * (tmi / 100)
    revenu_net_apres_impots = revenu_net - prelevements_sociaux - impot_revenu_foncier
    nette_nette = (revenu_net_apres_impots / prix_acquisition) * 100

    cashflow_mensuel = (
        loyer_mensuel
        - charges_mensuelles
        - prime_pno_annuelle / 12
        - frais_agence_annuel / 12
        - taxe_fonciere / 12
    )
    cashflow_annuel = cashflow_mensuel * 12

    cashflow_apres_credit_mensuel = cashflow_mensuel - mensualite_credit
    cashflow_apres_credit_annuel = cashflow_apres_credit_mensuel * 12

    return {
        "brute": round(brute, 2),
        "nette": round(nette, 2),
        "nette_nette": round(nette_nette, 2),
        "cashflow_mensuel": round(cashflow_mensuel, 2),
        "cashflow_annuel": round(cashflow_annuel, 2),
        "cashflow_apres_credit_mensuel": round(cashflow_apres_credit_mensuel, 2),
        "cashflow_apres_credit_annuel": round(cashflow_apres_credit_annuel, 2),
        "taxe_fonciere": taxe_fonciere,
        "prelevements_sociaux": round(prelevements_sociaux, 2),
        "impot_revenu_foncier": round(impot_revenu_foncier, 2),
    }
