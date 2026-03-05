# backend/tests/test_service_exceptions.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.storage_service import StorageService
from app.services.email_service import EmailService
from app.core.exceptions import ExternalServiceError


@pytest.mark.asyncio
async def test_storage_service_raises_external_service_error_on_upload_failure():
    """Test que StorageService lève ExternalServiceError en cas d'échec d'upload"""
    service = StorageService()

    # Mock Supabase client pour simuler une erreur
    with patch.object(service.client.storage, 'from_') as mock_from:
        mock_bucket = Mock()
        mock_bucket.upload.side_effect = Exception("Network timeout")
        mock_from.return_value = mock_bucket

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.upload_file("test.pdf", b"content")

        assert "Supabase Storage" in str(exc_info.value)
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_storage_service_raises_external_service_error_on_delete_failure():
    """Test que StorageService lève ExternalServiceError en cas d'échec de suppression"""
    service = StorageService()

    with patch.object(service.client.storage, 'from_') as mock_from:
        mock_bucket = Mock()
        mock_bucket.remove.side_effect = Exception("Storage full")
        mock_from.return_value = mock_bucket

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.delete_file("test.pdf")

        assert "Supabase Storage" in str(exc_info.value)
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_storage_service_raises_external_service_error_on_list_failure():
    """Test que StorageService lève ExternalServiceError en cas d'échec de listing"""
    service = StorageService()

    with patch.object(service.client.storage, 'from_') as mock_from:
        mock_bucket = Mock()
        mock_bucket.list.side_effect = Exception("Bucket not accessible")
        mock_from.return_value = mock_bucket

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.list_files()

        assert "Supabase Storage" in str(exc_info.value)
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_email_service_raises_external_service_error_on_magic_link_failure():
    """Test que EmailService lève ExternalServiceError en cas d'échec d'envoi de magic link"""
    service = EmailService()

    with patch('resend.Emails.send') as mock_send:
        mock_send.side_effect = Exception("API key invalid")

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.send_magic_link("test@example.com", "https://link")

        assert "Resend" in str(exc_info.value)
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_email_service_raises_external_service_error_on_welcome_failure():
    """Test que EmailService lève ExternalServiceError en cas d'échec d'envoi de welcome"""
    service = EmailService()

    with patch('resend.Emails.send') as mock_send:
        mock_send.side_effect = Exception("Rate limit exceeded")

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.send_welcome("test@example.com", "John Doe")

        assert "Resend" in str(exc_info.value)
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_email_service_raises_external_service_error_on_quitus_notification_failure():
    """Test que EmailService lève ExternalServiceError en cas d'échec de notification quitus"""
    service = EmailService()

    with patch('resend.Emails.send') as mock_send:
        mock_send.side_effect = Exception("Network error")

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.send_quitus_generated("test@example.com", "123 rue Test")

        assert "Resend" in str(exc_info.value)
        assert exc_info.value.status_code == 503
