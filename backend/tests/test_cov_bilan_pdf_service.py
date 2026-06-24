"""Coverage tests for app/services/bilan_pdf_service.py.

Strategy: call generate_bilan_pdf() with realistic, complete bilan_data dicts
for the three scopes (portefeuille, sci, bien).  Multiple calls cover all
conditional branches (paid/impayé loyers, charges, page breaks, footer).
"""

from __future__ import annotations

from app.services.bilan_pdf_service import (
    generate_bilan_pdf,
    _fmt_eur,
    _periode_label,
    _get_summary,
    _build_ledger_entries,
    _get_biens_list,
    _register_fonts,
)

from unittest.mock import patch
import os


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_loyer(statut: str = "paye", montant: float = 1000.0, date: str = "2026-03-05") -> dict:
    return {"statut": statut, "montant": montant, "date": date, "locataire": "Jean Dupont"}


def _make_charge(type_charge: str = "Taxe foncière", montant: float = 800.0, date: str = "2026-03-10") -> dict:
    return {"type": type_charge, "montant": montant, "date": date}


def _make_bien(
    bien_id: str = "b1",
    adresse: str = "12 rue de la Paix",
    ville: str = "Paris",
    loyers: list | None = None,
    charges: list | None = None,
) -> dict:
    if loyers is None:
        loyers = [_make_loyer("paye", 1200.0), _make_loyer("impaye", 800.0, "2026-03-01")]
    if charges is None:
        charges = [_make_charge("Taxe foncière", 800.0), _make_charge("Copropriété", 300.0)]
    return {
        "id": bien_id,
        "adresse": adresse,
        "ville": ville,
        "revenus_attendus": 1200.0,
        "revenus_encaisses": 1200.0,
        "impayes": 800.0,
        "charges": 1100.0,
        "cashflow_net": 100.0,
        "loyers": loyers,
        "charges_detail": charges,
    }


def _make_sci_scope(
    sci_id: str = "sci-1",
    sci_nom: str = "SCI Lumière",
    biens: list | None = None,
) -> dict:
    if biens is None:
        biens = [_make_bien("b1", "12 rue de la Paix", "Paris"),
                 _make_bien("b2", "5 avenue de Lyon", "Lyon")]
    return {
        "id": sci_id,
        "sci_nom": sci_nom,
        "revenus_attendus": 2400.0,
        "revenus_encaisses": 2400.0,
        "impayes": 0.0,
        "charges": 1100.0,
        "cashflow_net": 1300.0,
        "taux_recouvrement": 100.0,
        "biens": biens,
    }


def _make_portefeuille_bilan() -> dict:
    """Full bilan_data for portefeuille scope."""
    bien = _make_bien()
    sci1 = _make_sci_scope("sci-1", "SCI Lumière", [bien])
    sci2 = _make_sci_scope("sci-2", "SCI Horizon", [_make_bien("b3", "99 bd Haussmann", "Paris")])
    return {
        "periode": "2026-03",
        "generated_at": "2026-03-31T23:59:00",
        "portefeuille": {
            "revenus_attendus": 2400.0,
            "revenus_encaisses": 2400.0,
            "impayes": 0.0,
            "charges": 1100.0,
            "cashflow_net": 1300.0,
            "taux_recouvrement": 100.0,
        },
        "scis": [sci1, sci2],
    }


def _make_sci_bilan() -> dict:
    """Full bilan_data for sci scope."""
    bien = _make_bien()
    sci = _make_sci_scope(biens=[bien])
    return {
        "periode": "2026-03",
        "generated_at": "2026-03-31T00:00:00",
        "sci": sci,
        "scis": [sci],
    }


def _make_bien_bilan() -> dict:
    """Full bilan_data for bien scope."""
    bien = _make_bien()
    return {
        "periode": "2026-03",
        "generated_at": "2026-03-31T00:00:00",
        "bien": bien,
        "scis": [],
    }


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


class TestFmtEur:
    def test_positive(self):
        result = _fmt_eur(1200.0)
        assert "1" in result and "EUR" in result

    def test_zero(self):
        result = _fmt_eur(0.0)
        assert "0" in result and "EUR" in result

    def test_negative(self):
        result = _fmt_eur(-500.0)
        assert "EUR" in result

    def test_large(self):
        result = _fmt_eur(99_999.99)
        assert "EUR" in result


