from fastapi import APIRouter
from typing import List

from ...schemas.biens import Bien, BienCreate
from ...services import biens_service

router = APIRouter()


@router.get("", response_model=List[Bien])
def list_biens():
    """Return all biens from the database via the service layer."""
    return biens_service.list_biens()


@router.post("", response_model=Bien, status_code=201)
def create_bien(bien: BienCreate):
    """Create a new bien record using the service layer."""
    return biens_service.create_bien(bien)
