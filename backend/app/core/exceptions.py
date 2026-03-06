"""
Exceptions custom pour GererSCI.
Toutes héritent de GererSCIException qui inclut un status_code HTTP.
"""


class GererSCIException(Exception):
    """
    Exception de base pour toutes les erreurs GererSCI.

    Attributes:
        message: Message d'erreur lisible
        status_code: Code HTTP correspondant
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "internal_error",
        details: dict | list | str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(self.message)


class DatabaseError(GererSCIException):
    """Erreur de base de données (Supabase)"""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=503, code="database_error")


class ResourceNotFoundError(GererSCIException):
    """Ressource non trouvée (bien, loyer, associé, etc.)"""

    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} {resource_id} not found"
        super().__init__(message, status_code=404, code="resource_not_found")


class ValidationError(GererSCIException):
    """Erreur de validation des données d'entrée"""

    def __init__(self, message: str):
        super().__init__(message, status_code=400, code="validation_error")


class ExternalServiceError(GererSCIException):
    """
    Erreur d'un service externe (Stripe, Resend, Supabase Storage).
    Utilisé quand l'erreur vient d'un service tiers, pas de notre code.
    """

    def __init__(self, service: str, message: str):
        full_message = f"{service} error: {message}"
        super().__init__(full_message, status_code=503, code="external_service_error")


class AuthenticationError(GererSCIException):
    """Erreur d'authentification (token invalide, expiré)"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401, code="authentication_error")


class AuthorizationError(GererSCIException):
    """Erreur d'autorisation (user n'a pas le droit d'accéder à la ressource)"""

    def __init__(self, resource: str, resource_id: str):
        message = f"User not authorized to access {resource} {resource_id}"
        super().__init__(message, status_code=403, code="authorization_error")


class BusinessLogicError(GererSCIException):
    """
    Erreur de logique métier (ex: loyer déjà enregistré pour ce mois).
    Status 422 Unprocessable Entity (syntaxe OK mais logique invalide).
    """

    def __init__(self, message: str):
        super().__init__(message, status_code=422, code="business_logic_error")


class PlanLimitError(SCIManagerException):
    """Quota métier atteint pour le plan actif."""

    def __init__(self, resource: str, limit: int | None, current: int, plan_key: str):
        message = f"Le quota {resource} du plan actif est atteint."
        super().__init__(
            message,
            status_code=422,
            code="plan_limit_reached",
            details={
                "resource": resource,
                "limit": limit,
                "current": current,
                "plan_key": plan_key,
            },
        )


class UpgradeRequiredError(SCIManagerException):
    """Demande de montée en gamme quand la fonctionnalité n'est pas disponible."""

    def __init__(self, message: str, plan_key: str):
        super().__init__(
            message,
            status_code=402,
            code="upgrade_required",
            details={"plan_key": plan_key},
        )


class SubscriptionInactiveError(SCIManagerException):
    """Abonnement non actif ou non exploitable pour l'action demandée."""

    def __init__(self, plan_key: str | None = None, status: str | None = None):
        super().__init__(
            "L'abonnement actif ne permet pas cette opération.",
            status_code=403,
            code="subscription_inactive",
            details={"plan_key": plan_key, "status": status},
        )


class FeatureDisabledError(SCIManagerException):
    """Fonctionnalité désactivée via feature flag."""

    def __init__(self, message: str, flag_name: str):
        super().__init__(
            message,
            status_code=503,
            code="feature_disabled",
            details={"flag": flag_name},
        )
