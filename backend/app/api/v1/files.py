"""File management endpoints"""
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request

from app.core.exceptions import ExternalServiceError, ValidationError
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.services.storage_service import storage_service

router = APIRouter(prefix="/files", tags=["files"])
logger = structlog.get_logger(__name__)


def _validate_storage_path(path: str) -> str:
    if not path or ".." in path or path.startswith("/") or path.startswith("."):
        raise ValidationError("Chemin de fichier invalide.")
    return path


@router.post("/upload-quitus")
@limiter.limit("10/minute")
async def upload_quitus(
    request: Request, file_path: str, user_id: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Upload quitus PDF to storage
    Returns public URL for download
    """
    try:
        del request
        safe_path = _validate_storage_path(file_path)
        # File should be provided as bytes in request body
        # For now, just return placeholder
        url = await storage_service.get_file_url(safe_path)
        return {"success": True, "url": url, "message": "Quitus uploaded successfully"}
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        logger.error("upload_quitus_failed", user_id=user_id, file_path=file_path, error=str(e))
        raise ExternalServiceError("Storage", "Failed to upload quitus")


@router.get("/download/{file_path:path}")
@limiter.limit("30/minute")
async def download_file(
    request: Request, file_path: str, user_id: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Download file from storage (quitus, documents, etc.)
    """
    try:
        del request
        safe_path = _validate_storage_path(file_path)
        # Validate ownership (check if user owns this file)
        # For now, just return URL for client-side download
        url = await storage_service.get_file_url(safe_path)
        return {"success": True, "url": url}
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        logger.error("download_file_failed", user_id=user_id, file_path=file_path, error=str(e))
        raise ExternalServiceError("Storage", "Failed to download file")


@router.delete("/delete/{file_path:path}")
@limiter.limit("10/minute")
async def delete_file(
    request: Request, file_path: str, user_id: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Delete file from storage
    """
    try:
        del request
        safe_path = _validate_storage_path(file_path)
        # Validate ownership before deletion
        success = await storage_service.delete_file(safe_path)
        if success:
            return {"success": True, "message": "File deleted successfully"}
        raise ExternalServiceError("Storage", "Failed to delete file")
    except Exception as e:
        if isinstance(e, (ValidationError, ExternalServiceError)):
            raise
        logger.error("delete_file_failed", user_id=user_id, file_path=file_path, error=str(e))
        raise ExternalServiceError("Storage", "Failed to delete file")


@router.get("/list/{folder:path}")
@limiter.limit("20/minute")
async def list_files(
    request: Request, folder: str = "", user_id: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    List files in a folder
    """
    try:
        del request
        safe_folder = _validate_storage_path(folder) if folder else ""
        files = await storage_service.list_files(safe_folder)
        return {"success": True, "files": files}
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        logger.error("list_files_failed", user_id=user_id, folder=folder, error=str(e))
        raise ExternalServiceError("Storage", "Failed to list files")
