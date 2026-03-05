from app.models.quitus import QuitusRequest
from app.services.quitus_service import QuitusService


def test_generate_quitus_pdf():
    payload = QuitusRequest(
        id_loyer="loyer-2",
        id_bien="bien-2",
        nom_locataire="Alice Martin",
        periode="Fevrier 2026",
        montant=980.0,
        nom_sci="SCI Horizon Lyon",
        adresse_bien="42 avenue QA",
        ville_bien="Lyon",
    )
    pdf = QuitusService.generate_quitus_pdf(payload)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert b"SCI Horizon Lyon" in pdf
    assert b"Alice Martin" in pdf
    assert b"42 avenue QA, Lyon" in pdf
    assert b"loyer-2" not in pdf
    assert b"bien-2" not in pdf
