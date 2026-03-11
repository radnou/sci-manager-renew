"""Service de calcul de rentabilité pour les biens immobiliers."""


def calculate_rentabilite(
    prix_acquisition: float | None,
    loyer_mensuel: float,
    charges_mensuelles: float = 0,
    prime_pno_annuelle: float = 0,
    frais_agence_annuel: float = 0,
) -> dict:
    """
    Calcule la rentabilité brute, nette et le cashflow d'un bien.

    Args:
        prix_acquisition: Prix d'achat du bien (requis et > 0 pour un calcul valide).
        loyer_mensuel: Loyer mensuel hors charges.
        charges_mensuelles: Charges mensuelles du bien.
        prime_pno_annuelle: Prime annuelle d'assurance PNO.
        frais_agence_annuel: Total annuel des frais d'agence.

    Returns:
        Dictionnaire avec brute, nette, cashflow_mensuel, cashflow_annuel.
    """
    if not prix_acquisition or prix_acquisition <= 0:
        return {"brute": 0, "nette": 0, "cashflow_mensuel": 0, "cashflow_annuel": 0}

    loyer_annuel = loyer_mensuel * 12
    brute = (loyer_annuel / prix_acquisition) * 100

    charges_annuelles = (charges_mensuelles * 12) + prime_pno_annuelle + frais_agence_annuel
    revenu_net = loyer_annuel - charges_annuelles
    nette = (revenu_net / prix_acquisition) * 100

    cashflow_mensuel = loyer_mensuel - charges_mensuelles - prime_pno_annuelle / 12 - frais_agence_annuel / 12
    cashflow_annuel = cashflow_mensuel * 12

    return {
        "brute": round(brute, 2),
        "nette": round(nette, 2),
        "cashflow_mensuel": round(cashflow_mensuel, 2),
        "cashflow_annuel": round(cashflow_annuel, 2),
    }
