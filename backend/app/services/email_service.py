"""Email service using Resend API"""
from jinja2 import Template
import structlog
import resend

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)


class EmailService:
    """Service for sending emails via Resend"""

    def __init__(self):
        resend.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email

    async def send_magic_link(self, email: str, magic_link: str) -> dict:
        """Send magic link for authentication

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_magic_link", email=email)

        try:
            template = Template(
                """
            <h1>Connexion à GererSCI</h1>
            <p>Cliquez sur le lien ci-dessous pour vous connecter:</p>
            <a href="{{ link }}">Se connecter</a>
            <p>Ce lien expire dans 24h.</p>
            """
            )

            html = template.render(link=magic_link)

            result = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": email,
                    "subject": "Connexion à GererSCI",
                    "html": html,
                }
            )

            logger.info("magic_link_sent", email=email)
            return result
        except Exception as e:
            logger.error("magic_link_send_failed", email=email, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Magic link send failed: {str(e)}")

    async def send_welcome(self, email: str, user_name: str) -> dict:
        """Send welcome email

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_welcome_email", email=email)

        try:
            template = Template(
                """
            <h1>Bienvenue sur GererSCI, {{ name }}!</h1>
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

            result = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": email,
                    "subject": "Bienvenue sur GererSCI!",
                    "html": html,
                }
            )

            logger.info("welcome_email_sent", email=email)
            return result
        except Exception as e:
            logger.error("welcome_email_send_failed", email=email, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Welcome email send failed: {str(e)}")

    async def send_quitus_generated(self, email: str, bien_name: str) -> dict:
        """Notify when quitus is generated

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_quitus_notification", email=email, bien=bien_name)

        try:
            template = Template(
                """
            <h1>Quitus généré</h1>
            <p>Le quitus pour {{ bien }} a été généré avec succès.</p>
            <p>Vous pouvez le télécharger depuis votre dashboard.</p>
            """
            )

            html = template.render(bien=bien_name)

            result = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": email,
                    "subject": f"Quitus généré - {bien_name}",
                    "html": html,
                }
            )

            logger.info("quitus_notification_sent", email=email, bien=bien_name)
            return result
        except Exception as e:
            logger.error("quitus_notification_send_failed", email=email, bien=bien_name, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Quitus notification send failed: {str(e)}")

    async def send_subscription_confirmation(self, email: str, plan: str) -> dict:
        """Send subscription confirmation

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_subscription_confirmation", email=email, plan=plan)

        try:
            template = Template(
                """
            <h1>Abonnement activé</h1>
            <p>Votre abonnement au plan <strong>{{ plan }}</strong> est maintenant actif.</p>
            <p>Merci de votre confiance!</p>
            """
            )

            html = template.render(plan=plan)

            result = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": email,
                    "subject": "Abonnement activé",
                    "html": html,
                }
            )

            logger.info("subscription_confirmation_sent", email=email, plan=plan)
            return result
        except Exception as e:
            logger.error("subscription_confirmation_send_failed", email=email, plan=plan, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Subscription confirmation send failed: {str(e)}")


# Singleton instance
email_service = EmailService()
