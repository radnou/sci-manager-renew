"""
Tests for app.core.audit_log — AuditLogger methods.

Covers all 6 static methods with both success and failure scenarios,
including edge cases for None client, missing headers, and custom severity.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.core.audit_log import AuditLogger


def _make_request(client_host: str = "127.0.0.1", user_agent: str = "TestAgent/1.0"):
    """Create a mock FastAPI Request with configurable attributes."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = client_host
    request.headers = {"user-agent": user_agent}
    return request


def _make_request_no_client():
    """Create a mock Request with client=None (e.g., behind proxy)."""
    request = MagicMock()
    request.client = None
    request.headers = {}
    return request


# ──────────────────────────────────────────────────────────────
# log_auth_event
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_auth_event_success():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_auth_event(
            event="magic_link_sent",
            user_id="user-1",
            email="test@example.com",
            request=request,
            success=True,
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert "auth.magic_link_sent" in call_kwargs[0]
        assert call_kwargs[1]["severity"] == "INFO"
        assert call_kwargs[1]["ip_address"] == "127.0.0.1"
        assert call_kwargs[1]["user_agent"] == "TestAgent/1.0"


@pytest.mark.asyncio
async def test_log_auth_event_failure():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_auth_event(
            event="login_failed",
            user_id=None,
            email="bad@example.com",
            request=request,
            success=False,
            details={"reason": "invalid_token"},
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert call_kwargs[1]["severity"] == "WARNING"
        assert call_kwargs[1]["user_id"] is None
        assert call_kwargs[1]["details"] == {"reason": "invalid_token"}


@pytest.mark.asyncio
async def test_log_auth_event_no_client():
    request = _make_request_no_client()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_auth_event(
            event="logout",
            user_id="user-1",
            email="test@example.com",
            request=request,
            success=True,
        )
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args[1]["ip_address"] is None


# ──────────────────────────────────────────────────────────────
# log_data_access
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_data_access_success():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_data_access(
            resource="bien",
            action="create",
            user_id="user-1",
            resource_id="bien-42",
            request=request,
            success=True,
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert "data.bien.create" in call_kwargs[0]
        assert call_kwargs[1]["event_category"] == "data_access"
        assert call_kwargs[1]["severity"] == "INFO"


@pytest.mark.asyncio
async def test_log_data_access_failure():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_data_access(
            resource="loyer",
            action="delete",
            user_id="user-1",
            resource_id=None,
            request=request,
            success=False,
            details={"error": "not_found"},
        )
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args[1]["severity"] == "WARNING"


@pytest.mark.asyncio
async def test_log_data_access_no_client():
    request = _make_request_no_client()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_data_access(
            resource="sci",
            action="read",
            user_id="user-1",
            resource_id="sci-1",
            request=request,
            success=True,
        )
        assert mock_logger.info.call_args[1]["ip_address"] is None


# ──────────────────────────────────────────────────────────────
# log_gdpr_event
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_gdpr_event():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_gdpr_event(
            event="data_export",
            user_id="user-1",
            request=request,
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert "gdpr.data_export" in call_kwargs[0]
        assert call_kwargs[1]["event_category"] == "gdpr_compliance"
        assert call_kwargs[1]["severity"] == "INFO"


@pytest.mark.asyncio
async def test_log_gdpr_event_with_details():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_gdpr_event(
            event="account_delete",
            user_id="user-1",
            request=request,
            details={"tables_cleared": 5},
        )
        assert mock_logger.info.call_args[1]["details"] == {"tables_cleared": 5}


@pytest.mark.asyncio
async def test_log_gdpr_event_no_client():
    request = _make_request_no_client()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_gdpr_event(
            event="consent_update",
            user_id="user-1",
            request=request,
        )
        assert mock_logger.info.call_args[1]["ip_address"] is None


# ──────────────────────────────────────────────────────────────
# log_payment_event
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_payment_event_success():
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_payment_event(
            event="checkout_completed",
            user_id="user-1",
            amount=2900,
            currency="eur",
            stripe_customer_id="cus_123",
            success=True,
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert "payment.checkout_completed" in call_kwargs[0]
        assert call_kwargs[1]["amount"] == 2900
        assert call_kwargs[1]["currency"] == "eur"
        assert call_kwargs[1]["severity"] == "INFO"


@pytest.mark.asyncio
async def test_log_payment_event_failure():
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_payment_event(
            event="payment_failed",
            user_id=None,
            amount=None,
            currency="eur",
            stripe_customer_id=None,
            success=False,
            details={"error": "card_declined"},
        )
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args[1]["severity"] == "WARNING"


# ──────────────────────────────────────────────────────────────
# log_file_event
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_file_event_upload():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_file_event(
            event="upload",
            user_id="user-1",
            file_path="sci-1/bien-2/doc.pdf",
            file_size=1024,
            request=request,
            success=True,
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert "file.upload" in call_kwargs[0]
        assert call_kwargs[1]["file_size"] == 1024


@pytest.mark.asyncio
async def test_log_file_event_delete_failure():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_file_event(
            event="delete",
            user_id="user-1",
            file_path="sci-1/doc.pdf",
            file_size=None,
            request=request,
            success=False,
            details={"error": "not_found"},
        )
        assert mock_logger.info.call_args[1]["severity"] == "WARNING"


@pytest.mark.asyncio
async def test_log_file_event_no_client():
    request = _make_request_no_client()
    with patch("app.core.audit_log.logger") as mock_logger:
        await AuditLogger.log_file_event(
            event="download",
            user_id="user-1",
            file_path="path.pdf",
            file_size=500,
            request=request,
            success=True,
        )
        assert mock_logger.info.call_args[1]["ip_address"] is None


# ──────────────────────────────────────────────────────────────
# log_security_event
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_security_event_info():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        mock_logger.info = MagicMock()
        await AuditLogger.log_security_event(
            event="suspicious_ip",
            user_id="user-1",
            request=request,
            severity="INFO",
            details={"ip_count": 5},
        )
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args[1]["severity"] == "INFO"


@pytest.mark.asyncio
async def test_log_security_event_critical():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        mock_logger.critical = MagicMock()
        await AuditLogger.log_security_event(
            event="brute_force_detected",
            user_id=None,
            request=request,
            severity="CRITICAL",
        )
        mock_logger.critical.assert_called_once()
        call_kwargs = mock_logger.critical.call_args
        assert call_kwargs[1]["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_log_security_event_warning():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        mock_logger.warning = MagicMock()
        await AuditLogger.log_security_event(
            event="rate_limit_exceeded",
            user_id="user-1",
            request=request,
            severity="WARNING",
        )
        mock_logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_log_security_event_no_client():
    request = _make_request_no_client()
    with patch("app.core.audit_log.logger") as mock_logger:
        mock_logger.info = MagicMock()
        await AuditLogger.log_security_event(
            event="test",
            user_id=None,
            request=request,
            severity="INFO",
        )
        assert mock_logger.info.call_args[1]["ip_address"] is None


@pytest.mark.asyncio
async def test_log_security_event_error_severity():
    request = _make_request()
    with patch("app.core.audit_log.logger") as mock_logger:
        mock_logger.error = MagicMock()
        await AuditLogger.log_security_event(
            event="unauthorized_access",
            user_id="user-1",
            request=request,
            severity="ERROR",
            details={"resource": "admin_panel"},
        )
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args[1]["details"] == {"resource": "admin_panel"}
