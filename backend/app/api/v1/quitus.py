from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.security import get_current_user
from app.models.quitus import QuitusRequest, QuitusResponse
from app.services.quitus_service import QuitusService

router = APIRouter(prefix="/quitus", tags=["quitus"])

_generated_quitus: dict[str, tuple[str, bytes]] = {}


@router.post("/generate", response_model=QuitusResponse)
async def generate_quitus(
    request: QuitusRequest,
    user_id: str = Depends(get_current_user),
) -> QuitusResponse:
    del user_id
    pdf_bytes = QuitusService.generate_quitus_pdf(request)
    file_id = uuid4().hex
    filename = f"quitus-{request.id_loyer}.pdf"
    _generated_quitus[file_id] = (filename, pdf_bytes)

    return QuitusResponse(
        filename=filename,
        pdf_url=f"/api/v1/quitus/files/{file_id}",
        size_bytes=len(pdf_bytes),
    )


@router.get("/files/{file_id}")
async def download_quitus(
    file_id: str,
    user_id: str = Depends(get_current_user),
) -> Response:
    del user_id
    payload = _generated_quitus.get(file_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quittus not found")

    filename, pdf_bytes = payload
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
