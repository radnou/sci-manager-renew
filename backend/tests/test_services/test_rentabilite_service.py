"""Tests for rentabilite_service — profitability calculations."""

from app.services.rentabilite_service import (
    PRELEVEMENTS_SOCIAUX_RATE,
    calculate_rentabilite,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ZERO_RESULT_KEYS = {
    "brute", "nette", "nette_nette", "cashflow_mensuel", "cashflow_annuel",
    "prelevements_sociaux", "impot_revenu_foncier",
}


def _assert_zero_guard(result: dict) -> None:
    """All numeric output fields are 0 for invalid prix_acquisition."""
    for key in _ZERO_RESULT_KEYS:
        assert result[key] == 0, f"Expected {key}=0, got {result[key]}"


# ---------------------------------------------------------------------------
# Existing tests — backward-compatible
# ---------------------------------------------------------------------------


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
        _assert_zero_guard(result)

    def test_none_prix_acquisition(self):
        """None prix returns all zeros."""
        result = calculate_rentabilite(
            prix_acquisition=None,
            loyer_mensuel=1_000,
        )
        _assert_zero_guard(result)

    def test_negative_prix_acquisition(self):
        """Negative prix returns all zeros."""
        result = calculate_rentabilite(
            prix_acquisition=-100_000,
            loyer_mensuel=1_000,
        )
        _assert_zero_guard(result)

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


# ---------------------------------------------------------------------------
# New tests — taxe_fonciere, IR, prélèvements sociaux
# ---------------------------------------------------------------------------


class TestTaxeFonciere:
    """Taxe foncière reduces nette and cashflow exactly like other annual charges."""

    def test_taxe_fonciere_reduces_nette(self):
        """Taxe foncière included in charges_annuelles."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            taxe_fonciere=1_200,
        )
        # charges_annuelles = 0 + 0 + 0 + 1200 = 1200
        # nette = ((12000 - 1200) / 200000) * 100 = 5.4
        assert result["nette"] == 5.4

    def test_taxe_fonciere_reduces_cashflow(self):
        """Taxe foncière is spread over 12 months for cashflow."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            taxe_fonciere=1_200,
        )
        # cashflow_mensuel = 1000 - 0 - 0 - 0 - 100 = 900
        assert result["cashflow_mensuel"] == 900.0
        assert result["cashflow_annuel"] == 10_800.0

    def test_taxe_fonciere_field_returned(self):
        """taxe_fonciere is echoed back in the result."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            taxe_fonciere=800,
        )
        assert result["taxe_fonciere"] == 800

    def test_taxe_fonciere_zero_by_default(self):
        """Default taxe_fonciere=0 does not change existing calculations."""
        result_without = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
        )
        result_with_zero = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            taxe_fonciere=0,
        )
        assert result_without["nette"] == result_with_zero["nette"]
        assert result_without["cashflow_mensuel"] == result_with_zero["cashflow_mensuel"]


class TestPrelevementsSociaux:
    """Prélèvements sociaux = 17.2% on positive net foncier income."""

    def test_prelevements_sociaux_positive_net(self):
        """PS = 17.2% of positive net foncier."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
        )
        # revenu_net = 12000 (no charges)
        expected_ps = round(12_000 * PRELEVEMENTS_SOCIAUX_RATE, 2)
        assert result["prelevements_sociaux"] == expected_ps

    def test_prelevements_sociaux_zero_when_net_negative(self):
        """No PS when revenu net is negative (no tax on a deficit)."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=500,
            charges_mensuelles=800,  # net = 6000 - 9600 = -3600
        )
        assert result["prelevements_sociaux"] == 0.0

    def test_prelevements_sociaux_rate(self):
        """PS uses the constant PRELEVEMENTS_SOCIAUX_RATE (17.2%)."""
        assert PRELEVEMENTS_SOCIAUX_RATE == 0.172


class TestImpotRevenuFoncier:
    """IR foncier = tmi% of positive net foncier income."""

    def test_ir_with_tmi_30(self):
        """IR = 30% of net foncier at TMI 30."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            tmi=30,
        )
        # revenu_net = 12000
        expected_ir = round(12_000 * 0.30, 2)
        assert result["impot_revenu_foncier"] == expected_ir

    def test_ir_zero_when_tmi_zero(self):
        """No IR when TMI is 0 (default)."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
        )
        assert result["impot_revenu_foncier"] == 0.0

    def test_ir_zero_when_net_negative(self):
        """No IR when net foncier is negative."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=500,
            charges_mensuelles=800,
            tmi=41,
        )
        assert result["impot_revenu_foncier"] == 0.0


