"""
Exceptions custom pour SCI-Manager.
Toutes héritent de SCIManagerException qui inclut un status_code HTTP.
"""


class SCIManagerException(Exception):
    """
    Exception de base pour toutes les erreurs SCI-Manager.

    Attributes:
        message: Message d'erreur lisible
        status_code: Code HTTP correspondant
    """

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(SCIManagerException):
    """Erreur de base de données (Supabase)"""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=503)


class ResourceNotFoundError(SCIManagerException):
    """Ressource non trouvée (bien, loyer, associé, etc.)"""

    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} {resource_id} not found"
        super().__init__(message, status_code=404)


class ValidationError(SCIManagerException):
    """Erreur de validation des données d'entrée"""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class ExternalServiceError(SCIManagerException):
    """
    Erreur d'un service externe (Stripe, Resend, Supabase Storage).
    Utilisé quand l'erreur vient d'un service tiers, pas de notre code.
    """

    def __init__(self, service: str, message: str):
        full_message = f"{service} error: {message}"
        super().__init__(full_message, status_code=503)


class AuthenticationError(SCIManagerException):
    """Erreur d'authentification (token invalide, expiré)"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(SCIManagerException):
    """Erreur d'autorisation (user n'a pas le droit d'accéder à la ressource)"""

    def __init__(self, resource: str, resource_id: str):
        message = f"User not authorized to access {resource} {resource_id}"
        super().__init__(message, status_code=403)


class BusinessLogicError(SCIManagerException):
    """
    Erreur de logique métier (ex: loyer déjà enregistré pour ce mois).
    Status 422 Unprocessable Entity (syntaxe OK mais logique invalide).
    """

    def __init__(self, message: str):
        super().__init__(message, status_code=422)
