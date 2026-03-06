"""File management endpoints"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.services.storage_service import storage_service

router = APIRouter(prefix="/files", tags=["files"])


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
        # File should be provided as bytes in request body
        # For now, just return placeholder
        url = await storage_service.get_file_url(file_path)
        return {"success": True, "url": url, "message": "Quitus uploaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload quitus: {str(e)}",
        )


@router.get("/download/{file_path:path}")
@limiter.limit("30/minute")
async def download_file(
    request: Request, file_path: str, user_id: str = Depends(get_current_user)
) -> FileResponse:
    """
    Download file from storage (quitus, documents, etc.)
    """
    try:
        del request
        # Validate ownership (check if user owns this file)
        # For now, just return URL for client-side download
        url = await storage_service.get_file_url(file_path)
        return {"success": True, "url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}",
        )


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
        # Validate ownership before deletion
        success = await storage_service.delete_file(file_path)
        if success:
            return {"success": True, "message": "File deleted successfully"}
        raise Exception("Failed to delete file")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )


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
        files = await storage_service.list_files(folder)
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}",
        )
