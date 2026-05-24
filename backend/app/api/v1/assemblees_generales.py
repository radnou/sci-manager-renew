"""CRUD API for assemblees generales (general assembly registry) under /scis/{sci_id}/assemblees-generales."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field

from app.core.exceptions import DatabaseError, GererSCIException, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/assemblees-generales", tags=["assemblees-generales"])


# ──────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────


class AGCreate(BaseModel):
    date_ag: date
    type_ag: str = Field(..., min_length=1, max_length=50)
    exercice_annee: int = Field(..., ge=2000, le=2100)
    ordre_du_jour: Optional[str] = None
    pv_url: Optional[str] = None
    quorum_atteint: bool = False
    resolutions: Optional[str] = None
    notes: Optional[str] = None


class AGResponse(BaseModel):
    id: str
    id_sci: str
    date_ag: date
    type_ag: str
    exercice_annee: int
    ordre_du_jour: Optional[str] = None
    pv_url: Optional[str] = None
    quorum_atteint: bool
    resolutions: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _get_client(request: Request):
    return get_supabase_user_client(request)


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("", response_model=list[AGResponse])
@router.get("/", response_model=list[AGResponse])
async def list_assemblees_generales(
    request: Request,
    sci_id: UUID,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """List all general assemblies for a given SCI."""
    logger.info("listing_assemblees_generales", sci_id=str(sci_id), user_id=membership.user_id)

    try:
        client = _get_client(request)
        result = client.table("assemblees_generales").select("*").eq("id_sci", str(sci_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        rows.sort(key=lambda r: str(r.get("date_ag", "")), reverse=True)
        return rows
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("list_assemblees_generales_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list assemblees generales")


@router.post("", response_model=AGResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AGResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_assemblee_generale(
    request: Request,
    sci_id: UUID,
    payload: AGCreate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Create a new general assembly record. Requires gerant role."""
    logger.info(
        "creating_assemblee_generale",
        sci_id=str(sci_id),
        user_id=membership.user_id,
        type_ag=payload.type_ag,
        exercice_annee=payload.exercice_annee,
    )

    try:
        client = _get_client(request)
        insert_data = payload.model_dump(mode="json")
        insert_data["id_sci"] = str(sci_id)

        write_client = _get_client(request)
        result = write_client.table("assemblees_generales").insert(insert_data).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create assemblee generale")

        return rows[0]
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("create_assemblee_generale_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create assemblee generale")


