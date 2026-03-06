from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import FeatureDisabledError
from app.core.security import get_current_user

router = APIRouter(prefix="/cerfa", tags=["cerfa"])


class Cerfa2044Request(BaseModel):
    annee: int = Field(ge=2000, le=2100)
    total_revenus: float = Field(ge=0)
    total_charges: float = Field(ge=0)


@router.post("/2044")
async def generate_cerfa_2044(
    payload: Cerfa2044Request,
    user_id: str = Depends(get_current_user),
) -> dict[str, float | int | str]:
    del user_id
    if not settings.feature_cerfa_generation:
        raise FeatureDisabledError(
            "La génération Cerfa est désactivée.",
            flag_name="feature_cerfa_generation",
        )
    resultat_fiscal = round(payload.total_revenus - payload.total_charges, 2)
    return {
        "status": "generated",
        "annee": payload.annee,
        "total_revenus": payload.total_revenus,
        "total_charges": payload.total_charges,
        "resultat_fiscal": resultat_fiscal,
        "formulaire": "cerfa_2044",
    }
