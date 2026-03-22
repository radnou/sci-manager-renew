"""Email service using Resend API with Jinja2 file-based templates"""
from pathlib import Path

import structlog
import resend
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.external_services import run_with_retry
from app.core.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "emails"
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def _render_template(template_name: str, **kwargs: object) -> str:
    """Render an email template with the given context variables."""
    template = _jinja_env.get_template(template_name)
    return template.render(**kwargs)


class EmailService:
    """Service for sending emails via Resend"""

    def __init__(self) -> None:
        resend.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email
        self.frontend_url = settings.frontend_url

    async def send_magic_link(self, email: str, magic_link: str) -> dict:
        """Send magic link for authentication

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_magic_link", email=email)

        try:
            html = _render_template(
                "magic_link.html",
                cta_url=magic_link,
                cta_text="Se connecter",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": "Connexion à GererSCI",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_magic_link",
                func=lambda: resend.Emails.send(payload),
                context={"email": email},
            )

            logger.info("magic_link_sent", email=email)
            return result
        except Exception as e:
            logger.error("magic_link_send_failed", email=email, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Magic link send failed: {str(e)}")

    async def send_activation_welcome(self, email: str, magic_link_url: str) -> dict:
        """Send welcome email after guest checkout activation with magic link fallback.

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_activation_welcome_email", email=email)

        try:
            html = _render_template(
                "activation_welcome.html",
                cta_url=magic_link_url,
                cta_text="Accéder à mon espace",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": "Bienvenue sur GérerSCI — Activez votre accès",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_activation_welcome",
                func=lambda: resend.Emails.send(payload),
                context={"email": email},
            )

            logger.info("activation_welcome_email_sent", email=email)
            return result
        except Exception as e:
            logger.error("activation_welcome_email_send_failed", email=email, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Activation welcome email send failed: {str(e)}")

    async def send_welcome(self, email: str, plan_name: str) -> dict:
        """Send welcome email

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_welcome_email", email=email)

        try:
            html = _render_template(
                "welcome.html",
                plan_name=plan_name,
                cta_url=f"{self.frontend_url}/dashboard",
                cta_text="Accéder à mon espace",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": "Bienvenue sur GererSCI!",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_welcome",
                func=lambda: resend.Emails.send(payload),
                context={"email": email},
            )

            logger.info("welcome_email_sent", email=email)
            return result
        except Exception as e:
            logger.error("welcome_email_send_failed", email=email, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Welcome email send failed: {str(e)}")

    async def send_quitus_generated(
        self,
        email: str,
        bien_name: str,
        locataire_name: str = "",
        mois: str = "",
        bien_adresse: str = "",
        download_url: str = "",
    ) -> dict:
        """Notify when quitus is generated

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_quitus_notification", email=email, bien=bien_name)

        try:
            html = _render_template(
                "quittance.html",
                locataire_name=locataire_name or bien_name,
                mois=mois,
                bien_adresse=bien_adresse or bien_name,
                cta_url=download_url or f"{self.frontend_url}/dashboard",
                cta_text="Télécharger la quittance",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": f"Quitus généré - {bien_name}",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_quitus_notification",
                func=lambda: resend.Emails.send(payload),
                context={"email": email, "bien": bien_name},
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
            html = _render_template(
                "subscription.html",
                plan_name=plan,
                cta_url=f"{self.frontend_url}/dashboard",
                cta_text="Accéder à mon espace",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": "Abonnement activé",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_subscription_confirmation",
                func=lambda: resend.Emails.send(payload),
                context={"email": email, "plan": plan},
            )

            logger.info("subscription_confirmation_sent", email=email, plan=plan)
            return result
        except Exception as e:
            logger.error("subscription_confirmation_send_failed", email=email, plan=plan, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Subscription confirmation send failed: {str(e)}")

    async def send_associe_invitation(
        self,
        to_email: str,
        sci_nom: str,
        inviter_nom: str,
        role: str,
        frontend_url: str,
    ) -> bool:
        """Send invitation email to a new associé.

        Best-effort: returns True on success, False on failure (never raises).
        """
        role_label = "Gérant" if role == "gerant" else "Associé"
        logger.info(
            "sending_associe_invitation",
            to_email=to_email,
            sci_nom=sci_nom,
            role=role,
        )

        try:
            html = _render_template(
                "associe_invitation.html",
                sci_nom=sci_nom,
                inviter_nom=inviter_nom,
                role_label=role_label,
                cta_url=f"{frontend_url}/login",
                cta_text="Se connecter à GererSCI",
            )

            payload = {
                "from": self.from_email,
                "to": to_email,
                "subject": f"Vous êtes invité à rejoindre la SCI {sci_nom} sur GererSCI",
                "html": html,
            }
            await run_with_retry(
                operation="resend.send_associe_invitation",
                func=lambda: resend.Emails.send(payload),
                context={"email": to_email, "sci_nom": sci_nom},
            )

            logger.info("associe_invitation_sent", to_email=to_email, sci_nom=sci_nom)
            return True
        except Exception as e:
            logger.warning(
                "associe_invitation_send_failed",
                to_email=to_email,
                sci_nom=sci_nom,
                error=str(e),
                exc_info=True,
            )
            return False

    async def send_notification_email(
        self,
        email: str,
        title: str,
        message: str,
        notification_type: str,
    ) -> dict:
        """Send a notification email (cron alerts: late payments, expiring bails, etc.).

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info(
            "sending_notification_email",
            email=email,
            notification_type=notification_type,
        )

        try:
            html = _render_template(
                "notification.html",
                title=title,
                message=message,
                notification_type=notification_type,
                cta_url=f"{self.frontend_url}/dashboard",
                cta_text="Voir mon tableau de bord",
                unsubscribe_url=f"{self.frontend_url}/settings",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": f"GererSCI — {title}",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_notification_email",
                func=lambda: resend.Emails.send(payload),
                context={"email": email, "notification_type": notification_type},
            )

            logger.info(
                "notification_email_sent",
                email=email,
                notification_type=notification_type,
            )
            return result
        except Exception as e:
            logger.error(
                "notification_email_send_failed",
                email=email,
                notification_type=notification_type,
                error=str(e),
                exc_info=True,
            )
            raise ExternalServiceError(
                "Resend",
                f"Notification email send failed: {str(e)}",
            )

    async def send_reset_password(self, email: str, reset_link: str) -> dict:
        """Send password reset email

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_reset_password", email=email)

        try:
            html = _render_template(
                "reset_password.html",
                cta_url=reset_link,
                cta_text="Réinitialiser mon mot de passe",
            )

            payload = {
                "from": self.from_email,
                "to": email,
                "subject": "Réinitialisation de votre mot de passe - GererSCI",
                "html": html,
            }
            result = await run_with_retry(
                operation="resend.send_reset_password",
                func=lambda: resend.Emails.send(payload),
                context={"email": email},
            )

            logger.info("reset_password_sent", email=email)
            return result
        except Exception as e:
            logger.error("reset_password_send_failed", email=email, error=str(e), exc_info=True)
            raise ExternalServiceError("Resend", f"Reset password email send failed: {str(e)}")

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        template: str,
        context: dict | None = None,
    ) -> dict:
        """Generic email send using a Jinja2 template.

        Raises:
            ExternalServiceError: Si l'envoi échoue
        """
        logger.info("sending_generic_email", to=to, template=template)
        try:
            html = _render_template(template, **(context or {}))
            payload = {
                "from": self.from_email,
                "to": to,
                "subject": subject,
                "html": html,
            }
            result = await run_with_retry(
                operation=f"resend.send_{template}",
                func=lambda: resend.Emails.send(payload),
                context={"email": to},
            )
            logger.info("generic_email_sent", to=to, template=template)
            return result
        except Exception as e:
            logger.error("generic_email_send_failed", to=to, template=template, error=str(e))
            raise ExternalServiceError("Resend", f"Email send failed: {str(e)}")


# Singleton instance
email_service = EmailService()