@router.patch("/{ag_id}", response_model=AGResponse)
@limiter.limit("30/minute")
async def update_assemblee_generale(
    request: Request,
    sci_id: UUID,
    ag_id: UUID,
    payload: AGCreate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Update an existing general assembly record. Requires gerant role."""
    logger.info(
        "updating_assemblee_generale",
        sci_id=str(sci_id),
        ag_id=str(ag_id),
        user_id=membership.user_id,
    )

    try:
        client = _get_client(request)

        # Verify the AG exists and belongs to this SCI
        check = client.table("assemblees_generales").select("id").eq("id", str(ag_id)).eq("id_sci", str(sci_id)).execute()
        if getattr(check, "error", None):
            raise DatabaseError(str(check.error))
        if not (check.data or []):
            raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

        update_data = payload.model_dump(mode="json")
        result = client.table("assemblees_generales").update(update_data).eq("id", str(ag_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

        return rows[0]
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("update_assemblee_generale_failed", ag_id=str(ag_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update assemblee generale")


@router.delete("/{ag_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_assemblee_generale(
    request: Request,
    sci_id: UUID,
    ag_id: UUID,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Delete a general assembly record. Requires gerant role."""
    logger.info(
        "deleting_assemblee_generale",
        sci_id=str(sci_id),
        ag_id=str(ag_id),
        user_id=membership.user_id,
    )

    try:
        client = _get_client(request)

        # Verify the AG exists and belongs to this SCI
        check = client.table("assemblees_generales").select("id").eq("id", str(ag_id)).eq("id_sci", str(sci_id)).execute()
        if getattr(check, "error", None):
            raise DatabaseError(str(check.error))
        if not (check.data or []):
            raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

        result = client.table("assemblees_generales").delete().eq("id", str(ag_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("delete_assemblee_generale_failed", ag_id=str(ag_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete assemblee generale")


# ──────────────────────────────────────────────────────────────
# MODELE PV d'AG pré-rempli
# ──────────────────────────────────────────────────────────────

_MODELES_AG = {
    "ago_approbation_comptes": {
        "type_ag": "ordinaire",
        "ordre_du_jour": (
            "1. Approbation des comptes de l'exercice {annee}\n"
            "2. Affectation du résultat\n"
            "3. Quitus au gérant\n"
            "4. Questions diverses"
        ),
        "resolutions_modele": (
            "Résolution 1 : L'assemblée approuve les comptes de l'exercice {annee} "
            "tels que présentés par le gérant, faisant apparaître un résultat de {resultat} €.\n\n"
            "Résolution 2 : L'assemblée décide d'affecter le résultat de {resultat} € "
            "en report à nouveau.\n\n"
            "Résolution 3 : L'assemblée donne quitus au gérant, {nom_gerant}, "
            "pour sa gestion au cours de l'exercice {annee}."
        ),
        "quorum_requis": "Selon statuts (défaut: majorité des parts)",
    },
    "age_modification_statuts": {
        "type_ag": "extraordinaire",
        "ordre_du_jour": (
            "1. Modification des statuts\n"
            "2. Mise à jour de l'objet social\n"
            "3. Questions diverses"
        ),
        "resolutions_modele": (
            "Résolution 1 : L'assemblée décide de modifier l'article {article} des statuts "
            "de la société {nom_sci} comme suit : [détails de la modification].\n\n"
            "Résolution 2 : L'assemblée donne tous pouvoirs au gérant, {nom_gerant}, "
            "pour accomplir les formalités légales résultant de cette modification."
        ),
        "quorum_requis": "Unanimité des associés (sauf clause statutaire contraire)",
    },
    "age_cession_parts": {
        "type_ag": "extraordinaire",
        "ordre_du_jour": (
            "1. Agrément de la cession de parts sociales\n"
            "2. Mise à jour du registre des associés\n"
            "3. Modification des statuts en conséquence\n"
            "4. Questions diverses"
        ),
        "resolutions_modele": (
            "Résolution 1 : L'assemblée agrée la cession de {nb_parts} parts sociales "
            "par {cedant} au profit de {cessionnaire} au prix de {prix_unitaire} € par part, "
            "soit un prix total de {prix_total} €.\n\n"
            "Résolution 2 : L'assemblée prend acte de la nouvelle répartition du capital social "
            "et donne tous pouvoirs au gérant, {nom_gerant}, pour mettre à jour les statuts."
        ),
        "quorum_requis": "Unanimité des associés (art. 1861 C.civ, sauf clause statutaire)",
    },
}


class ModeleAGResponse(BaseModel):
    type_ag: str
    ordre_du_jour: str
    resolutions_modele: str
    date_ag_suggeree: str
    quorum_requis: str


@router.get("/modele/{type_modele}", response_model=ModeleAGResponse)
async def get_modele_ag(
    request: Request,
    sci_id: UUID,
    type_modele: str,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Return a pre-filled AG template with actual SCI data."""
    if type_modele not in _MODELES_AG:
        raise ValidationError(
            f"Type de modèle invalide. Valeurs acceptées : {', '.join(_MODELES_AG.keys())}"
        )

    logger.info("get_modele_ag", sci_id=str(sci_id), type_modele=type_modele)

    client = _get_client(request)

    # Fetch SCI data
    sci_result = client.table("sci").select("*").eq("id", str(sci_id)).execute()
    sci = (sci_result.data or [{}])[0] if sci_result.data else {}

    nom_sci = sci.get("nom", "")
    nom_gerant = sci.get("nom_gerant", "Le Gérant")

    # Fetch latest fiscalite to get resultat
    fisc_result = (
        client.table("fiscalite")
        .select("annee, resultat_fiscal")
        .eq("id_sci", str(sci_id))
        .order("annee", desc=True)
        .limit(1)
        .execute()
    )
    last_fisc = (fisc_result.data or [{}])[0] if fisc_result.data else {}
    annee = last_fisc.get("annee", date.today().year - 1)
    resultat = last_fisc.get("resultat_fiscal", 0) or 0

    # Calculate date_ag_suggeree: 6 months after fiscal year end (Dec 31)
    date_cloture = date(int(annee), 12, 31)
    date_ag_suggeree = date_cloture + timedelta(days=183)

    modele = _MODELES_AG[type_modele]

    # Format template strings
    format_vars = {
        "annee": str(annee),
        "resultat": f"{resultat:,.2f}".replace(",", " "),
        "nom_gerant": nom_gerant,
        "nom_sci": nom_sci,
        "article": "XX",
        "nb_parts": "___",
        "cedant": "___",
        "cessionnaire": "___",
        "prix_unitaire": "___",
        "prix_total": "___",
    }

    return ModeleAGResponse(
        type_ag=modele["type_ag"],
        ordre_du_jour=modele["ordre_du_jour"].format(**format_vars),
        resolutions_modele=modele["resolutions_modele"].format(**format_vars),
        date_ag_suggeree=date_ag_suggeree.isoformat(),
        quorum_requis=modele["quorum_requis"],
    )


# ──────────────────────────────────────────────────────────────
# CONVOCATION AG
# ──────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────
# Feuille de presence models
# ──────────────────────────────────────────────────────────────


class AssociePresence(BaseModel):
    associe_id: str
    nom: str
    nb_parts: float = 0
    pct: float = 0
    present: Optional[bool] = None


class FeuillePresenceResponse(BaseModel):
    sci_nom: str
    date_ag: str
    type_ag: str
    associes: list[AssociePresence] = []
    total_parts: float = 0
    quorum_requis: str = "Majorite des parts (>50%)"
    quorum_atteint: Optional[bool] = None


class PresenceItem(BaseModel):
    associe_id: str
    present: bool


class PresenceUpdatePayload(BaseModel):
    presences: list[PresenceItem]


class PresenceUpdateResponse(BaseModel):
    quorum_atteint: bool
    parts_presentes: float
    total_parts: float
    pourcentage_present: float


class ConvocationAGResponse(BaseModel):
    texte_convocation: str
    date_limite_envoi: str
    date_ag: str
    associes_destinataires: list[dict]


@router.post("/{ag_id}/convocation", response_model=ConvocationAGResponse)
@limiter.limit("30/minute")
async def generate_convocation_ag(
    request: Request,
    sci_id: UUID,
    ag_id: UUID,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Generate convocation letter text for a general assembly."""
    logger.info("generate_convocation_ag", sci_id=str(sci_id), ag_id=str(ag_id))

    client = _get_client(request)

    # Fetch AG
    ag_result = (
        client.table("assemblees_generales")
        .select("*")
        .eq("id", str(ag_id))
        .eq("id_sci", str(sci_id))
        .execute()
    )
    if not (ag_result.data or []):
        raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

    ag = ag_result.data[0]

    # Fetch SCI
    sci_result = client.table("sci").select("*").eq("id", str(sci_id)).execute()
    sci = (sci_result.data or [{}])[0] if sci_result.data else {}

    # Fetch associes for this SCI
    assoc_result = (
        client.table("associes")
        .select("nom, email, part")
        .eq("id_sci", str(sci_id))
        .execute()
    )
    associes = assoc_result.data or []

    nom_sci = sci.get("nom", "")
    adresse_siege = sci.get("adresse_siege", "")
    nom_gerant = sci.get("nom_gerant", "Le Gérant")
    date_ag = ag.get("date_ag", "")
    type_ag = ag.get("type_ag", "ordinaire")
    ordre_du_jour = ag.get("ordre_du_jour", "")

    today_str = date.today().isoformat()

    # Date limite envoi: date_ag - 15 jours (art. 1856 C.civ)
    try:
        ag_date_obj = date.fromisoformat(str(date_ag))
        date_limite = ag_date_obj - timedelta(days=15)
    except (ValueError, TypeError):
        date_limite = date.today()

    # Build convocation text
    type_label = "Ordinaire" if type_ag == "ordinaire" else "Extraordinaire"
    texte = (
        f"{nom_sci}\n"
        f"{adresse_siege}\n\n"
        f"Le {today_str}\n\n"
        f"Objet : Convocation à l'Assemblée Générale {type_label}\n\n"
        f"Madame, Monsieur,\n\n"
        f"Vous êtes convoqué(e) à l'Assemblée Générale {type_label} de la société {nom_sci} "
        f"qui se tiendra le {date_ag} au siège social.\n\n"
        f"Ordre du jour :\n{ordre_du_jour}\n\n"
        f"Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.\n\n"
        f"Le Gérant,\n"
        f"{nom_gerant}"
    )

    return ConvocationAGResponse(
        texte_convocation=texte,
        date_limite_envoi=date_limite.isoformat(),
        date_ag=str(date_ag),
        associes_destinataires=associes,
    )


# ──────────────────────────────────────────────────────────────
# FEUILLE DE PRESENCE AG
# ──────────────────────────────────────────────────────────────


@router.get("/{ag_id}/feuille-presence", response_model=FeuillePresenceResponse)
async def get_feuille_presence(
    request: Request,
    sci_id: UUID,
    ag_id: UUID,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Return the attendance sheet for a general assembly."""
    logger.info("get_feuille_presence", sci_id=str(sci_id), ag_id=str(ag_id))

    client = _get_client(request)

    # Fetch AG
    ag_result = (
        client.table("assemblees_generales")
        .select("*")
        .eq("id", str(ag_id))
        .eq("id_sci", str(sci_id))
        .execute()
    )
    if not (ag_result.data or []):
        raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))
    ag = ag_result.data[0]

    # Fetch SCI
    sci_result = client.table("sci").select("nom").eq("id", str(sci_id)).execute()
    sci_nom = (sci_result.data or [{}])[0].get("nom", "") if sci_result.data else ""

    # Fetch associes for this SCI
    assoc_result = (
        client.table("associes")
        .select("id, nom, part")
        .eq("id_sci", str(sci_id))
        .execute()
    )
    associes = assoc_result.data or []

    total_parts = sum(float(a.get("part") or 0) for a in associes)

    associes_presence = []
    for a in associes:
        nb_parts = float(a.get("part") or 0)
        pct = round(nb_parts / total_parts * 100, 2) if total_parts > 0 else 0
        associes_presence.append(
            AssociePresence(
                associe_id=str(a["id"]),
                nom=a.get("nom", ""),
                nb_parts=nb_parts,
                pct=pct,
                present=None,
            )
        )

    return FeuillePresenceResponse(
        sci_nom=sci_nom,
        date_ag=str(ag.get("date_ag", "")),
        type_ag=ag.get("type_ag", "ordinaire"),
        associes=associes_presence,
        total_parts=total_parts,
        quorum_requis="Majorite des parts (>50%)",
        quorum_atteint=None,
    )


@router.post("/{ag_id}/feuille-presence", response_model=PresenceUpdateResponse)
@limiter.limit("30/minute")
async def update_feuille_presence(
    request: Request,
    sci_id: UUID,
    ag_id: UUID,
    payload: PresenceUpdatePayload,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Record attendance and compute quorum for a general assembly."""
    logger.info("update_feuille_presence", sci_id=str(sci_id), ag_id=str(ag_id))

    client = _get_client(request)

    # Verify AG exists and belongs to this SCI
    ag_result = (
        client.table("assemblees_generales")
        .select("id")
        .eq("id", str(ag_id))
        .eq("id_sci", str(sci_id))
        .execute()
    )
    if not (ag_result.data or []):
        raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

    # Fetch all associes for this SCI
    assoc_result = (
        client.table("associes")
        .select("id, part")
        .eq("id_sci", str(sci_id))
        .execute()
    )
    associes = assoc_result.data or []
    parts_by_id = {str(a["id"]): float(a.get("part") or 0) for a in associes}
    total_parts = sum(parts_by_id.values())

    # Calculate parts presentes
    present_ids = {p.associe_id for p in payload.presences if p.present}
    parts_presentes = sum(parts_by_id.get(aid, 0) for aid in present_ids)

    pourcentage = round(parts_presentes / total_parts * 100, 2) if total_parts > 0 else 0
    quorum_atteint = pourcentage > 50

    # Update the AG record with quorum result
    client.table("assemblees_generales").update({
        "quorum_atteint": quorum_atteint,
    }).eq("id", str(ag_id)).execute()

    logger.info(
        "feuille_presence_updated",
        ag_id=str(ag_id),
        quorum_atteint=quorum_atteint,
        pourcentage=pourcentage,
    )

    return PresenceUpdateResponse(
        quorum_atteint=quorum_atteint,
        parts_presentes=parts_presentes,
        total_parts=total_parts,
        pourcentage_present=pourcentage,
    )
