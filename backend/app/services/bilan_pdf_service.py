"""PDF generation for monthly bilans using ReportLab.

Follows the same font/color patterns as quitus_service.py.
"""

from __future__ import annotations

import os
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Font registration (same pattern as quitus_service)
# ---------------------------------------------------------------------------

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
    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"

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

    if font_name == "Helvetica":
        import reportlab as _rl

        rl_fonts_dir = os.path.join(os.path.dirname(_rl.__file__), "fonts")
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


_FONT, _FONT_BOLD = _register_fonts()

# Color palette (matching quitus_service)
_DARK = HexColor("#0f172a")
_LIGHT = HexColor("#f8fafc")
_GRAY = HexColor("#475569")
_BORDER = HexColor("#cbd5e1")
_ACCENT = HexColor("#1e40af")
_GREEN = HexColor("#166534")
_RED = HexColor("#991b1b")

_MONTH_NAMES = [
    "", "Janvier", "F\u00e9vrier", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Ao\u00fbt", "Septembre", "Octobre", "Novembre", "D\u00e9cembre",
]


def _fmt_eur(amount: float) -> str:
    """Format as French currency."""
    return f"{amount:,.2f} EUR".replace(",", " ").replace(".", ",").replace(" ", " ")


def _periode_label(periode: str) -> str:
    """Convert '2026-03' to 'Mars 2026'."""
    try:
        year, month = int(periode[:4]), int(periode[5:7])
        return f"{_MONTH_NAMES[month]} {year}"
    except (ValueError, IndexError):
        return periode


# ---------------------------------------------------------------------------
# PDF Generation
# ---------------------------------------------------------------------------


