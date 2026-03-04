from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.quitus import QuitusRequest


class QuitusService:
    @staticmethod
    def generate_quitus_pdf(quitus: QuitusRequest) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(72, 790, "Quittus de loyer")

        pdf.setFont("Helvetica", 11)
        pdf.drawString(72, 760, f"Locataire: {quitus.nom_locataire}")
        pdf.drawString(72, 742, f"Periode: {quitus.periode}")
        pdf.drawString(72, 724, f"Montant regle: {quitus.montant:.2f} EUR")
        pdf.drawString(72, 706, f"Bien: {quitus.id_bien}")
        pdf.drawString(72, 688, f"Loyer: {quitus.id_loyer}")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.read()
