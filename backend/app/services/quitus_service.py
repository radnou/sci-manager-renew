from datetime import date
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.quitus import QuitusRequest


class QuitusService:
    @staticmethod
    def _build_property_label(quitus: QuitusRequest) -> str:
        if quitus.adresse_bien and quitus.ville_bien:
            return f"{quitus.adresse_bien}, {quitus.ville_bien}"
        if quitus.adresse_bien:
            return quitus.adresse_bien
        if quitus.ville_bien:
            return f"Bien situe a {quitus.ville_bien}"
        return "Bien rattache a la SCI"

    @staticmethod
    def generate_quitus_pdf(quitus: QuitusRequest) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
        width, height = A4
        issuer = quitus.nom_sci or "SCI a confirmer"
        property_label = QuitusService._build_property_label(quitus)
        amount_label = f"{quitus.montant:.2f} EUR"
        issue_date = date.today().strftime("%d/%m/%Y")

        pdf.setTitle(f"Quittance {quitus.periode}")
        pdf.setAuthor(issuer)
        pdf.setSubject("Quittance de loyer")

        pdf.setFillColor(HexColor("#0f172a"))
        pdf.rect(0, height - 96, width, 96, stroke=0, fill=1)
        pdf.setFillColor(HexColor("#f8fafc"))
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(56, height - 42, issuer)
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawString(56, height - 74, "Quittance de loyer")

        pdf.setFillColor(HexColor("#0f172a"))
        pdf.setFont("Helvetica", 11)
        pdf.drawString(56, height - 128, f"Locataire : {quitus.nom_locataire}")
        pdf.drawString(56, height - 146, f"Periode : {quitus.periode}")
        pdf.drawString(56, height - 164, f"Bien : {property_label}")

        pdf.setStrokeColor(HexColor("#cbd5e1"))
        pdf.setFillColor(HexColor("#f8fafc"))
        pdf.roundRect(56, height - 278, width - 112, 88, 12, stroke=1, fill=1)
        pdf.setFillColor(HexColor("#475569"))
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(76, height - 214, "Montant acquitte")
        pdf.setFillColor(HexColor("#0f172a"))
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(76, height - 246, amount_label)

        pdf.setFont("Helvetica", 11)
        text = pdf.beginText(56, height - 324)
        text.setLeading(18)
        text.textLine(
            f"Nous attestons avoir recu de {quitus.nom_locataire} la somme de {amount_label}"
        )
        text.textLine(
            f"au titre du loyer et des charges de la periode {quitus.periode}."
        )
        text.textLine(f"Le paiement concerne le bien situe {property_label}.")
        text.textLine("")
        text.textLine(f"Document etabli le {issue_date} pour justificatif.")
        pdf.drawText(text)

        pdf.setStrokeColor(HexColor("#94a3b8"))
        pdf.line(56, 164, 236, 164)
        pdf.setFont("Helvetica", 10)
        pdf.drawString(56, 148, "Signature / cachet")
        pdf.drawRightString(width - 56, 148, issuer)

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.read()