class TestNettNette:
    """Rentabilité nette-nette = after deducting PS + IR from net foncier."""

    def test_nette_nette_no_tax(self):
        """With tmi=0 and no PS on zero net, nette_nette == nette when no charges."""
        # No charges → revenu_net = 12000, PS = 2064, IR = 0
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            tmi=0,
        )
        ps = 12_000 * PRELEVEMENTS_SOCIAUX_RATE
        revenu_apres = 12_000 - ps
        expected = round((revenu_apres / 200_000) * 100, 2)
        assert result["nette_nette"] == expected

    def test_nette_nette_with_tmi_30(self):
        """nette_nette correctly combines PS + IR deductions."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            charges_mensuelles=100,
            taxe_fonciere=600,
            tmi=30,
        )
        # charges_annuelles = 1200 + 600 = 1800
        # revenu_net = 12000 - 1800 = 10200
        revenu_net = 10_200
        ps = revenu_net * PRELEVEMENTS_SOCIAUX_RATE
        ir = revenu_net * 0.30
        revenu_apres = revenu_net - ps - ir
        expected = round((revenu_apres / 200_000) * 100, 2)
        assert result["nette_nette"] == expected

    def test_nette_nette_negative_when_high_charges(self):
        """nette_nette can be negative; no PS/IR are applied on deficit."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=500,
            charges_mensuelles=800,  # net = -3600
            tmi=30,
        )
        # revenu_net = -3600, so PS and IR are 0
        # nette_nette == nette
        assert result["nette_nette"] == result["nette"]
        assert result["prelevements_sociaux"] == 0.0
        assert result["impot_revenu_foncier"] == 0.0

    def test_nette_nette_less_than_nette(self):
        """nette_nette is always ≤ nette when net is positive."""
        result = calculate_rentabilite(
            prix_acquisition=200_000,
            loyer_mensuel=1_000,
            tmi=14,
        )
        assert result["nette_nette"] <= result["nette"]

    def test_full_scenario(self):
        """Full realistic scenario: all inputs combined."""
        result = calculate_rentabilite(
            prix_acquisition=300_000,
            loyer_mensuel=1_200,
            charges_mensuelles=150,
            prime_pno_annuelle=480,
            frais_agence_annuel=720,
            taxe_fonciere=900,
            tmi=30,
        )
        loyer_annuel = 14_400
        charges_annuelles = (150 * 12) + 480 + 720 + 900  # 3900
        revenu_net = loyer_annuel - charges_annuelles  # 10500
        ps = round(revenu_net * PRELEVEMENTS_SOCIAUX_RATE, 2)
        ir = round(revenu_net * 0.30, 2)
        revenu_apres = revenu_net - ps - ir
        expected_nette_nette = round((revenu_apres / 300_000) * 100, 2)

        assert result["brute"] == round((loyer_annuel / 300_000) * 100, 2)
        assert result["nette"] == round((revenu_net / 300_000) * 100, 2)
        assert result["nette_nette"] == expected_nette_nette
        assert result["prelevements_sociaux"] == ps
        assert result["impot_revenu_foncier"] == ir
        assert result["taxe_fonciere"] == 900


class TestNewFieldsAlwaysPresent:
    """New fields are present in every return path, including guard path."""

    def test_zero_guard_has_new_fields(self):
        """Zero-guard path returns all new keys with zero values."""
        result = calculate_rentabilite(prix_acquisition=0, loyer_mensuel=1_000)
        assert "nette_nette" in result
        assert "prelevements_sociaux" in result
        assert "impot_revenu_foncier" in result
        assert "taxe_fonciere" in result

    def test_normal_path_has_new_fields(self):
        """Normal calculation path includes all new keys."""
        result = calculate_rentabilite(prix_acquisition=200_000, loyer_mensuel=1_000)
        for key in ("nette_nette", "prelevements_sociaux", "impot_revenu_foncier", "taxe_fonciere"):
            assert key in result, f"Missing key: {key}"
