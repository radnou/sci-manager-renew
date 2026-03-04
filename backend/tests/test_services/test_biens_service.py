from app.services.biens_service import calculate_rentabilite


def test_biens_service_wrapper():
    result = calculate_rentabilite(
        {
            "loyer_cc": 1200,
            "charges": 100,
            "prix_acquisition": 220000,
        }
    )
    assert result["rentabilite_brute"] > 0
