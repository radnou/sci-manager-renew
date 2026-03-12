"""Tests for rentabilite_service — profitability calculations."""

from app.services.rentabilite_service import calculate_rentabilite


class TestCalculateRentabilite:
    """Tests for calculate_rentabilite function."""

    def test_basic_brute_and_nette(self):
        """Rentabilite brute = (loyer*12 / prix) * 100."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
        )
        # brute = (12000 / 200000) * 100 = 6.0
        assert result["brute"] == 6.0
        # nette same as brute when no charges
        assert result["nette"] == 6.0
        assert result["cashflow_mensuel"] == 1_000
        assert result["cashflow_annuel"] == 12_000

    def test_with_charges(self):
        """Charges reduce nette but not brute."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            charges_mensuelles=200,
        )
        assert result["brute"] == 6.0
        # nette = ((12000 - 2400) / 200000) * 100 = 4.8
        assert result["nette"] == 4.8
        assert result["cashflow_mensuel"] == 800
        assert result["cashflow_annuel"] == 9_600

    def test_with_pno_and_frais_agence(self):
        """PNO and frais agence are annual, spread to monthly for cashflow."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            charges_mensuelles=100,
            prime_pno_annuelle=600,
            frais_agence_annuel=1_200,
        )
        # brute = (12000 / 200000) * 100 = 6.0
        assert result["brute"] == 6.0
        # charges_annuelles = (100*12) + 600 + 1200 = 3000
        # nette = ((12000 - 3000) / 200000) * 100 = 4.5
        assert result["nette"] == 4.5
        # cashflow_mensuel = 1000 - 100 - 50 - 100 = 750
        assert result["cashflow_mensuel"] == 750
        assert result["cashflow_annuel"] == 9_000

    def test_zero_prix_acquisition(self):
        """Zero prix returns all zeros (division guard)."""
        result = calculate_rentabilite(
            prix_acquisition=0,
            loyer_mensuel=1_000,
        )
        assert result == {"brute": 0, "nette": 0, "cashflow_mensuel": 0, "cashflow_annuel": 0}

    def test_none_prix_acquisition(self):
        """None prix returns all zeros."""
        result = calculate_rentabilite(
            prix_acquisition=None,
            loyer_mensuel=1_000,
        )
        assert result == {"brute": 0, "nette": 0, "cashflow_mensuel": 0, "cashflow_annuel": 0}

    def test_negative_prix_acquisition(self):
        """Negative prix returns all zeros."""
        result = calculate_rentabilite(
            prix_acquisition=-100_000,
            loyer_mensuel=1_000,
        )
        assert result == {"brute": 0, "nette": 0, "cashflow_mensuel": 0, "cashflow_annuel": 0}

    def test_zero_loyer(self):
        """Zero loyer gives zero rentabilite."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=0,
        )
        assert result["brute"] == 0
        assert result["nette"] == 0
        assert result["cashflow_mensuel"] == 0
        assert result["cashflow_annuel"] == 0

    def test_negative_cashflow(self):
        """Charges higher than loyer produce negative cashflow."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=500,
            charges_mensuelles=800,
        )
        assert result["brute"] == 3.0
        # nette = ((6000 - 9600) / 200000) * 100 = -1.8
        assert result["nette"] == -1.8
        assert result["cashflow_mensuel"] == -300
        assert result["cashflow_annuel"] == -3_600

    def test_rounding(self):
        """Results are rounded to 2 decimal places."""
        result = calculate_rentabilite(
            prix_acquisition=300_000,
            loyer_mensuel=750,
        )
        # brute = (9000 / 300000) * 100 = 3.0
        assert result["brute"] == 3.0
        # all values are floats with max 2 decimals
        for key in ("brute", "nette", "cashflow_mensuel", "cashflow_annuel"):
            value = result[key]
            assert value == round(value, 2)

    def test_large_values(self):
        """Handles large acquisition prices and loyers correctly."""
        result = calculate_rentabilite(
            prix_acquisition=2_000_000,
            loyer_mensuel=8_000,
            charges_mensuelles=2_000,
            prime_pno_annuelle=3_600,
            frais_agence_annuel=4_800,
        )
        # brute = (96000 / 2000000) * 100 = 4.8
        assert result["brute"] == 4.8
        # charges_annuelles = 24000 + 3600 + 4800 = 32400
        # nette = ((96000 - 32400) / 2000000) * 100 = 3.18
        assert result["nette"] == 3.18

    def test_default_optional_params(self):
        """Default values for optional params are zero."""
        result = calculate_rentabilite(
            prix_acquisition=100_000,
            loyer_mensuel=500,
        )
        # With all defaults at 0, brute == nette
        assert result["brute"] == result["nette"]
