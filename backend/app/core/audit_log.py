"""
Audit Logging pour conformité réglementaire (SOC 2, RGPD, ISO 27001).

Ce module fournit des fonctions centralisées pour logger les événements
critiques nécessaires aux audits de sécurité et de conformité.
"""
import structlog
from typing import Optional
from fastapi import Request

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Centralized audit logging for compliance"""

    @staticmethod
    async def log_auth_event(
        event: str,
        user_id: Optional[str],
        email: Optional[str],
        request: Request,
        success: bool,
        details: Optional[dict] = None
    ) -> None:
        """
        Log authentication events (login, logout, magic link, etc.)

        Args:
            event: Type d'événement (magic_link_sent, magic_link_verified, logout, etc.)
            user_id: ID utilisateur (None si pas encore authentifié)
            email: Email utilisateur
            request: FastAPI Request object
            success: Succès ou échec de l'opération
            details: Détails additionnels (optionnel)
        """
        logger.info(
            f"auth.{event}",
            event_category="authentication",
            event_type=event,
            user_id=user_id,
            user_email=email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=success,
            details=details or {},
            severity="INFO" if success else "WARNING"
        )

    @staticmethod
    async def log_data_access(
        resource: str,
        action: str,
        user_id: str,
        resource_id: Optional[str],
        request: Request,
        success: bool,
        details: Optional[dict] = None
    ) -> None:
        """
        Log data access events (CRUD operations)

        Args:
            resource: Type de ressource (bien, loyer, associe, cerfa, etc.)
            action: Action effectuée (create, read, update, delete)
            user_id: ID utilisateur
            resource_id: ID de la ressource concernée
            request: FastAPI Request object
            success: Succès ou échec de l'opération
            details: Détails additionnels (optionnel)
        """
        logger.info(
            f"data.{resource}.{action}",
            event_category="data_access",
            resource_type=resource,
            action=action,
            user_id=user_id,
            resource_id=resource_id,
            ip_address=request.client.host if request.client else None,
            success=success,
            details=details or {},
            severity="INFO" if success else "WARNING"
        )

    @staticmethod
    async def log_gdpr_event(
        event: str,
        user_id: str,
        request: Request,
        details: Optional[dict] = None
    ) -> None:
        """
        Log GDPR-related events (export, delete, consent)

        Args:
            event: Type d'événement (data_export, account_delete, consent_update)
            user_id: ID utilisateur
            request: FastAPI Request object
            details: Détails additionnels (optionnel)
        """
        logger.info(
            f"gdpr.{event}",
            event_category="gdpr_compliance",
            event_type=event,
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=details or {},
            severity="INFO"
        )

    @staticmethod
    async def log_payment_event(
        event: str,
        user_id: Optional[str],
        amount: Optional[int],
        currency: str,
        stripe_customer_id: Optional[str],
        success: bool,
        details: Optional[dict] = None
    ) -> None:
        """
        Log payment-related events (Stripe transactions)

        Args:
            event: Type d'événement (checkout_completed, subscription_created, etc.)
            user_id: ID utilisateur
            amount: Montant en centimes
            currency: Devise (eur, usd, etc.)
            stripe_customer_id: ID client Stripe
            success: Succès ou échec de l'opération
            details: Détails additionnels (optionnel)
        """
        logger.info(
            f"payment.{event}",
            event_category="payment",
            event_type=event,
            user_id=user_id,
            amount=amount,
            currency=currency,
            stripe_customer_id=stripe_customer_id,
            success=success,
            details=details or {},
            severity="INFO" if success else "WARNING"
        )

    @staticmethod
    async def log_file_event(
        event: str,
        user_id: str,
        file_path: str,
        file_size: Optional[int],
        request: Request,
        success: bool,
        details: Optional[dict] = None
    ) -> None:
        """
        Log file operations (upload, download, delete)

        Args:
            event: Type d'événement (upload, download, delete)
            user_id: ID utilisateur
            file_path: Chemin du fichier
            file_size: Taille du fichier en bytes
            request: FastAPI Request object
            success: Succès ou échec de l'opération
            details: Détails additionnels (optionnel)
        """
        logger.info(
            f"file.{event}",
            event_category="file_operation",
            event_type=event,
            user_id=user_id,
            file_path=file_path,
            file_size=file_size,
            ip_address=request.client.host if request.client else None,
            success=success,
            details=details or {},
            severity="INFO" if success else "WARNING"
        )

    @staticmethod
    async def log_security_event(
        event: str,
        user_id: Optional[str],
        request: Request,
        severity: str,
        details: Optional[dict] = None
    ) -> None:
        """
        Log security events (brute force, suspicious activity, etc.)

        Args:
            event: Type d'événement (brute_force_detected, suspicious_ip, etc.)
            user_id: ID utilisateur (None si pas identifié)
            request: FastAPI Request object
            severity: Niveau de sévérité (INFO, WARNING, ERROR, CRITICAL)
            details: Détails additionnels (optionnel)
        """
        log_method = getattr(logger, severity.lower(), logger.info)
        log_method(
            f"security.{event}",
            event_category="security",
            event_type=event,
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=details or {},
            severity=severity
        )