def generate_bilan_pdf(
    bilan_data: dict,
    scope: str = "portefeuille",
    scope_id: str | None = None,
) -> bytes:
    """Generate a monthly bilan PDF.

    Args:
        bilan_data: The full bilan data dict (from generate_bilan_mensuel or cache).
        scope: "portefeuille" | "sci" | "bien".
        scope_id: UUID of SCI or bien for scoped views.

    Returns:
        PDF bytes.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    width, height = A4

    periode = bilan_data.get("periode", "")
    mois_label = _periode_label(periode)

    # Determine scope label
    if scope == "sci" and "sci" in bilan_data:
        scope_label = bilan_data["sci"].get("sci_nom", "SCI")
    elif scope == "bien" and "bien" in bilan_data:
        b = bilan_data["bien"]
        scope_label = f"{b.get('adresse', '')} {b.get('ville', '')}".strip() or "Bien"
    else:
        scope_label = "Portefeuille"

    pdf.setTitle(f"Bilan Mensuel {mois_label}")
    pdf.setAuthor("G\u00e9rerSCI")
    pdf.setSubject("Bilan Mensuel")

    # ── HEADER ──
    header_h = 80
    pdf.setFillColor(_DARK)
    pdf.rect(0, height - header_h, width, header_h, stroke=0, fill=1)

    y = height - 30
    pdf.setFillColor(_LIGHT)
    pdf.setFont(_FONT_BOLD, 16)
    pdf.drawString(40, y, f"Bilan Mensuel \u2014 {mois_label}")
    y -= 20
    pdf.setFont(_FONT, 10)
    pdf.drawString(40, y, scope_label)

    # Right side: generation date
    right_x = width - 40
    pdf.setFont(_FONT, 8)
    generated = bilan_data.get("generated_at", "")[:10]
    pdf.drawRightString(right_x, height - 30, f"G\u00e9n\u00e9r\u00e9 le {generated}")

    # ── SUMMARY BOX ──
    y = height - header_h - 30
    summary = _get_summary(bilan_data, scope)

    pdf.setFillColor(_DARK)
    pdf.setFont(_FONT_BOLD, 12)
    pdf.drawString(40, y, "R\u00e9sum\u00e9")
    y -= 20

    summary_items = [
        ("Revenus attendus", summary.get("revenus_attendus", 0)),
        ("Revenus encaiss\u00e9s", summary.get("revenus_encaisses", 0)),
        ("Impay\u00e9s", summary.get("impayes", 0)),
        ("Charges", summary.get("charges", 0)),
        ("Cashflow net", summary.get("cashflow_net", 0)),
    ]

    row_h = 22
    table_left = 40
    table_right = width - 40
    table_width = table_right - table_left

    for label, amount in summary_items:
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFont(_FONT, 10)
        pdf.setFillColor(_DARK)
        pdf.drawString(table_left + 10, y - 15, label)

        # Color negative values red, positive green
        if amount < 0:
            pdf.setFillColor(_RED)
        elif amount > 0 and label == "Cashflow net":
            pdf.setFillColor(_GREEN)
        else:
            pdf.setFillColor(_DARK)
        pdf.drawRightString(table_right - 10, y - 15, _fmt_eur(amount))
        y -= row_h

    # Taux de recouvrement
    taux = summary.get("taux_recouvrement", 0)
    pdf.setStrokeColor(_BORDER)
    pdf.setFillColor(HexColor("#f1f5f9"))
    pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=1)
    pdf.setFont(_FONT_BOLD, 10)
    pdf.setFillColor(_DARK)
    pdf.drawString(table_left + 10, y - 15, "Taux de recouvrement")
    pdf.drawRightString(table_right - 10, y - 15, f"{taux:.1f} %")
    y -= row_h

    # ── GRAND LIVRE SIMPLIFIE ──
    y -= 25
    pdf.setFillColor(_DARK)
    pdf.setFont(_FONT_BOLD, 12)
    pdf.drawString(40, y, "Grand Livre Simplifi\u00e9")
    y -= 5

    # Get all entries (loyers as entries, charges as sorties)
    entries = _build_ledger_entries(bilan_data, scope, scope_id)

    if entries:
        y -= 15
        # Table header
        col_date_w = 70
        col_label_w = table_width - col_date_w - 80 - 80 - 70
        col_entree_w = 80
        col_sortie_w = 80
        col_solde_w = 70

        pdf.setFillColor(HexColor("#f1f5f9"))
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFont(_FONT_BOLD, 8)
        pdf.setFillColor(_DARK)

        x = table_left + 5
        pdf.drawString(x, y - 15, "Date")
        x += col_date_w
        pdf.drawString(x, y - 15, "Libell\u00e9")
        x += col_label_w
        pdf.drawRightString(x + col_entree_w - 5, y - 15, "Entr\u00e9es")
        x += col_entree_w
        pdf.drawRightString(x + col_sortie_w - 5, y - 15, "Sorties")
        x += col_sortie_w
        pdf.drawRightString(x + col_solde_w - 5, y - 15, "Solde")
        y -= row_h

        solde_cumul = 0.0
        pdf.setFont(_FONT, 8)

        for entry in entries:
            # Check page break
            if y - row_h < 80:
                _draw_footer(pdf, width)
                pdf.showPage()
                y = height - 40
                pdf.setFont(_FONT, 8)

            entree = entry.get("entree", 0)
            sortie = entry.get("sortie", 0)
            solde_cumul += entree - sortie

            pdf.setStrokeColor(_BORDER)
            pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
            pdf.setFillColor(_DARK)

            x = table_left + 5
            pdf.drawString(x, y - 15, entry.get("date", "")[:10])
            x += col_date_w

            label = entry.get("label", "")
            # Truncate long labels
            if len(label) > 40:
                label = label[:37] + "..."
            pdf.drawString(x, y - 15, label)
            x += col_label_w

            if entree > 0:
                pdf.setFillColor(_GREEN)
                pdf.drawRightString(x + col_entree_w - 5, y - 15, _fmt_eur(entree))
            pdf.setFillColor(_DARK)
            x += col_entree_w

            if sortie > 0:
                pdf.setFillColor(_RED)
                pdf.drawRightString(x + col_sortie_w - 5, y - 15, _fmt_eur(sortie))
            pdf.setFillColor(_DARK)
            x += col_sortie_w

            if solde_cumul < 0:
                pdf.setFillColor(_RED)
            else:
                pdf.setFillColor(_DARK)
            pdf.drawRightString(x + col_solde_w - 5, y - 15, _fmt_eur(solde_cumul))
            pdf.setFillColor(_DARK)
            y -= row_h

        # Total row
        if y - row_h < 80:
            _draw_footer(pdf, width)
            pdf.showPage()
            y = height - 40

        total_entrees = sum(e.get("entree", 0) for e in entries)
        total_sorties = sum(e.get("sortie", 0) for e in entries)

        pdf.setFillColor(HexColor("#e2e8f0"))
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(_BORDER)
        pdf.rect(table_left, y - row_h, table_width, row_h, stroke=1, fill=0)
        pdf.setFont(_FONT_BOLD, 8)
        pdf.setFillColor(_DARK)

        x = table_left + 5
        pdf.drawString(x, y - 15, "TOTAL")
        x += col_date_w + col_label_w
        pdf.setFillColor(_GREEN)
        pdf.drawRightString(x + col_entree_w - 5, y - 15, _fmt_eur(total_entrees))
        x += col_entree_w
        pdf.setFillColor(_RED)
        pdf.drawRightString(x + col_sortie_w - 5, y - 15, _fmt_eur(total_sorties))
        x += col_sortie_w
        color = _GREEN if solde_cumul >= 0 else _RED
        pdf.setFillColor(color)
        pdf.drawRightString(x + col_solde_w - 5, y - 15, _fmt_eur(solde_cumul))
        y -= row_h

    _draw_footer(pdf, width)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_summary(bilan_data: dict, scope: str) -> dict:
    """Extract summary numbers from bilan_data based on scope."""
    if scope == "sci" and "sci" in bilan_data:
        s = bilan_data["sci"]
        return {
            "revenus_attendus": s.get("revenus_attendus", 0),
            "revenus_encaisses": s.get("revenus_encaisses", 0),
            "impayes": s.get("impayes", 0),
            "charges": s.get("charges", 0),
            "cashflow_net": s.get("cashflow_net", 0),
            "taux_recouvrement": s.get("taux_recouvrement", 0),
        }
    if scope == "bien" and "bien" in bilan_data:
        b = bilan_data["bien"]
        rev = b.get("revenus_attendus", 0)
        enc = b.get("revenus_encaisses", 0)
        return {
            "revenus_attendus": rev,
            "revenus_encaisses": enc,
            "impayes": b.get("impayes", 0),
            "charges": b.get("charges", 0),
            "cashflow_net": b.get("cashflow_net", 0),
            "taux_recouvrement": (enc / rev * 100) if rev > 0 else 0,
        }
    # Default: portefeuille
    p = bilan_data.get("portefeuille", {})
    return {
        "revenus_attendus": p.get("revenus_attendus", 0),
        "revenus_encaisses": p.get("revenus_encaisses", 0),
        "impayes": p.get("impayes", 0),
        "charges": p.get("charges", 0),
        "cashflow_net": p.get("cashflow_net", 0),
        "taux_recouvrement": p.get("taux_recouvrement", 0),
    }


def _build_ledger_entries(bilan_data: dict, scope: str, scope_id: str | None) -> list[dict]:
    """Build sorted ledger entries from bilan data."""
    entries: list[dict] = []

    biens_list = _get_biens_list(bilan_data, scope, scope_id)

    for bien in biens_list:
        adresse = bien.get("adresse", "")
        ville = bien.get("ville", "")
        loc_label = f"{adresse}, {ville}".strip(", ") if adresse else "Bien"

        for loyer in bien.get("loyers", []):
            locataire = loyer.get("locataire", "")
            label = f"Loyer {loc_label}"
            if locataire:
                label = f"Loyer {locataire} \u2014 {loc_label}"
            statut = loyer.get("statut", "")
            montant = loyer.get("montant", 0)
            # Only encaissements are entries
            if statut in ("paye", "paid"):
                entries.append({
                    "date": loyer.get("date", ""),
                    "label": label,
                    "entree": montant,
                    "sortie": 0,
                })
            else:
                # Show impaye as zero entry for visibility
                entries.append({
                    "date": loyer.get("date", ""),
                    "label": f"[IMPAY\u00c9] {label}",
                    "entree": 0,
                    "sortie": 0,
                })

        for charge in bien.get("charges_detail", []):
            type_charge = charge.get("type", "Charge")
            entries.append({
                "date": charge.get("date", ""),
                "label": f"{type_charge} \u2014 {loc_label}",
                "entree": 0,
                "sortie": charge.get("montant", 0),
            })

    # Sort by date
    entries.sort(key=lambda e: e.get("date", ""))
    return entries


def _get_biens_list(bilan_data: dict, scope: str, scope_id: str | None) -> list[dict]:
    """Extract the relevant biens list from bilan_data."""
    if scope == "bien" and "bien" in bilan_data:
        return [bilan_data["bien"]]
    if scope == "sci" and "sci" in bilan_data:
        return bilan_data["sci"].get("biens", [])
    # Portefeuille: all biens across all SCIs
    biens = []
    for sci in bilan_data.get("scis", []):
        biens.extend(sci.get("biens", []))
    return biens


def _draw_footer(pdf, width: float) -> None:
    """Draw branding footer at bottom of page."""
    pdf.setFont(_FONT, 6)
    pdf.setFillColor(HexColor("#94a3b8"))
    pdf.drawCentredString(width / 2, 30, "G\u00e9n\u00e9r\u00e9 par G\u00e9rerSCI (gerersci.fr)")
