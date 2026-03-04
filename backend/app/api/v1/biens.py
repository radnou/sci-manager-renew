from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from ...schemas.biens import Bien, BienCreate

router = APIRouter()

# simple in-memory storage
BIENS_DB: List[Bien] = []

@router.get("", response_model=List[Bien])
def list_biens():
    return BIENS_DB

@router.post("", response_model=Bien, status_code=201)
def create_bien(bien: BienCreate):
    new = Bien(id=uuid4(), **bien.dict())
    BIENS_DB.append(new)
    return new
