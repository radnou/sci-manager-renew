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
