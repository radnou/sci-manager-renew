import os
from unittest.mock import patch

from app.models.quitus import QuitusRequest
from app.services.quitus_service import QuitusService, _register_fonts


def test_generate_quitus_pdf():
    payload = QuitusRequest(
        id_loyer="loyer-2",
        id_bien="bien-2",
        nom_locataire="Alice Martin",
        periode="Fevrier 2026",
        montant=980.0,
        nom_sci="SCI Horizon Lyon",
        adresse_bien="42 avenue QA",
        ville_bien="Lyon",
    )
    pdf = QuitusService.generate_quitus_pdf(payload)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert b"SCI Horizon Lyon" in pdf
    assert b"Alice Martin" in pdf
    assert b"42 avenue QA, Lyon" in pdf
    assert b"loyer-2" not in pdf
    assert b"bien-2" not in pdf


# ---------------------------------------------------------------------------
# _build_property_label edge cases
# ---------------------------------------------------------------------------

class TestBuildPropertyLabel:
    def test_adresse_and_ville(self):
        q = QuitusRequest(
            id_loyer="l1", id_bien="b1", nom_locataire="Jean Dupont",
            periode="Mars 2026", montant=500.0,
            adresse_bien="10 rue de la Paix", ville_bien="Paris",
        )
        assert QuitusService._build_property_label(q) == "10 rue de la Paix, Paris"

    def test_adresse_only(self):
        q = QuitusRequest(
            id_loyer="l1", id_bien="b1", nom_locataire="Jean Dupont",
            periode="Mars 2026", montant=500.0,
            adresse_bien="10 rue de la Paix",
        )
        assert QuitusService._build_property_label(q) == "10 rue de la Paix"

    def test_ville_only(self):
        q = QuitusRequest(
            id_loyer="l1", id_bien="b1", nom_locataire="Jean Dupont",
            periode="Mars 2026", montant=500.0,
            ville_bien="Lyon",
        )
        assert QuitusService._build_property_label(q) == "Bien situé à Lyon"

    def test_no_adresse_no_ville(self):
        q = QuitusRequest(
            id_loyer="l1", id_bien="b1", nom_locataire="Jean Dupont",
            periode="Mars 2026", montant=500.0,
        )
        assert QuitusService._build_property_label(q) == "Bien rattaché à la SCI"


# ---------------------------------------------------------------------------
# generate_quitus_pdf variations
# ---------------------------------------------------------------------------

class TestGenerateQuitusPdfVariations:
    def test_no_sci_name_defaults(self):
        q = QuitusRequest(
            id_loyer="l1", id_bien="b1", nom_locataire="Jean Dupont",
            periode="Avril 2026", montant=750.0,
        )
        pdf = QuitusService.generate_quitus_pdf(q)
        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF")

    def test_large_amount(self):
        q = QuitusRequest(
            id_loyer="l1", id_bien="b1", nom_locataire="Marie Claire",
            periode="Mai 2026", montant=99999.99,
            nom_sci="SCI Test", adresse_bien="1 avenue Test", ville_bien="Marseille",
        )
        pdf = QuitusService.generate_quitus_pdf(q)
        assert isinstance(pdf, bytes)
        assert b"99999.99" in pdf


# ---------------------------------------------------------------------------
# _register_fonts — font discovery paths (lines 31-36, 40-45, 54, 56)
# ---------------------------------------------------------------------------

class TestRegisterFonts:
    def test_register_fonts_returns_tuple(self):
        """_register_fonts always returns a (name, bold_name) tuple."""
        name, bold = _register_fonts()
        assert isinstance(name, str)
        assert isinstance(bold, str)

    def test_register_fonts_no_dejavu_falls_back_to_vera(self):
        """When DejaVu not found, falls back to Vera bundled with reportlab."""
        # Patch os.path.isfile to return False for DejaVu paths
        original_isfile = os.path.isfile

        def fake_isfile(path):
            if "DejaVu" in path or "dejavu" in path:
                return False
            return original_isfile(path)

        with patch("app.services.quitus_service.os.path.isfile", side_effect=fake_isfile):
            name, bold = _register_fonts()
            # Should be either Vera or Helvetica (never DejaVu)
            assert "DejaVu" not in name

    def test_register_fonts_no_fonts_at_all(self):
        """When no TTF fonts exist, falls back to Helvetica."""
        with patch("app.services.quitus_service.os.path.isfile", return_value=False):
            name, bold = _register_fonts()
            assert name == "Helvetica"
            assert bold == "Helvetica-Bold"

    def test_register_fonts_dejavu_found(self):
        """When DejaVu path exists, registers it (lines 39-44)."""
        def fake_isfile(path):
            # Only DejaVu paths exist
            if path == "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf":
                return True
            if path == "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf":
                return True
            return False

        # Patch TTFont to avoid file read and registerFont to avoid registration
        with patch("app.services.quitus_service.os.path.isfile", side_effect=fake_isfile), \
             patch("app.services.quitus_service.TTFont", return_value="fake-font"), \
             patch("app.services.quitus_service.pdfmetrics.registerFont"):
            name, bold = _register_fonts()
            assert name == "DejaVuSans"
            assert bold == "DejaVuSans-Bold"

    def test_register_fonts_dejavu_register_exception(self):
        """When registerFont raises, catches and continues (lines 43-44)."""
        original_isfile = os.path.isfile

        def fake_isfile(path):
            if "DejaVu" in path or "dejavu" in path:
                return True
            return original_isfile(path)

        with patch("app.services.quitus_service.os.path.isfile", side_effect=fake_isfile), \
             patch("app.services.quitus_service.pdfmetrics.registerFont", side_effect=Exception("bad font")):
            name, bold = _register_fonts()
            # Should fall back since registration failed
            # Could be Vera or Helvetica depending on Vera availability
            assert isinstance(name, str)
            assert isinstance(bold, str)
