"""File storage service using Supabase Storage"""
from io import BytesIO
from typing import Optional

import structlog
from supabase import create_client

from app.core.config import settings
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
        """Upload file to storage and return public URL

        Raises:
            ExternalServiceError: Si l'upload échoue
        """
        logger.info("uploading_file", path=file_path, size=len(file_content))

        try:
            self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type},
            )

            # Get public URL
            url = self.client.storage.from_(self.bucket_name).get_public_url(
                file_path
            )

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
            self.client.storage.from_(self.bucket_name).remove([file_path])
            logger.info("file_deleted", path=file_path)
            return True
        except Exception as e:
            logger.error("file_deletion_failed", path=file_path, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Deletion failed: {str(e)}")

    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for a file"""
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)

    async def create_bucket_if_not_exists(self) -> bool:
        """Create documents bucket if it doesn't exist

        Raises:
            ExternalServiceError: Si la création du bucket échoue
        """
        try:
            # Try to list bucket
            self.client.storage.list_buckets()
            return True
        except Exception:
            # Create bucket
            try:
                logger.info("creating_bucket", bucket=self.bucket_name)
                self.client.storage.create_bucket(
                    bucket_id=self.bucket_name,
                    options={"public": True},
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
            files = self.client.storage.from_(self.bucket_name).list(path=folder)
            logger.info("files_listed", folder=folder, count=len(files))
            return files
        except Exception as e:
            logger.error("file_listing_failed", folder=folder, error=str(e), exc_info=True)
            raise ExternalServiceError("Supabase Storage", f"Listing failed: {str(e)}")


# Singleton instance
storage_service = StorageService()