class TestPeriodeLabel:
    def test_valid_periode(self):
        assert _periode_label("2026-03") == "Mars 2026"

    def test_january(self):
        assert _periode_label("2025-01") == "Janvier 2025"

    def test_december(self):
        assert _periode_label("2025-12") == "Décembre 2025"

    def test_invalid_falls_back(self):
        result = _periode_label("invalid")
        assert result == "invalid"

    def test_empty_falls_back(self):
        result = _periode_label("")
        assert result == ""


class TestGetSummary:
    def test_portefeuille_scope(self):
        bilan = _make_portefeuille_bilan()
        summary = _get_summary(bilan, "portefeuille")
        assert summary["revenus_attendus"] == 2400.0
        assert summary["taux_recouvrement"] == 100.0

    def test_sci_scope(self):
        bilan = _make_sci_bilan()
        summary = _get_summary(bilan, "sci")
        assert summary["cashflow_net"] == 1300.0

    def test_bien_scope_with_revenus(self):
        bilan = _make_bien_bilan()
        summary = _get_summary(bilan, "bien")
        assert "revenus_attendus" in summary
        # taux_recouvrement computed from revenus_encaisses / revenus_attendus
        assert summary["taux_recouvrement"] >= 0

    def test_bien_scope_zero_revenus(self):
        bilan = _make_bien_bilan()
        bilan["bien"]["revenus_attendus"] = 0
        bilan["bien"]["revenus_encaisses"] = 0
        summary = _get_summary(bilan, "bien")
        assert summary["taux_recouvrement"] == 0

    def test_sci_scope_no_sci_key(self):
        """Falls through to portefeuille default when sci key missing."""
        bilan = {"portefeuille": {"revenus_attendus": 500.0, "revenus_encaisses": 500.0,
                                   "impayes": 0.0, "charges": 0.0, "cashflow_net": 500.0,
                                   "taux_recouvrement": 100.0}}
        summary = _get_summary(bilan, "sci")
        assert summary["revenus_attendus"] == 500.0


class TestGetBiensList:
    def test_bien_scope(self):
        bilan = _make_bien_bilan()
        biens = _get_biens_list(bilan, "bien", None)
        assert len(biens) == 1

    def test_sci_scope(self):
        bilan = _make_sci_bilan()
        biens = _get_biens_list(bilan, "sci", None)
        assert len(biens) >= 1

    def test_portefeuille_scope(self):
        bilan = _make_portefeuille_bilan()
        biens = _get_biens_list(bilan, "portefeuille", None)
        assert len(biens) >= 2


class TestBuildLedgerEntries:
    def test_paid_loyer_is_entree(self):
        bilan = _make_bien_bilan()
        entries = _build_ledger_entries(bilan, "bien", None)
        paid = [e for e in entries if e.get("entree", 0) > 0]
        assert len(paid) >= 1

    def test_impaye_loyer_is_zero_entry(self):
        bilan = _make_bien_bilan()
        entries = _build_ledger_entries(bilan, "bien", None)
        impayes = [e for e in entries if "IMPAYÉ" in e.get("label", "")]
        assert len(impayes) >= 1

    def test_charge_is_sortie(self):
        bilan = _make_bien_bilan()
        entries = _build_ledger_entries(bilan, "bien", None)
        sorties = [e for e in entries if e.get("sortie", 0) > 0]
        assert len(sorties) >= 1

    def test_entries_sorted_by_date(self):
        bilan = _make_bien_bilan()
        bilan["bien"]["loyers"] = [
            {"statut": "paye", "montant": 1000.0, "date": "2026-03-15", "locataire": "A"},
            {"statut": "paye", "montant": 1000.0, "date": "2026-03-01", "locataire": "B"},
        ]
        bilan["bien"]["charges_detail"] = []
        entries = _build_ledger_entries(bilan, "bien", None)
        dates = [e["date"] for e in entries]
        assert dates == sorted(dates)

    def test_bien_no_adresse(self):
        bilan = _make_bien_bilan()
        bilan["bien"]["adresse"] = ""
        entries = _build_ledger_entries(bilan, "bien", None)
        # Should not raise; falls back to "Bien" label
        assert isinstance(entries, list)

    def test_loyer_paid_status_variants(self):
        """Both 'paye' and 'paid' statuses are treated as encaissements."""
        bilan = _make_bien_bilan()
        bilan["bien"]["loyers"] = [
            {"statut": "paye", "montant": 500.0, "date": "2026-03-01", "locataire": ""},
            {"statut": "paid", "montant": 600.0, "date": "2026-03-02", "locataire": ""},
        ]
        bilan["bien"]["charges_detail"] = []
        entries = _build_ledger_entries(bilan, "bien", None)
        paid_entries = [e for e in entries if e.get("entree", 0) > 0]
        assert len(paid_entries) == 2

    def test_long_label_truncated(self):
        """Long-label loyers are still stored in entries; the drawing loop truncates them."""
        bilan = _make_bien_bilan()
        bilan["bien"]["loyers"] = [
            {
                "statut": "paye",
                "montant": 1000.0,
                "date": "2026-03-01",
                "locataire": "A" * 50,  # very long locataire name
            }
        ]
        bilan["bien"]["charges_detail"] = []
        entries = _build_ledger_entries(bilan, "bien", None)
        # Entries store the full label; generate_bilan_pdf() truncates during drawing.
        # Here we just verify entries are returned with a non-empty label.
        assert len(entries) == 1
        assert len(entries[0].get("label", "")) > 40
        # Verify that passing these entries through generate_bilan_pdf does not raise.
        pdf = generate_bilan_pdf(bilan, scope="bien")
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# generate_bilan_pdf() — full PDF generation
# ---------------------------------------------------------------------------


