"""File storage service using Supabase Storage"""
from io import BytesIO

import structlog
from supabase import create_client

from app.core.config import settings
from app.core.external_services import run_with_retry
from app.core.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)


class StorageService:
    """Service for managing files in Supabase Storage"""

    def __init__(self):
        self.client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        self.bucket_name = "documents"

    async def upload_file(
        self, file_path: str, file_content: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file to storage and return storage URL

        Raises:
            ExternalServiceError: Si l'upload échoue
        """
        logger.info("uploading_file", path=file_path, size=len(file_content))

        try:
            await run_with_retry(
                operation="supabase_storage.upload",
                func=lambda: self.client.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=file_content,
                    file_options={"content-type": content_type, "upsert": "true"},
                ),
                allow_retry=False,
                context={"path": file_path, "bucket": self.bucket_name},
            )

            # Keep returning a URL for backward compatibility, even when bucket is private.
            url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)

            logger.info("file_uploaded", path=file_path)
            return url
        except Exception as e:
            logger.error("file_upload_failed", path=file_path, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Upload failed: {str(e)}")

    async def upload_pdf(self, file_path: str, pdf_buffer: BytesIO) -> str:
        """Upload PDF file"""
        pdf_buffer.seek(0)
        return await self.upload_file(
            file_path=file_path, file_content=pdf_buffer.read(), content_type="application/pdf"
        )

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage

        Raises:
            ExternalServiceError: Si la suppression échoue
        """
        logger.info("deleting_file", path=file_path)

        try:
            await run_with_retry(
                operation="supabase_storage.delete",
                func=lambda: self.client.storage.from_(self.bucket_name).remove([file_path]),
                allow_retry=False,
                context={"path": file_path, "bucket": self.bucket_name},
            )
            logger.info("file_deleted", path=file_path)
            return True
        except Exception as e:
            logger.error("file_deletion_failed", path=file_path, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Deletion failed: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        """Download file from storage.

        Raises:
            ExternalServiceError: Si le téléchargement échoue
        """
        logger.info("downloading_file", path=file_path)

        try:
            content = await run_with_retry(
                operation="supabase_storage.download",
                func=lambda: self.client.storage.from_(self.bucket_name).download(file_path),
                context={"path": file_path, "bucket": self.bucket_name},
            )
            logger.info("file_downloaded", path=file_path, size=len(content))
            return content
        except Exception as e:
            logger.error("file_download_failed", path=file_path, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Download failed: {str(e)}")

    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for a file"""
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)

    async def create_signed_url(self, file_path: str, expires_in: int = 300) -> str:
        """Create a temporary signed URL for a private object.

        Raises:
            ExternalServiceError: Si la génération d'URL signée échoue
        """
        logger.info("creating_signed_url", path=file_path, expires_in=expires_in)

        try:
            payload = await run_with_retry(
                operation="supabase_storage.create_signed_url",
                func=lambda: self.client.storage.from_(self.bucket_name).create_signed_url(
                    file_path,
                    expires_in,
                ),
                context={"path": file_path, "bucket": self.bucket_name},
            )
        except Exception as e:
            logger.error("signed_url_creation_failed", path=file_path, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Signed URL creation failed: {str(e)}")

        url: str | None = None
        if isinstance(payload, dict):
            url = (
                payload.get("signedURL")
                or payload.get("signedUrl")
                or payload.get("signed_url")
            )
        elif isinstance(payload, str):
            url = payload

        if not url:
            raise ExternalServiceError("Supabase Storage", "Signed URL creation failed: empty URL")

        # Supabase may return an absolute URL or a relative /storage path.
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("/"):
            return f"{settings.supabase_url.rstrip('/')}/storage/v1{url}"
        return f"{settings.supabase_url.rstrip('/')}/storage/v1/{url.lstrip('/')}"

    async def create_bucket_if_not_exists(self) -> bool:
        """Create documents bucket if it doesn't exist

        Raises:
            ExternalServiceError: Si la création du bucket échoue
        """
        try:
            buckets = await run_with_retry(
                operation="supabase_storage.list_buckets",
                func=lambda: self.client.storage.list_buckets() or [],
                context={"bucket": self.bucket_name},
            )
        except Exception as e:
            logger.error("bucket_listing_failed", bucket=self.bucket_name, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Bucket listing failed: {str(e)}")

        for bucket in buckets:
            bucket_id = bucket.get("id") if isinstance(bucket, dict) else getattr(bucket, "id", None)
            if bucket_id == self.bucket_name:
                return True

        try:
            logger.info("creating_bucket", bucket=self.bucket_name)
            await run_with_retry(
                operation="supabase_storage.create_bucket",
                func=lambda: self.client.storage.create_bucket(
                    id=self.bucket_name,
                    options={"public": False},
                ),
                allow_retry=False,
                context={"bucket": self.bucket_name},
            )
            logger.info("bucket_created", bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.error("bucket_creation_failed", bucket=self.bucket_name, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Bucket creation failed: {str(e)}")

    async def list_files(self, folder: str = "") -> list[dict]:
        """List files in a folder

        Raises:
            ExternalServiceError: Si le listing échoue
        """
        logger.info("listing_files", folder=folder)

        try:
            files = await run_with_retry(
                operation="supabase_storage.list_files",
                func=lambda: self.client.storage.from_(self.bucket_name).list(path=folder),
                context={"bucket": self.bucket_name, "folder": folder},
            )
            logger.info("files_listed", folder=folder, count=len(files))
            return files
        except Exception as e:
            logger.error("file_listing_failed", folder=folder, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Listing failed: {str(e)}")


# Singleton instance
storage_service = StorageService()
