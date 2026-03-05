# backend/tests/test_exceptions.py
import pytest
from app.core.exceptions import (
    SCIManagerException,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError
)

def test_base_exception_has_status_code():
    """Test que SCIManagerException a un status_code"""
    exc = SCIManagerException("Test error", status_code=418)
    assert exc.message == "Test error"
    assert exc.status_code == 418

def test_database_error_defaults_to_503():
    """Test que DatabaseError a status 503"""
    exc = DatabaseError("Connection failed")
    assert exc.status_code == 503
    assert "Connection failed" in exc.message

def test_resource_not_found_defaults_to_404():
    """Test que ResourceNotFoundError a status 404"""
    exc = ResourceNotFoundError("Bien", "bien-123")
    assert exc.status_code == 404
    assert "Bien bien-123 not found" in exc.message

def test_validation_error_defaults_to_400():
    """Test que ValidationError a status 400"""
    exc = ValidationError("Invalid email format")
    assert exc.status_code == 400

def test_external_service_error_includes_service_name():
    """Test que ExternalServiceError mentionne le service"""
    exc = ExternalServiceError("Stripe", "Payment declined")
    assert exc.status_code == 503
    assert "Stripe" in exc.message
    assert "Payment declined" in exc.message

def test_authentication_error_defaults_to_401():
    """Test que AuthenticationError a status 401"""
    exc = AuthenticationError("Invalid token")
    assert exc.status_code == 401

def test_authorization_error_defaults_to_403():
    """Test que AuthorizationError a status 403"""
    exc = AuthorizationError("User", "bien-123")
    assert exc.status_code == 403
    assert "User" in exc.message
    assert "bien-123" in exc.message

def test_business_logic_error_defaults_to_422():
    """Test que BusinessLogicError a status 422"""
    exc = BusinessLogicError("Loyer already registered for this month")
    assert exc.status_code == 422
    assert "already registered" in exc.message


# Tests for global exception handlers (Task 2.2)

def test_sci_manager_exception_handler_returns_correct_status():
    """Test que les exceptions SCI-Manager retournent le bon status"""
    from fastapi.testclient import TestClient
    from app.main import app
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/test/validation-error")
    async def test_validation_error():
        raise ValidationError("Test validation failed")

    app.include_router(test_router)

    client = TestClient(app)
    response = client.get("/test/validation-error")

    assert response.status_code == 400
    response_json = response.json()
    assert response_json["error"] == "Test validation failed"
    assert "request_id" in response_json


def test_generic_exception_handler_hides_details_in_production():
    """Test que les exceptions génériques sont loggées et gérées"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.config import settings
    from fastapi import APIRouter

    # Sauvegarder l'environnement original
    original_env = settings.app_env

    try:
        # Changer en production pour ce test
        settings.app_env = "production"

        test_router = APIRouter()

        @test_router.get("/test/generic-error-prod")
        async def test_generic_error():
            raise Exception("Internal database connection string: postgresql://secret")

        app.include_router(test_router)

        client = TestClient(app)
        response = client.get("/test/generic-error-prod")

        assert response.status_code == 500
        response_json = response.json()

        # En production, ne pas exposer les détails
        assert "secret" not in response.text.lower()
        assert response_json["error"] == "Internal server error"
        assert "request_id" in response_json

    finally:
        # Restaurer l'environnement
        settings.app_env = original_env


def test_pydantic_validation_error_handler():
    """Test que les erreurs de validation Pydantic sont bien gérées"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import get_current_user

    # Override dependency pour bypasser l'auth
    app.dependency_overrides[get_current_user] = lambda: "user123"

    try:
        client = TestClient(app)

        # Envoyer des données invalides à un endpoint
        response = client.post(
            "/api/v1/biens/",
            json={
                "adresse": "Test",
                # Manque des champs requis: ville, code_postal, etc.
            }
        )

        assert response.status_code == 422  # Unprocessable Entity
        response_json = response.json()
        assert "error" in response_json or "detail" in response_json
        # Vérifier que le request_id est présent
        if "request_id" in response_json:
            assert response_json["request_id"] is not None
    finally:
        app.dependency_overrides.clear()
