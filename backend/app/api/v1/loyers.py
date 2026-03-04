from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from ...schemas.loyers import Loyer, LoyerCreate

router = APIRouter()

LOYERS_DB: List[Loyer] = []

@router.get("", response_model=List[Loyer])
def list_loyers():
    return LOYERS_DB

@router.post("", response_model=Loyer, status_code=201)
def create_loyer(loyer: LoyerCreate):
    new = Loyer(id=uuid4(), **loyer.dict())
    LOYERS_DB.append(new)
    return new
