from app.services.quitus_service import generate_quitus_pdf


def test_generate_quitus_pdf():
    pdf = generate_quitus_pdf("Hello")
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
