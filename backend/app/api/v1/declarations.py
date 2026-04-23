"""
Routes API pour les déclarations fiscales (2065, 2072).

Endpoints :
- POST /scis/{sci_id}/declaration-2065/generate
- GET /scis/{sci_id}/declaration-2065/{exercice}
- GET /scis/{sci_id}/declaration-2065/{exercice}/pdf
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.core.dependencies import require_sci_membership
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.services.declaration_2065_service import Declaration2065Service

router = APIRouter(prefix="/scis/{sci_id}/declaration-2065", tags=["declarations"])

# ──────────────────────────────────────────────────────────────
# Schémas
# ──────────────────────────────────────────────────────────────


class Declaration2065GenerateRequest(BaseModel):
    exercice: int = Query(..., ge=2000, le=2100, description="Année fiscale")
    tresorerie: Optional[float] = None
    reserves: Optional[float] = None


class Declaration2065Response(BaseModel):
    sci_id: str
    exercice: int
    date_cloture: str
    actif: dict
    passif: dict
    ecart: float
    message: str = "Bilan équilibré"


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.post("/generate", response_model=Declaration2065Response)
async def generate_declaration_2065(
    sci_id: UUID,
    request: Declaration2065GenerateRequest,
    _=Depends(require_sci_membership),
):
    """Génère une déclaration 2065 pré-remplie pour une SCI."""
    service = Declaration2065Service()
    
    try:
        declaration = await service.generate_declaration(
            sci_id=sci_id,
            exercice=request.exercice,
            trésorerie=request.tresorerie,
            réserves=request.reserves,
        )
        
        # Sauvegarde en base
        await service.save_declaration(declaration)
        
        return Declaration2065Response(
            sci_id=str(declaration.sci_id),
            exercice=declaration.exercice,
            date_cloture=declaration.date_cloture.isoformat(),
            actif={
                "immobilisations": float(declaration.actif.immobilisations_corporelles),
                "creances": float(declaration.actif.créances_clients),
                "tresorerie": float(declaration.actif.trésorerie_actif),
                "total": float(declaration.actif.total_actif),
            },
            passif={
                "capital": float(declaration.passif.capital_social),
                "resultat": float(declaration.passif.résultat_exercice),
                "emprunts": float(declaration.passif.emprunts),
                "total": float(declaration.passif.total_passif),
            },
            ecart=float(declaration.écart),
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{exercice}", response_model=Declaration2065Response)
async def get_declaration_2065(
    sci_id: UUID,
    exercice: int,
    _=Depends(require_sci_membership),
):
    """Récupère une déclaration 2065 existante."""
    service = Declaration2065Service()
    
    # Récupération depuis la base
    result = service.client.table("declarations_2065").select("*").eq("id_sci", str(sci_id)).eq("exercice", exercice).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Déclaration 2065 non trouvée pour l'exercice {exercice}"
        )
    
    data = result.data[0]
    return Declaration2065Response(
        sci_id=str(sci_id),
        exercice=exercice,
        date_cloture=data.get("date_cloture", ""),
        actif={
            "immobilisations": data.get("actif_immobilisations", 0),
            "creances": data.get("actif_creances", 0),
            "tresorerie": data.get("actif_tresorerie", 0),
            "total": sum([
                data.get("actif_immobilisations", 0) or 0,
                data.get("actif_creances", 0) or 0,
                data.get("actif_tresorerie", 0) or 0,
            ]),
        },
        passif={
            "capital": data.get("passif_capital", 0),
            "resultat": data.get("passif_resultat", 0),
            "emprunts": data.get("passif_emprunts", 0),
            "total": sum([
                data.get("passif_capital", 0) or 0,
                data.get("passif_resultat", 0) or 0,
                data.get("passif_emprunts", 0) or 0,
            ]),
        },
        ecart=data.get("ecart", 0),
    )


@router.get("/{exercice}/pdf")
async def get_declaration_2065_pdf(
    sci_id: UUID,
    exercice: int,
    _=Depends(require_sci_membership),
):
    """Télécharge la déclaration 2065 au format PDF (placeholder)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Génération PDF en cours de développement. Utilisez les données JSON."
    )
