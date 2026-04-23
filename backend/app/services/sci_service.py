from typing import Any


class SCIService:
    @staticmethod
    def calculate_rentabilite(bien: dict[str, Any]) -> dict[str, float]:
        loyer_annuel = float(bien.get("loyer_cc", 0)) * 12
        prix_acquisition = float(bien.get("prix_acquisition") or 0)
        frais_notaire = float(bien.get("frais_notaire") or 0)
        frais_agence = float(bien.get("frais_agence_acquisition") or 0)
        charges_annuelles = float(bien.get("charges", 0)) * 12
        
        # Prix total d'acquisition (prix + frais)
        prix_total = prix_acquisition + frais_notaire + frais_agence

        rentabilite_brute = (loyer_annuel / prix_total * 100) if prix_total else 0
        rentabilite_nette = (
            ((loyer_annuel - charges_annuelles) / prix_total * 100)
            if prix_total
            else 0
        )

        return {
            "rentabilite_brute": round(rentabilite_brute, 2),
            "rentabilite_nette": round(rentabilite_nette, 2),
            "cashflow_annuel": round(loyer_annuel - charges_annuelles, 2),
        }
