from app.models.quitus import QuitusRequest
from app.services.quitus_service import QuitusService


def test_generate_quitus_pdf():
    payload = QuitusRequest(
        id_loyer="loyer-2",
        id_bien="bien-2",
        nom_locataire="Alice Martin",
        periode="Fevrier 2026",
        montant=980.0,
    )
    pdf = QuitusService.generate_quitus_pdf(payload)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