class TestGenerateBilanPdf:
    """Each test calls generate_bilan_pdf() and checks for valid PDF bytes."""

    def test_portefeuille_scope(self):
        bilan = _make_portefeuille_bilan()
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_sci_scope(self):
        bilan = _make_sci_bilan()
        pdf = generate_bilan_pdf(bilan, scope="sci", scope_id="sci-1")
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_bien_scope(self):
        bilan = _make_bien_bilan()
        pdf = generate_bilan_pdf(bilan, scope="bien", scope_id="b1")
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_negative_cashflow(self):
        """Negative cashflow triggers red color path."""
        bilan = _make_portefeuille_bilan()
        bilan["portefeuille"]["cashflow_net"] = -500.0
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert pdf[:4] == b"%PDF"

    def test_positive_cashflow(self):
        """Positive cashflow triggers green color path."""
        bilan = _make_portefeuille_bilan()
        bilan["portefeuille"]["cashflow_net"] = 1300.0
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert pdf[:4] == b"%PDF"

    def test_zero_taux_recouvrement(self):
        bilan = _make_portefeuille_bilan()
        bilan["portefeuille"]["taux_recouvrement"] = 0.0
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert len(pdf) > 500

    def test_full_taux_recouvrement(self):
        bilan = _make_portefeuille_bilan()
        bilan["portefeuille"]["taux_recouvrement"] = 100.0
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert len(pdf) > 500

    def test_no_entries(self):
        """Empty ledger (no loyers, no charges) — entries block skipped."""
        bilan = {
            "periode": "2026-03",
            "generated_at": "2026-03-31T00:00:00",
            "portefeuille": {
                "revenus_attendus": 0.0,
                "revenus_encaisses": 0.0,
                "impayes": 0.0,
                "charges": 0.0,
                "cashflow_net": 0.0,
                "taux_recouvrement": 0.0,
            },
            "scis": [],
        }
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert pdf[:4] == b"%PDF"

    def test_many_entries_trigger_page_break(self):
        """Generate enough entries to force the page-break logic (y < 80)."""
        loyers = [
            {"statut": "paye", "montant": 1000.0, "date": f"2026-03-{i:02d}", "locataire": f"L{i}"}
            for i in range(1, 30)
        ]
        charges = [
            {"type": "Taxe", "montant": 100.0, "date": f"2026-03-{i:02d}"}
            for i in range(1, 20)
        ]
        bien = _make_bien(loyers=loyers, charges=charges)
        bilan = {
            "periode": "2026-03",
            "generated_at": "2026-03-31T00:00:00",
            "portefeuille": {
                "revenus_attendus": 29000.0,
                "revenus_encaisses": 29000.0,
                "impayes": 0.0,
                "charges": 1900.0,
                "cashflow_net": 27100.0,
                "taux_recouvrement": 100.0,
            },
            "scis": [{"id": "s1", "biens": [bien]}],
        }
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert pdf[:4] == b"%PDF"

    def test_missing_generated_at(self):
        """generated_at absent or short — slicing [:10] should not raise."""
        bilan = _make_portefeuille_bilan()
        bilan["generated_at"] = ""
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert len(pdf) > 500

    def test_sci_scope_label_from_sci_nom(self):
        """sci scope uses sci_nom for the scope_label."""
        bilan = _make_sci_bilan()
        bilan["sci"]["sci_nom"] = "SCI Custom Label"
        pdf = generate_bilan_pdf(bilan, scope="sci")
        assert pdf[:4] == b"%PDF"

    def test_bien_scope_label_from_adresse(self):
        """bien scope uses adresse + ville for scope_label."""
        bilan = _make_bien_bilan()
        bilan["bien"]["adresse"] = "99 bd Test"
        bilan["bien"]["ville"] = "Nantes"
        pdf = generate_bilan_pdf(bilan, scope="bien")
        assert pdf[:4] == b"%PDF"

    def test_bien_scope_empty_adresse_ville(self):
        """bien scope with no adresse and no ville falls back to 'Bien'."""
        bilan = _make_bien_bilan()
        bilan["bien"]["adresse"] = ""
        bilan["bien"]["ville"] = ""
        pdf = generate_bilan_pdf(bilan, scope="bien")
        assert len(pdf) > 500

    def test_total_row_page_break(self):
        """Force the total-row page break (lines 308-310) by having exactly 33 entries on last page.

        A4 height ~841pt. After a mid-table page break y=height-40≈802.
        Each entry row_h=22.  After 33 entries: y≈802-33*22=74 → y-row_h=52 < 80 → fires.
        First page has 20 entries (< threshold 32), triggering no mid-page break, leaving
        y≈802 - 20*22 = 362. The subsequent 13 entries make 33 total.  But the simplest
        reliable approach is to generate a number of entries that fills a full page (32+) and
        leaves exactly 33 on the final page.  We use 32 + 33 = 65 entries total.
        """
        loyers = [
            {"statut": "paye", "montant": 100.0, "date": f"2026-03-{(i % 28) + 1:02d}", "locataire": f"L{i}"}
            for i in range(65)
        ]
        bien = _make_bien(loyers=loyers, charges=[])
        bilan = {
            "periode": "2026-03",
            "generated_at": "2026-03-31T00:00:00",
            "portefeuille": {
                "revenus_attendus": 6500.0,
                "revenus_encaisses": 6500.0,
                "impayes": 0.0,
                "charges": 0.0,
                "cashflow_net": 6500.0,
                "taux_recouvrement": 100.0,
            },
            "scis": [{"id": "s1", "biens": [bien]}],
        }
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert pdf[:4] == b"%PDF"

    def test_negative_solde_cumul(self):
        """Running solde going negative triggers red color for solde column."""
        charges_heavy = [
            {"type": "Taxe", "montant": 5000.0, "date": "2026-03-01"},
        ]
        bien = _make_bien(
            loyers=[{"statut": "paye", "montant": 100.0, "date": "2026-03-15", "locataire": "A"}],
            charges=charges_heavy,
        )
        bilan = {
            "periode": "2026-03",
            "generated_at": "2026-03-31T00:00:00",
            "portefeuille": {
                "revenus_attendus": 100.0,
                "revenus_encaisses": 100.0,
                "impayes": 0.0,
                "charges": 5000.0,
                "cashflow_net": -4900.0,
                "taux_recouvrement": 100.0,
            },
            "scis": [{"id": "s1", "biens": [bien]}],
        }
        pdf = generate_bilan_pdf(bilan, scope="portefeuille")
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# _register_fonts (bilan_pdf_service version)
# ---------------------------------------------------------------------------

