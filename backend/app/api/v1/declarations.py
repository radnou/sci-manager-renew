"""
Routes API pour les déclarations fiscales (2065, 2072).

Endpoints :
- POST /scis/{sci_id}/declaration-2065/generate
- GET /scis/{sci_id}/declaration-2065/{exercice}
- GET /scis/{sci_id}/declaration-2065/{exercice}/pdf
"""

from uuid import UUID
from typing import Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.paywall import AssocieMembership, require_sci_membership
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.services.declaration_2065_service import Declaration2065Service
from app.services.declaration_2065_pdf_service import Declaration2065PdfService

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
    """Récupère une déclaration 2065 existante (la génère si absente)."""
    service = Declaration2065Service()
    
    # Essayer de récupérer depuis la base
    try:
        result = service.client.table("declarations_2065").select("*").eq("id_sci", str(sci_id)).eq("exercice", exercice).execute()
        if result.data:
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
    except Exception:
        # Table non existante ou autre erreur → fallback génération
        pass
    
    # Fallback : générer la déclaration à la volée
    try:
        declaration = await service.generate_declaration(sci_id, exercice)
        return Declaration2065Response(
            sci_id=str(sci_id),
            exercice=exercice,
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
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{exercice}/pdf")
async def get_declaration_2065_pdf(
    sci_id: UUID,
    exercice: int,
    _=Depends(require_sci_membership),
):
    """Télécharge la déclaration 2065 au format PDF CERFA."""
    service = Declaration2065Service()
    
    # Récupérer la déclaration
    result = service.client.table("declarations_2065").select("*").eq("id_sci", str(sci_id)).eq("exercice", exercice).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Déclaration 2065 non trouvée pour l'exercice {exercice}"
        )
    
    # Récupérer le nom de la SCI
    sci_result = service.client.table("sci").select("nom").eq("id", str(sci_id)).execute()
    sci_nom = sci_result.data[0]["nom"] if sci_result.data else ""
    
    # Re-générer la déclaration pour avoir l'objet complet
    declaration = await service.generate_declaration(sci_id, exercice)
    
    # Générer le PDF
    pdf_service = Declaration2065PdfService()
    pdf_bytes = pdf_service.generate(declaration, sci_nom)
    
    safe_nom = sci_nom.replace(" ", "_") if sci_nom else "sci"
    filename = f"declaration_2065_{exercice}_{safe_nom}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
