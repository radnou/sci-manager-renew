from reportlab.pdfgen import canvas
from io import BytesIO


def generate_quitus_pdf(text: str = "Quittus") -> bytes:
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, text)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()