class TestRegisterFontsBilan:
    def test_returns_tuple_strings(self):
        name, bold = _register_fonts()
        assert isinstance(name, str) and len(name) > 0
        assert isinstance(bold, str) and len(bold) > 0

    def test_no_fonts_helvetica_fallback(self):
        with patch("app.services.bilan_pdf_service.os.path.isfile", return_value=False):
            name, bold = _register_fonts()
        assert name == "Helvetica"
        assert bold == "Helvetica-Bold"

    def test_dejavu_not_found_vera_fallback(self):
        original = os.path.isfile

        def fake_isfile(path):
            if "DejaVu" in path or "dejavu" in path:
                return False
            return original(path)

        with patch("app.services.bilan_pdf_service.os.path.isfile", side_effect=fake_isfile):
            name, bold = _register_fonts()
        assert "DejaVu" not in name

    def test_dejavu_registration_raises_continues(self):
        original = os.path.isfile

        def fake_isfile(path):
            if "DejaVu" in path:
                return True
            return original(path)

        with patch("app.services.bilan_pdf_service.os.path.isfile", side_effect=fake_isfile), \
             patch("app.services.bilan_pdf_service.pdfmetrics.registerFont", side_effect=Exception("bad")):
            name, bold = _register_fonts()
        assert isinstance(name, str)
