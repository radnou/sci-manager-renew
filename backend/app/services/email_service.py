"""Email service using Resend API"""
from jinja2 import Template
import resend

from app.core.config import settings


class EmailService:
    """Service for sending emails via Resend"""

    def __init__(self):
        resend.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email

    async def send_magic_link(self, email: str, magic_link: str) -> dict:
        """Send magic link for authentication"""
        template = Template(
            """
        <h1>Connexion à SCI-Manager</h1>
        <p>Cliquez sur le lien ci-dessous pour vous connecter:</p>
        <a href="{{ link }}">Se connecter</a>
        <p>Ce lien expire dans 24h.</p>
        """
        )

        html = template.render(link=magic_link)

        return resend.Emails.send(
            {
                "from": self.from_email,
                "to": email,
                "subject": "Connexion à SCI-Manager",
                "html": html,
            }
        )

    async def send_welcome(self, email: str, user_name: str) -> dict:
        """Send welcome email"""
        template = Template(
            """
        <h1>Bienvenue sur SCI-Manager, {{ name }}!</h1>
        <p>Votre compte a été créé avec succès.</p>
        <p>Vous pouvez maintenant:</p>
        <ul>
            <li>Ajouter vos biens immobiliers</li>
            <li>Gérer vos loyers et charges</li>
            <li>Générer automatiquement vos quitus</li>
            <li>Exporter vos données fiscales (Cerfa 2044)</li>
        </ul>
        """
        )

        html = template.render(name=user_name)

        return resend.Emails.send(
            {
                "from": self.from_email,
                "to": email,
                "subject": "Bienvenue sur SCI-Manager!",
                "html": html,
            }
        )

    async def send_quitus_generated(self, email: str, bien_name: str) -> dict:
        """Notify when quitus is generated"""
        template = Template(
            """
        <h1>Quitus généré</h1>
        <p>Le quitus pour {{ bien }} a été généré avec succès.</p>
        <p>Vous pouvez le télécharger depuis votre dashboard.</p>
        """
        )

        html = template.render(bien=bien_name)

        return resend.Emails.send(
            {
                "from": self.from_email,
                "to": email,
                "subject": f"Quitus généré - {bien_name}",
                "html": html,
            }
        )

    async def send_subscription_confirmation(self, email: str, plan: str) -> dict:
        """Send subscription confirmation"""
        template = Template(
            """
        <h1>Abonnement activé</h1>
        <p>Votre abonnement au plan <strong>{{ plan }}</strong> est maintenant actif.</p>
        <p>Merci de votre confiance!</p>
        """
        )

        html = template.render(plan=plan)

        return resend.Emails.send(
            {
                "from": self.from_email,
                "to": email,
                "subject": "Abonnement activé",
                "html": html,
            }
        )


# Singleton instance
email_service = EmailService()
