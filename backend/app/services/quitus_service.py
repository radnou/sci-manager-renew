import os
from datetime import date
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models.quitus import PublicQuitusRequest, QuitusRequest

# Register a TTF font with Latin-1 support for French accented characters.
# Priority: DejaVu Sans (system) > Bitstream Vera (bundled with reportlab) > Helvetica.
# Helvetica (Type 1) cannot render UTF-8 accents; Vera/DejaVu TTF fonts can.

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


def _register_fonts() -> tuple[str, str]:
    """Register a TTF font that supports accented characters and return (name, bold_name)."""
    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"

    # Try DejaVu Sans first (best Unicode coverage, common on Linux/Docker).
    for path in _DEJAVU_PATHS:
        if os.path.isfile(path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                font_name = "DejaVuSans"
            except Exception:
                pass
            break

    for path in _DEJAVU_BOLD_PATHS:
        if os.path.isfile(path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", path))
                font_bold = "DejaVuSans-Bold"
            except Exception:
                pass
            break

    # If DejaVu not found, use Bitstream Vera bundled with reportlab (always available).
    if font_name == "Helvetica":
        import reportlab

        rl_fonts_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        vera_path = os.path.join(rl_fonts_dir, "Vera.ttf")
        vera_bold_path = os.path.join(rl_fonts_dir, "VeraBd.ttf")

        if os.path.isfile(vera_path):
            try:
                pdfmetrics.registerFont(TTFont("Vera", vera_path))
                font_name = "Vera"
            except Exception:
                pass

        if os.path.isfile(vera_bold_path):
            try:
                pdfmetrics.registerFont(TTFont("VeraBd", vera_bold_path))
                font_bold = "VeraBd"
            except Exception:
                pass

    return font_name, font_bold


_FONT_NAME, _FONT_NAME_BOLD = _register_fonts()

# Color palette
_DARK = HexColor("#0f172a")
_LIGHT = HexColor("#f8fafc")
_GRAY = HexColor("#475569")
_BORDER = HexColor("#cbd5e1")
_ACCENT = HexColor("#1e40af")


def _fmt_eur(amount: float) -> str:
    """Format a number as French currency: 1 234,56 EUR."""
    return f"{amount:,.2f} EUR".replace(",", " ").replace(".", ",").replace(" ", " ")


def _fmt_date_fr(d: date) -> str:
    """Format a date as dd/mm/yyyy."""
    return d.strftime("%d/%m/%Y")


def get_next_quittance_number(
    supabase_client, sci_id: str, loyer_date: date
) -> str:
    """Generate sequential quittance number: QTT-{AAAAMM}-{NNN}.

    Increments quittance_compteur atomically per SCI per month.
    Falls back to a timestamp-based number if DB operations fail.
    """
    annee_mois = loyer_date.strftime("%Y%m")

    try:
        # Call the RPC function atomically
        result = supabase_client.rpc(
            "increment_quittance_counter",
            {"p_sci_id": sci_id, "p_annee_mois": annee_mois}
        ).execute()
        nouveau = result.data
        if nouveau is None:
            raise Exception("RPC returned null")
        return f"QTT-{annee_mois}-{nouveau:03d}"
    except Exception:
        # Fallback: timestamp-based number (never blocks PDF generation)
        import time
        return f"QTT-{annee_mois}-{int(time.time()) % 10000:04d}"


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
    def generate_quitus_pdf(
        quitus: QuitusRequest,
        sci_data: dict | None = None,
        bail_data: dict | None = None,
        locataires: list[dict] | None = None,
        quittance_numero: str | None = None,
    ) -> bytes:
        """Generate a legally compliant quittance PDF.

        Args:
            quitus: Base quittance request with loyer/bien/locataire info
            sci_data: SCI row from DB (nom, capital_social, rcs_ville, rcs_numero,
                      forme_juridique, nom_gerant, adresse_siege)
            bail_data: Bail row (loyer_hc, charges_locatives)
            locataires: List of locataire dicts (nom, prenom)
            quittance_numero: Sequential number (e.g. QTT-202603-001)
        """
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
        width, height = A4

        # ── Resolve data from sci_data or fallback to quitus fields ──
        sci = sci_data or {}
        issuer = sci.get("nom") or quitus.nom_sci or "SCI à confirmer"
        forme_juridique = sci.get("forme_juridique") or "SCI"
        capital_social = sci.get("capital_social")
        rcs_ville = sci.get("rcs_ville")
        rcs_numero = sci.get("rcs_numero")
        siege = sci.get("adresse_siege") or ""
        nom_gerant = sci.get("nom_gerant") or ""

        # Bail decomposition (prefer bail_data over quitus fields)
        bail = bail_data or {}
        loyer_hc = bail.get("loyer_hc") or quitus.loyer_hc
        charges_provisions = bail.get("charges_locatives") or quitus.charges_locatives
        total_du = loyer_hc + charges_provisions
        total_verse = quitus.montant
        reste_du = max(0, round(total_du - total_verse, 2))
        is_partial = reste_du > 0.005  # tolerance for float rounding

        # Locataire names
        if locataires:
            nom_locataire = ", ".join(
                f"{loc.get('prenom', '')} {loc.get('nom', '')}".strip() or loc.get("nom", "")
                for loc in locataires
            ) or quitus.nom_locataire
        else:
            nom_locataire = quitus.nom_locataire

        property_label = QuitusService._build_property_label(quitus)
        issue_date = date.today()
        issue_date_str = _fmt_date_fr(issue_date)

        # Determine document title
        doc_title = "REÇU DE PAIEMENT" if is_partial else "QUITTANCE DE LOYER"

        pdf.setTitle(f"Quittance {quitus.periode}")
        pdf.setAuthor(issuer)
        pdf.setSubject(doc_title)

        # ─────────────────────────────────────────────────────────
        # HEADER: Two-column layout
        # ─────────────────────────────────────────────────────────
        header_h = 100
        pdf.setFillColor(_DARK)
        pdf.rect(0, height - header_h, width, header_h, stroke=0, fill=1)

        # Left column: SCI info
        y = height - 28
        pdf.setFillColor(_LIGHT)
        pdf.setFont(_FONT_NAME_BOLD, 13)
        # Avoid "SCI SCI Belleville" if name already starts with the forme juridique
        if issuer.upper().startswith(forme_juridique.upper()):
            header_label = issuer
        else:
            header_label = f"{forme_juridique} {issuer}"
        pdf.drawString(40, y, header_label)

        y -= 16
        pdf.setFont(_FONT_NAME, 8)
        info_parts: list[str] = []
        if capital_social is not None:
            info_parts.append(f"Capital : {_fmt_eur(capital_social)}")
        if rcs_ville:
            rcs_label = f"RCS {rcs_ville}"
            if rcs_numero:
                rcs_label += f" {rcs_numero}"
            info_parts.append(rcs_label)
        if info_parts:
            pdf.drawString(40, y, " — ".join(info_parts))
            y -= 13

        if siege:
            pdf.drawString(40, y, f"Siège : {siege}")
            y -= 13

        if nom_gerant:
            pdf.drawString(40, y, f"Gérant : {nom_gerant}")

        # Right column: Document title + number + date
        right_x = width - 40
        y_right = height - 30
        pdf.setFont(_FONT_NAME_BOLD, 16)
        pdf.drawRightString(right_x, y_right, doc_title)

        y_right -= 18
        pdf.setFont(_FONT_NAME, 9)
        if quittance_numero:
            pdf.drawRightString(right_x, y_right, f"N° {quittance_numero}")
            y_right -= 14
        pdf.drawRightString(right_x, y_right, f"Émise le {issue_date_str}")

        # ─────────────────────────────────────────────────────────
        # LOCATAIRE + BIEN INFO
        # ─────────────────────────────────────────────────────────
        y = height - header_h - 30
        pdf.setFillColor(_DARK)
        pdf.setFont(_FONT_NAME, 11)
        pdf.drawString(40, y, f"Locataire : {nom_locataire}")
        y -= 18
        pdf.drawString(40, y, f"Bien : {property_label}")

        # ─────────────────────────────────────────────────────────
        # BODY: Financial breakdown table
        # ─────────────────────────────────────────────────────────
        y -= 35
        table_top = y
        table_left = 40
        table_right = width - 40
        table_width = table_right - table_left
        row_h = 24
        col_label_w = table_width * 0.65
        col_amount_w = table_width * 0.35

        # Table header
        pdf.setFillColor(HexColor("#f1f5f9"))
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFillColor(_DARK)
        pdf.setFont(_FONT_NAME_BOLD, 10)
        pdf.drawString(table_left + 10, y - 16, "Désignation")
        pdf.drawRightString(table_right - 10, y - 16, "Montant")
        y -= row_h

        # Période row
        periode_label = f"Période : {quitus.periode}"

        def _draw_row(label: str, amount: float, bold: bool = False) -> float:
            nonlocal y
            pdf.setStrokeColor(_BORDER)
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
            font = _FONT_NAME_BOLD if bold else _FONT_NAME
            pdf.setFont(font, 10)
            pdf.setFillColor(_DARK)
            pdf.drawString(table_left + 10, y - 16, label)
            pdf.drawRightString(table_right - 10, y - 16, _fmt_eur(amount))
            y -= row_h
            return y

        _draw_row(f"Loyer hors charges — {periode_label}", loyer_hc)
        _draw_row("Provision pour charges", charges_provisions)

        # Total dû row (highlighted)
        pdf.setFillColor(HexColor("#e2e8f0"))
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFont(_FONT_NAME_BOLD, 10)
        pdf.setFillColor(_DARK)
        pdf.drawString(table_left + 10, y - 16, "Total dû")
        pdf.drawRightString(table_right - 10, y - 16, _fmt_eur(total_du))
        y -= row_h

        # Total versé row
        _draw_row("Total versé", total_verse, bold=True)

        # Reste dû row (only if partial)
        if is_partial:
            pdf.setFillColor(HexColor("#fef2f2"))
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
            pdf.setStrokeColor(HexColor("#fca5a5"))
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
            pdf.setFont(_FONT_NAME_BOLD, 10)
            pdf.setFillColor(HexColor("#991b1b"))
            pdf.drawString(table_left + 10, y - 16, "Reste dû")
            pdf.drawRightString(table_right - 10, y - 16, _fmt_eur(reste_du))
            y -= row_h

        # ─────────────────────────────────────────────────────────
        # ATTESTATION TEXT
        # ─────────────────────────────────────────────────────────
        y -= 25
        pdf.setFont(_FONT_NAME, 10)
        pdf.setFillColor(_DARK)
        text = pdf.beginText(40, y)
        text.setLeading(16)

        if is_partial:
            text.textLine(
                f"Nous attestons avoir reçu de {nom_locataire} la somme de {_fmt_eur(total_verse)}"
            )
            text.textLine(
                f"au titre du loyer et des charges de la période {quitus.periode}."
            )
            text.textLine(
                f"Le solde restant dû s'élève à {_fmt_eur(reste_du)}."
            )
        else:
            text.textLine(
                f"Nous soussignés attestons avoir reçu de {nom_locataire} la somme de {_fmt_eur(total_verse)}"
            )
            text.textLine(
                f"au titre du loyer ({_fmt_eur(loyer_hc)}) et des charges locatives "
                f"({_fmt_eur(charges_provisions)}) pour la période {quitus.periode},"
            )
            text.textLine(
                f"et lui en donnons quittance, sous réserve de tous droits."
            )

        text.textLine(f"Le paiement concerne le bien situé {property_label}.")
        text.textLine("")
        text.textLine(f"Document établi le {issue_date_str}.")
        pdf.drawText(text)

        # ─────────────────────────────────────────────────────────
        # FOOTER: Signature + legal mentions
        # ─────────────────────────────────────────────────────────

        # Signature line
        sig_y = 170
        pdf.setStrokeColor(HexColor("#94a3b8"))
        pdf.line(40, sig_y, 220, sig_y)
        pdf.setFont(_FONT_NAME, 10)
        pdf.setFillColor(_DARK)
        sig_label = "Le gérant"
        if nom_gerant:
            sig_label = f"Le gérant, {nom_gerant}"
        pdf.drawString(40, sig_y - 16, sig_label)
        pdf.drawRightString(width - 40, sig_y - 16, issuer)

        # Legal mentions
        legal_y = 80
        pdf.setFont(_FONT_NAME, 7)
        pdf.setFillColor(_GRAY)
        pdf.drawString(
            40, legal_y,
            "Ce document est délivré conformément à l'article 21 de la loi n° 89-462 du 6 juillet 1989 "
            "et à l'article 1366 du Code civil.",
        )
        pdf.drawString(
            40, legal_y - 11,
            "Cette quittance ne libère l'occupant que pour la période et le montant indiqués.",
        )
        pdf.drawString(
            40, legal_y - 22,
            "Conservez ce document : il pourra être demandé pour justifier de domicile "
            "(article 3 du décret n° 2015-1437).",
        )

        # Branding
        pdf.setFont(_FONT_NAME, 6)
        pdf.setFillColor(HexColor("#94a3b8"))
        pdf.drawCentredString(width / 2, 30, "Généré par GérerSCI (gerersci.fr)")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def generate_public_quitus_pdf(payload: PublicQuitusRequest) -> bytes:
        """Generate a simple quittance PDF for the public (free) tool.

        No DB access, no storage — purely stateless PDF generation.
        """
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
        width, height = A4

        issuer = payload.nom_proprietaire
        nom_locataire = payload.nom_locataire
        property_label = payload.adresse_bien
        loyer_hc = payload.loyer_hc
        charges_provisions = payload.charges_locatives
        total_du = loyer_hc + charges_provisions
        total_verse = payload.montant_paye
        reste_du = max(0, round(total_du - total_verse, 2))
        is_partial = reste_du > 0.005

        # Parse payment date
        try:
            paiement_date = date.fromisoformat(payload.date_paiement)
        except ValueError:
            paiement_date = date.today()

        issue_date = date.today()
        issue_date_str = _fmt_date_fr(issue_date)
        doc_title = "REÇU DE PAIEMENT" if is_partial else "QUITTANCE DE LOYER"

        pdf.setTitle(f"Quittance {payload.periode}")
        pdf.setAuthor(issuer)
        pdf.setSubject(doc_title)

        # ── HEADER ──
        header_h = 100
        pdf.setFillColor(_DARK)
        pdf.rect(0, height - header_h, width, header_h, stroke=0, fill=1)

        y = height - 28
        pdf.setFillColor(_LIGHT)
        pdf.setFont(_FONT_NAME_BOLD, 13)
        pdf.drawString(40, y, issuer)

        # Right column
        right_x = width - 40
        y_right = height - 30
        pdf.setFont(_FONT_NAME_BOLD, 16)
        pdf.drawRightString(right_x, y_right, doc_title)
        y_right -= 18
        pdf.setFont(_FONT_NAME, 9)
        pdf.drawRightString(right_x, y_right, f"Émise le {issue_date_str}")

        # ── LOCATAIRE + BIEN ──
        y = height - header_h - 30
        pdf.setFillColor(_DARK)
        pdf.setFont(_FONT_NAME, 11)
        pdf.drawString(40, y, f"Locataire : {nom_locataire}")
        y -= 18
        pdf.drawString(40, y, f"Bien : {property_label}")

        # ── TABLE ──
        y -= 35
        table_left = 40
        table_right = width - 40
        table_width = table_right - table_left
        row_h = 24

        # Table header
        pdf.setFillColor(HexColor("#f1f5f9"))
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFillColor(_DARK)
        pdf.setFont(_FONT_NAME_BOLD, 10)
        pdf.drawString(table_left + 10, y - 16, "Désignation")
        pdf.drawRightString(table_right - 10, y - 16, "Montant")
        y -= row_h

        def _draw_row(label: str, amount: float, bold: bool = False) -> None:
            nonlocal y
            pdf.setStrokeColor(_BORDER)
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
            font = _FONT_NAME_BOLD if bold else _FONT_NAME
            pdf.setFont(font, 10)
            pdf.setFillColor(_DARK)
            pdf.drawString(table_left + 10, y - 16, label)
            pdf.drawRightString(table_right - 10, y - 16, _fmt_eur(amount))
            y -= row_h

        _draw_row(f"Loyer hors charges — Période : {payload.periode}", loyer_hc)
        _draw_row("Provision pour charges", charges_provisions)

        # Total dû
        pdf.setFillColor(HexColor("#e2e8f0"))
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFont(_FONT_NAME_BOLD, 10)
        pdf.setFillColor(_DARK)
        pdf.drawString(table_left + 10, y - 16, "Total dû")
        pdf.drawRightString(table_right - 10, y - 16, _fmt_eur(total_du))
        y -= row_h

        _draw_row("Total versé", total_verse, bold=True)

        if is_partial:
            pdf.setFillColor(HexColor("#fef2f2"))
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
            pdf.setStrokeColor(HexColor("#fca5a5"))
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
            pdf.setFont(_FONT_NAME_BOLD, 10)
            pdf.setFillColor(HexColor("#991b1b"))
            pdf.drawString(table_left + 10, y - 16, "Reste dû")
            pdf.drawRightString(table_right - 10, y - 16, _fmt_eur(reste_du))
            y -= row_h

        # ── ATTESTATION TEXT ──
        y -= 25
        pdf.setFont(_FONT_NAME, 10)
        pdf.setFillColor(_DARK)
        text = pdf.beginText(40, y)
        text.setLeading(16)

        if is_partial:
            text.textLine(
                f"Nous attestons avoir reçu de {nom_locataire} la somme de {_fmt_eur(total_verse)}"
            )
            text.textLine(
                f"au titre du loyer et des charges de la période {payload.periode}."
            )
            text.textLine(
                f"Le solde restant dû s'élève à {_fmt_eur(reste_du)}."
            )
        else:
            text.textLine(
                f"Nous soussignés attestons avoir reçu de {nom_locataire} la somme de {_fmt_eur(total_verse)}"
            )
            text.textLine(
                f"au titre du loyer ({_fmt_eur(loyer_hc)}) et des charges locatives "
                f"({_fmt_eur(charges_provisions)}) pour la période {payload.periode},"
            )
            text.textLine(
                "et lui en donnons quittance, sous réserve de tous droits."
            )

        text.textLine(f"Le paiement concerne le bien situé {property_label}.")
        mode_label = getattr(payload, "mode_paiement", None)
        if mode_label:
            text.textLine(f"Date de paiement : {_fmt_date_fr(paiement_date)} — Mode : {mode_label}.")
        else:
            text.textLine(f"Date de paiement : {_fmt_date_fr(paiement_date)}.")
        text.textLine("")
        text.textLine(f"Document établi le {issue_date_str}.")
        pdf.drawText(text)

        # ── SIGNATURE ──
        sig_y = 170
        pdf.setStrokeColor(HexColor("#94a3b8"))
        pdf.line(40, sig_y, 220, sig_y)
        pdf.setFont(_FONT_NAME, 10)
        pdf.setFillColor(_DARK)
        pdf.drawString(40, sig_y - 16, "Le bailleur")
        pdf.drawRightString(width - 40, sig_y - 16, issuer)

        # ── LEGAL FOOTER ──
        legal_y = 80
        pdf.setFont(_FONT_NAME, 7)
        pdf.setFillColor(_GRAY)
        pdf.drawString(
            40, legal_y,
            "Ce document est délivré conformément à l'article 21 de la loi n° 89-462 du 6 juillet 1989 "
            "et à l'article 1366 du Code civil.",
        )
        pdf.drawString(
            40, legal_y - 11,
            "Cette quittance ne libère l'occupant que pour la période et le montant indiqués.",
        )
        pdf.drawString(
            40, legal_y - 22,
            "Conservez ce document : il pourra être demandé pour justifier de domicile "
            "(article 3 du décret n° 2015-1437).",
        )

        # Branding
        pdf.setFont(_FONT_NAME, 6)
        pdf.setFillColor(HexColor("#94a3b8"))
        pdf.drawCentredString(width / 2, 30, "Généré par GérerSCI (gerersci.fr)")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.read()
