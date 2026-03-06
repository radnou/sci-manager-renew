from __future__ import annotations

import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.rate_limit import limiter
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


def _build_inline_filename(periode: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", periode.lower()).strip("-")
    return f"quittance-{slug or 'periode'}.pdf"


@router.post("/generate", response_model=QuitusResponse)
@limiter.limit("15/minute")
async def generate_quitus(
    request: Request, payload: QuitusRequest, user_id: str = Depends(get_current_user)
):
    del request
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


@router.post("/render")
@limiter.limit("20/minute")
async def render_quitus(request: Request, payload: QuitusRequest, user_id: str = Depends(get_current_user)):
    del request
    del user_id

    pdf_bytes = QuitusService.generate_quitus_pdf(payload)
    filename = _build_inline_filename(payload.periode)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/files/{filename}")
@limiter.limit("30/minute")
async def download_quitus(request: Request, filename: str, user_id: str = Depends(get_current_user)):
    del request
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
