from fastapi import APIRouter, Response
from reportlab.pdfgen import canvas
from io import BytesIO

router = APIRouter()

@router.get("", response_class=Response)
def generate_quitus():
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Quittus de loyer")
    p.showPage()
    p.save()
    buffer.seek(0)
    return Response(content=buffer.read(), media_type="application/pdf")
