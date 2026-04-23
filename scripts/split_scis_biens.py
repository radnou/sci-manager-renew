#!/usr/bin/env python3
"""
Split scis_biens.py monolithe en modules domaine.
Usage: python split_scis_biens.py
"""

import re
from pathlib import Path

SRC = Path("scis_biens.py")
BACKEND = Path(__file__).parent.parent / "backend" / "app" / "api" / "v1"

def read_source():
    return (BACKEND / SRC).read_text()

def extract_lines(content: str, start: int, end: int) -> str:
    lines = content.splitlines()
    return "\n".join(lines[start-1:end])

def main():
    content = read_source()
    
    # Détection des sections par route
    sections = {
        "biens_core": (1, 509),      # Imports + CRUD biens
        "biens_loyers": (510, 585),   # Loyers
        "biens_baux": (586, 1215),    # Baux + locataires + régularisations + avenants
        "biens_charges": (1216, 1349), # Charges
        "biens_pno": (1350, 1482),    # Assurance PNO
        "biens_frais": (1483, 1573),   # Frais agence
        "biens_documents": (1574, 1742), # Documents
        "biens_evenements": (1743, 2132), # Événements + obligations + sinistres
    }
    
    imports = """from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel

from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client
from app.core.exceptions import DatabaseError, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.services.subscription_service import SubscriptionService
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.models.charges import ChargeCreate, ChargeResponse, ChargeUpdate
from app.models.evenements import EvenementCreate, EvenementResponse, EvenementUpdate
from app.models.loyers import LoyerCreate, LoyerResponse
from app.schemas.assurance_pno import AssurancePnoCreate, AssurancePnoResponse, AssurancePnoUpdate
from app.schemas.baux import BailCreate, BailResponse, BailUpdate
from app.schemas.documents import DocumentBienResponse
from app.schemas.fiche_bien import FicheBienResponse, RentabiliteCalculee
from app.schemas.frais_agence import FraisAgenceCreate, FraisAgenceResponse
from app.services.document_links import create_document_signed_url, extract_document_storage_path
from app.services.rentabilite_service import calculate_rentabilite

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/biens", tags=["scis-biens"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    return get_supabase_service_client()


def _verify_bien_belongs_to_sci(client, bien_id: str, sci_id: str) -> dict:
    result = client.table("biens").select("*").eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    rows = result.data or []
    if not rows:
        raise ResourceNotFoundError("Bien", bien_id)
    bien = rows[0]
    if str(bien.get("id_sci", "")) != sci_id:
        raise ResourceNotFoundError("Bien", bien_id)
    return bien
"""
    
    for name, (start, end) in sections.items():
        module_code = imports + "\n\n" + extract_lines(content, start, end)
        target = BACKEND / f"{name}.py"
        target.write_text(module_code)
        print(f"✅ {target} ({len(module_code.splitlines())} lignes)")
    
    # Backup original
    backup = BACKEND / "scis_biens.py.bak"
    (BACKEND / SRC).rename(backup)
    print(f"📦 Backup: {backup}")
    
    # Create __init__.py for new module registration
    init_content = """# API v1 biens sub-modules
from .biens_core import router as biens_core_router
from .biens_loyers import router as biens_loyers_router
from .biens_baux import router as biens_baux_router
from .biens_charges import router as biens_charges_router
from .biens_pno import router as biens_pno_router
from .biens_frais import router as biens_frais_router
from .biens_documents import router as biens_documents_router
from .biens_evenements import router as biens_evenements_router
"""
    (BACKEND / "__init__biens.py").write_text(init_content)
    
    print("\n🎉 Split terminé !")
    print("📋 Modules créés :")
    for name in sections:
        print(f"   - {name}.py")
    print("\n⚠️  Prochaines étapes :")
    print("   1. Vérifier les imports croisés")
    print("   2. Mettre à jour app/main.py pour inclure les nouveaux routers")
    print("   3. Supprimer scis_biens.py.bak après validation")

if __name__ == "__main__":
    main()
