from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.security import get_current_user
from app.models.quitus import QuitusRequest, QuitusResponse
from app.services.quitus_service import QuitusService
from app.services.storage_service import storage_service

router = APIRouter(prefix="/quitus", tags=["quitus"])


def _validate_filename(filename: str) -> str:
    if (
        not filename
        or "/" in filename
        or "\\" in filename
        or filename.startswith(".")
        or ".." in filename
    ):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return filename


@router.post("/generate", response_model=QuitusResponse)
async def generate_quitus(payload: QuitusRequest, user_id: str = Depends(get_current_user)):
    pdf_bytes = QuitusService.generate_quitus_pdf(payload)
    filename = f"quitus-{uuid4().hex}.pdf"
    storage_path = f"quitus/{user_id}/{filename}"

    await storage_service.create_bucket_if_not_exists()
    await storage_service.upload_file(
        file_path=storage_path,
        file_content=pdf_bytes,
        content_type="application/pdf",
    )

    return {
        "filename": filename,
        "pdf_url": f"/api/v1/quitus/files/{filename}",
        "size_bytes": len(pdf_bytes),
    }


@router.get("/files/{filename}")
async def download_quitus(filename: str, user_id: str = Depends(get_current_user)):
    safe_filename = _validate_filename(filename)
    storage_path = f"quitus/{user_id}/{safe_filename}"

    try:
        pdf_bytes = await storage_service.download_file(storage_path)
    except Exception as exc:
        # Supabase client errors for missing files are mapped to 404 for UX.
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail="File not found") from exc
        raise

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_filename}"'},
    )
