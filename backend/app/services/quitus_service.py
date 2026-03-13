import os
from datetime import date
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models.quitus import QuitusRequest

# Register DejaVu Sans for proper accent support in PDFs.
# Fall back to Helvetica if the font file is not available.
_FONT_NAME = "Helvetica"
_FONT_NAME_BOLD = "Helvetica-Bold"

_DEJAVU_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
_DEJAVU_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]

for _path in _DEJAVU_PATHS:
    if os.path.isfile(_path):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", _path))
            _FONT_NAME = "DejaVuSans"
        except Exception:
            pass
        break

for _path in _DEJAVU_BOLD_PATHS:
    if os.path.isfile(_path):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _path))
            _FONT_NAME_BOLD = "DejaVuSans-Bold"
        except Exception:
            pass
        break


class QuitusService:
    @staticmethod
    def _build_property_label(quitus: QuitusRequest) -> str:
        if quitus.adresse_bien and quitus.ville_bien:
            return f"{quitus.adresse_bien}, {quitus.ville_bien}"
        if quitus.adresse_bien:
            return quitus.adresse_bien
        if quitus.ville_bien:
            return f"Bien situé à {quitus.ville_bien}"
        return "Bien rattaché à la SCI"

    @staticmethod
    def generate_quitus_pdf(quitus: QuitusRequest) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
        width, height = A4
        issuer = quitus.nom_sci or "SCI à confirmer"
        property_label = QuitusService._build_property_label(quitus)
        amount_label = f"{quitus.montant:.2f} EUR"
        issue_date = date.today().strftime("%d/%m/%Y")

        pdf.setTitle(f"Quittance {quitus.periode}")
        pdf.setAuthor(issuer)
        pdf.setSubject("Quittance de loyer")

        pdf.setFillColor(HexColor("#0f172a"))
        pdf.rect(0, height - 96, width, 96, stroke=0, fill=1)
        pdf.setFillColor(HexColor("#f8fafc"))
        pdf.setFont(_FONT_NAME_BOLD, 12)
        pdf.drawString(56, height - 42, issuer)
        pdf.setFont(_FONT_NAME_BOLD, 24)
        pdf.drawString(56, height - 74, "Quittance de loyer")

        pdf.setFillColor(HexColor("#0f172a"))
        pdf.setFont(_FONT_NAME, 11)
        pdf.drawString(56, height - 128, f"Locataire : {quitus.nom_locataire}")
        pdf.drawString(56, height - 146, f"Période : {quitus.periode}")
        pdf.drawString(56, height - 164, f"Bien : {property_label}")

        pdf.setStrokeColor(HexColor("#cbd5e1"))
        pdf.setFillColor(HexColor("#f8fafc"))
        pdf.roundRect(56, height - 278, width - 112, 88, 12, stroke=1, fill=1)
        pdf.setFillColor(HexColor("#475569"))
        pdf.setFont(_FONT_NAME_BOLD, 10)
        pdf.drawString(76, height - 214, "Montant acquitté")
        pdf.setFillColor(HexColor("#0f172a"))
        pdf.setFont(_FONT_NAME_BOLD, 22)
        pdf.drawString(76, height - 246, amount_label)

        pdf.setFont(_FONT_NAME, 11)
        text = pdf.beginText(56, height - 324)
        text.setLeading(18)
        text.textLine(
            f"Nous attestons avoir reçu de {quitus.nom_locataire} la somme de {amount_label}"
        )
        text.textLine(
            f"au titre du loyer et des charges de la période {quitus.periode}."
        )
        text.textLine(f"Le paiement concerne le bien situé {property_label}.")
        text.textLine("")
        text.textLine(f"Document établi le {issue_date} pour justificatif.")
        pdf.drawText(text)

        pdf.setStrokeColor(HexColor("#94a3b8"))
        pdf.line(56, 164, 236, 164)
        pdf.setFont(_FONT_NAME, 10)
        pdf.drawString(56, 148, "Signature / cachet")
        pdf.drawRightString(width - 56, 148, issuer)

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.read()
