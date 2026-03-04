"""File storage service using Supabase Storage"""
from io import BytesIO
from typing import Optional

from supabase import create_client

from app.core.config import settings


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
        """Upload file to storage and return public URL"""
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

            return url
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    async def upload_pdf(self, file_path: str, pdf_buffer: BytesIO) -> str:
        """Upload PDF file"""
        pdf_buffer.seek(0)
        return await self.upload_file(
            file_path=file_path, file_content=pdf_buffer.read(), content_type="application/pdf"
        )

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for a file"""
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)

    async def create_bucket_if_not_exists(self) -> bool:
        """Create documents bucket if it doesn't exist"""
        try:
            # Try to list bucket
            self.client.storage.list_buckets()
            return True
        except Exception:
            # Create bucket
            try:
                self.client.storage.create_bucket(
                    bucket_id=self.bucket_name,
                    options={"public": True},
                )
                return True
            except Exception as e:
                raise Exception(f"Failed to create bucket: {str(e)}")

    async def list_files(self, folder: str = "") -> list[dict]:
        """List files in a folder"""
        try:
            files = self.client.storage.from_(self.bucket_name).list(path=folder)
            return files
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")


# Singleton instance
storage_service = StorageService()
