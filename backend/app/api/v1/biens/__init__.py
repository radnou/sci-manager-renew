"""Module API biens — sous-routes de /scis/{sci_id}/biens.

Structure après split du monolithe scis_biens.py (~2700 lignes → 8 modules).
"""

from fastapi import APIRouter

from .biens_core import router as core_router
from .biens_loyers import router as loyers_router
from .biens_baux import router as baux_router
from .biens_charges import router as charges_router
from .biens_pno import router as pno_router
from .biens_frais import router as frais_router
from .biens_documents import router as documents_router
from .biens_evenements import router as evenements_router

# Router principal qui agrège tous les sous-routers
router = APIRouter(prefix="/scis/{sci_id}/biens", tags=["scis-biens"])

# Inclusion des sous-routers avec leurs préfixes respectifs
router.include_router(core_router)
router.include_router(loyers_router)
router.include_router(baux_router)
router.include_router(charges_router)
router.include_router(pno_router)
router.include_router(frais_router)
router.include_router(documents_router)
router.include_router(evenements_router)
