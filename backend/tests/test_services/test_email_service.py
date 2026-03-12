"""Tests for email service Jinja2 template rendering"""
import pytest
from unittest.mock import patch, AsyncMock

from app.services.email_service import _render_template, EmailService
from app.core.exceptions import ExternalServiceError


class TestRenderTemplate:
    """Tests for _render_template helper"""

    def test_render_welcome_template(self):
        html = _render_template(
            "welcome.html",
            plan_name="Gestion",
            cta_url="https://app.gerersci.fr",
            cta_text="Accéder",
        )
        assert "Gestion" in html
        assert "GererSCI" in html
        assert "https://app.gerersci.fr" in html
        assert "Accéder" in html

    def test_render_magic_link_template(self):
        html = _render_template(
            "magic_link.html",
            cta_url="https://app.gerersci.fr/auth/callback?token=abc",
            cta_text="Se connecter",
        )
        assert "Se connecter" in html
        assert "https://app.gerersci.fr/auth/callback?token=abc" in html
        assert "GererSCI" in html

    def test_render_reset_password_template(self):
        html = _render_template(
            "reset_password.html",
            cta_url="https://app.gerersci.fr/reset?token=xyz",
            cta_text="Réinitialiser mon mot de passe",
        )
        assert "https://app.gerersci.fr/reset?token=xyz" in html
        assert "1 heure" in html
        assert "GererSCI" in html

    def test_render_quittance_template(self):
        html = _render_template(
            "quittance.html",
            locataire_name="Jean Dupont",
            mois="Mars 2026",
            bien_adresse="12 rue de la Paix, Paris",
            cta_url="https://app.gerersci.fr/download/q123",
            cta_text="Télécharger la quittance",
        )
        assert "Jean Dupont" in html
        assert "Mars 2026" in html
        assert "12 rue de la Paix, Paris" in html
        assert "https://app.gerersci.fr/download/q123" in html

    def test_render_subscription_template(self):
        html = _render_template(
            "subscription.html",
            plan_name="Pro",
            cta_url="https://app.gerersci.fr/dashboard",
            cta_text="Accéder à mon espace",
        )
        assert "Pro" in html
        assert "GererSCI" in html
        assert "https://app.gerersci.fr/dashboard" in html

    def test_base_template_without_cta(self):
        """When no cta_url/cta_text, the CTA button block should not appear"""
        html = _render_template("welcome.html", plan_name="Starter")
        assert "Starter" in html
        # No CTA button rendered
        assert "Si le bouton ne fonctionne pas" not in html

    def test_base_template_with_cta(self):
        """When cta_url and cta_text provided, both button and fallback link appear"""
        html = _render_template(
            "welcome.html",
            plan_name="Pro",
            cta_url="https://example.com",
            cta_text="Click me",
        )
        assert "Click me" in html
        assert "https://example.com" in html
        assert "Si le bouton ne fonctionne pas" in html

    def test_template_html_escaping(self):
        """Autoescape should prevent XSS in template variables"""
        html = _render_template(
            "welcome.html",
            plan_name='<script>alert("xss")</script>',
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_welcome_without_cta_omits_button(self):
        """When no cta_url provided, no href button should render."""
        html = _render_template("welcome.html", plan_name="Fiscal")
        assert "Fiscal" in html
        assert "href=" not in html or "Accéder" not in html

    def test_base_template_structure(self):
        """All templates should have consistent branded structure."""
        for tpl in ["welcome.html", "magic_link.html", "reset_password.html", "subscription.html"]:
            html = _render_template(
                tpl,
                plan_name="Test",
                cta_url="https://test.com",
                cta_text="Click",
                locataire_name="X",
                mois="Y",
                bien_adresse="Z",
            )
            assert "GererSCI" in html, f"{tpl} missing brand name"
            assert "gerersci.fr" in html, f"{tpl} missing footer domain"
            assert "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower(), f"{tpl} missing DOCTYPE"

    def test_render_nonexistent_template_raises(self):
        """Requesting a template that doesn't exist should raise"""
        with pytest.raises(Exception):
            _render_template("nonexistent.html")


class TestEmailServiceMethods:
    """Integration tests for EmailService methods using mocked Resend"""

    @pytest.mark.asyncio
    async def test_send_magic_link_renders_template(self):
        service = EmailService()
        with patch("resend.Emails.send") as mock_send:
            mock_send.return_value = {"id": "msg_123"}
            result = await service.send_magic_link(
                "user@example.com",
                "https://auth.gerersci.fr/callback?token=abc",
            )
        assert result == {"id": "msg_123"}
        call_args = mock_send.call_args[0][0]
        assert "Se connecter" in call_args["html"]
        assert "https://auth.gerersci.fr/callback?token=abc" in call_args["html"]

    @pytest.mark.asyncio
    async def test_send_welcome_renders_template(self):
        service = EmailService()
        with patch("resend.Emails.send") as mock_send:
            mock_send.return_value = {"id": "msg_456"}
            result = await service.send_welcome("user@example.com", "Pro")
        assert result == {"id": "msg_456"}
        call_args = mock_send.call_args[0][0]
        assert "Pro" in call_args["html"]
        assert "GererSCI" in call_args["html"]

    @pytest.mark.asyncio
    async def test_send_subscription_confirmation_renders_template(self):
        service = EmailService()
        with patch("resend.Emails.send") as mock_send:
            mock_send.return_value = {"id": "msg_789"}
            result = await service.send_subscription_confirmation(
                "user@example.com", "Starter"
            )
        assert result == {"id": "msg_789"}
        call_args = mock_send.call_args[0][0]
        assert "Starter" in call_args["html"]

    @pytest.mark.asyncio
    async def test_send_quitus_generated_renders_template(self):
        service = EmailService()
        with patch("resend.Emails.send") as mock_send:
            mock_send.return_value = {"id": "msg_q1"}
            result = await service.send_quitus_generated(
                "user@example.com",
                bien_name="Apt 3B",
                locataire_name="Marie Martin",
                mois="Février 2026",
                bien_adresse="5 avenue Victor Hugo",
            )
        assert result == {"id": "msg_q1"}
        call_args = mock_send.call_args[0][0]
        assert "Marie Martin" in call_args["html"]
        assert "vrier 2026" in call_args["html"]

    @pytest.mark.asyncio
    async def test_send_reset_password_renders_template(self):
        service = EmailService()
        with patch("resend.Emails.send") as mock_send:
            mock_send.return_value = {"id": "msg_rp1"}
            result = await service.send_reset_password(
                "user@example.com",
                "https://app.gerersci.fr/reset?token=xyz",
            )
        assert result == {"id": "msg_rp1"}
        call_args = mock_send.call_args[0][0]
        assert "https://app.gerersci.fr/reset?token=xyz" in call_args["html"]
        assert "1 heure" in call_args["html"]

    @pytest.mark.asyncio
    async def test_send_welcome_failure_raises_external_service_error(self):
        service = EmailService()
        with patch("resend.Emails.send") as mock_send:
            mock_send.side_effect = Exception("API down")
            with pytest.raises(ExternalServiceError):
                await service.send_welcome("user@example.com", "Pro")
