from app.models.quitus import QuitusRequest
from app.services.quitus_service import QuitusService


def test_generate_quitus_pdf_backward_compat():
    payload = QuitusRequest(
        id_loyer="legacy-loyer",
        id_bien="legacy-bien",
        nom_locataire="Legacy",
        periode="Janvier 2026",
        montant=1000,
    )
    pdf = QuitusService.generate_quitus_pdf(payload)
    assert pdf.startswith(b"%PDF")
