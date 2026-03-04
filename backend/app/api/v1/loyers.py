from fastapi import APIRouter
from typing import List

from ...schemas.loyers import Loyer, LoyerCreate
from ...services import loyers_service

router = APIRouter()


@router.get("", response_model=List[Loyer])
def list_loyers():
    return loyers_service.list_loyers()


@router.post("", response_model=Loyer, status_code=201)
def create_loyer(loyer: LoyerCreate):
    return loyers_service.create_loyer(loyer)
