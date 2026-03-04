from app.services.sci_service import SCIService


def test_calculate_rentabilite():
    result = SCIService.calculate_rentabilite(
        {
            "loyer_cc": 1500,
            "prix_acquisition": 300000,
            "charges": 200,
        }
    )
    assert result["rentabilite_brute"] == 6.0
    assert result["rentabilite_nette"] == 5.2
    assert result["cashflow_annuel"] == 15600.0


def test_calculate_rentabilite_without_price():
    result = SCIService.calculate_rentabilite({"loyer_cc": 900, "charges": 100})
    assert result["rentabilite_brute"] == 0
    assert result["rentabilite_nette"] == 0
    assert result["cashflow_annuel"] == 9600.0
