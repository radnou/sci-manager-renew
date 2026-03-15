"""CSV import for biens and loyers."""

from __future__ import annotations

import csv
import io
import re
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response

from app.core.exceptions import ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role
from app.core.supabase_client import get_supabase_service_client

router = APIRouter(prefix="/scis/{sci_id}/import", tags=["import"])
logger = structlog.get_logger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_ROWS = 500

BIENS_REQUIRED_COLUMNS = {"adresse", "ville", "code_postal", "type_locatif", "surface_m2", "nb_pieces", "loyer_cc", "charges"}
LOYERS_REQUIRED_COLUMNS = {"adresse_bien", "date_loyer", "montant", "statut"}

BIENS_TEMPLATE = """adresse,ville,code_postal,type_locatif,surface_m2,nb_pieces,loyer_cc,charges,dpe_classe
12 rue de la Paix,Paris,75001,nu,65,3,1250,180,C
8 rue des Lilas,Lyon,69001,meuble,28,1,750,90,D
"""

LOYERS_TEMPLATE = """adresse_bien,date_loyer,montant,statut
12 rue de la Paix,2026-01-01,1250,paye
12 rue de la Paix,2026-02-01,1250,en_attente
"""

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _get_write_client():
    """Service client for INSERT operations -- RLS blocks inserts before membership exists."""
    return get_supabase_service_client()


def _sanitize(value: str) -> str:
    """Strip whitespace and remove HTML tags from a value."""
    value = value.strip()
    value = _HTML_TAG_RE.sub("", value)
    return value


def _validate_biens_row(row: dict[str, str], index: int) -> dict | str:
    """Validate and convert a biens CSV row. Returns dict on success, error string on failure."""
    adresse = _sanitize(row.get("adresse", ""))
    ville = _sanitize(row.get("ville", ""))
    code_postal = _sanitize(row.get("code_postal", ""))
    type_locatif = _sanitize(row.get("type_locatif", ""))

    if not adresse or not ville or not code_postal:
        return f"Ligne {index}: adresse, ville et code_postal sont obligatoires."

    try:
        surface = float(_sanitize(row.get("surface_m2", "0")))
        nb_pieces = int(_sanitize(row.get("nb_pieces", "0")))
        loyer_cc = float(_sanitize(row.get("loyer_cc", "0")))
        charges = float(_sanitize(row.get("charges", "0")))
    except (ValueError, TypeError):
        return f"Ligne {index}: valeur numérique invalide."

    result = {
        "adresse": adresse,
        "ville": ville,
        "code_postal": code_postal,
        "type_bien": type_locatif or "appartement",
        "surface_m2": surface,
        "nb_pieces": nb_pieces,
        "loyer_cc": loyer_cc,
        "charges_provisions": charges,
        "statut": "libre",
    }

    dpe = _sanitize(row.get("dpe_classe", ""))
    if dpe:
        result["dpe_classe"] = dpe.upper()

    return result


def _validate_loyers_row(row: dict[str, str], index: int) -> dict | str:
    """Validate and convert a loyers CSV row. Returns dict on success, error string on failure."""
    adresse_bien = _sanitize(row.get("adresse_bien", ""))
    date_loyer = _sanitize(row.get("date_loyer", ""))
    statut = _sanitize(row.get("statut", ""))

    if not adresse_bien or not date_loyer:
        return f"Ligne {index}: adresse_bien et date_loyer sont obligatoires."

    if statut not in ("paye", "en_attente", "retard", "partiel", ""):
        return f"Ligne {index}: statut invalide '{statut}'."

    try:
        montant = float(_sanitize(row.get("montant", "0")))
    except (ValueError, TypeError):
        return f"Ligne {index}: montant invalide."

    return {
        "adresse_bien": adresse_bien,
        "date_loyer": date_loyer,
        "montant": montant,
        "statut": statut or "en_attente",
    }


# ──────────────────────────────────────────────────────────────
# GET /templates/{type} — download CSV template
# ──────────────────────────────────────────────────────────────

@router.get("/templates/{template_type}")
async def get_csv_template(template_type: str):
    """Download a CSV template for biens or loyers import."""
    if template_type == "biens":
        content = BIENS_TEMPLATE.lstrip("\n")
        filename = "template-biens.csv"
    elif template_type == "loyers":
        content = LOYERS_TEMPLATE.lstrip("\n")
        filename = "template-loyers.csv"
    else:
        raise ValidationError(f"Type de template invalide: '{template_type}'. Utilisez 'biens' ou 'loyers'.")

    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ──────────────────────────────────────────────────────────────
# POST /csv — import CSV data
# ──────────────────────────────────────────────────────────────

@router.post("/csv", status_code=status.HTTP_200_OK)
async def import_csv(
    sci_id: UUID,
    type: str = Form(...),
    file: UploadFile = File(...),
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Import biens or loyers from a CSV file into the given SCI."""
    if type not in ("biens", "loyers"):
        raise ValidationError(f"Type d'import invalide: '{type}'. Utilisez 'biens' ou 'loyers'.")

    # Read file content
    file_content = await file.read()

    # Validate file size
    if len(file_content) > MAX_FILE_SIZE:
        raise ValidationError(f"Fichier trop volumineux (max {MAX_FILE_SIZE // (1024 * 1024)} Mo).")

    if len(file_content) == 0:
        raise ValidationError("Fichier vide.")

    # Decode UTF-8
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError("Encodage invalide. Le fichier doit être en UTF-8.")

    # Parse CSV
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValidationError("Fichier CSV invalide: aucune colonne détectée.")

    columns = {c.strip().lower() for c in reader.fieldnames}

    # Validate columns
    if type == "biens":
        missing = BIENS_REQUIRED_COLUMNS - columns
        if missing:
            raise ValidationError(f"Colonnes manquantes: {', '.join(sorted(missing))}")
    else:
        missing = LOYERS_REQUIRED_COLUMNS - columns
        if missing:
            raise ValidationError(f"Colonnes manquantes: {', '.join(sorted(missing))}")

    # Read all rows
    rows = list(reader)
    if len(rows) > MAX_ROWS:
        raise ValidationError(f"Trop de lignes ({len(rows)}). Maximum autorisé: {MAX_ROWS}.")

    write_client = _get_write_client()
    imported = 0
    skipped = 0
    errors: list[str] = []

    if type == "biens":
        # Load existing biens for duplicate detection
        existing_result = write_client.table("biens").select("adresse,ville").eq("id_sci", str(sci_id)).execute()
        existing_keys = {
            (row["adresse"].lower(), row["ville"].lower())
            for row in (existing_result.data or [])
            if row.get("adresse") and row.get("ville")
        }

        for i, row in enumerate(rows, start=2):
            validated = _validate_biens_row(row, i)
            if isinstance(validated, str):
                errors.append(validated)
                continue

            key = (validated["adresse"].lower(), validated["ville"].lower())
            if key in existing_keys:
                skipped += 1
                continue

            validated["id_sci"] = str(sci_id)
            write_client.table("biens").insert(validated).execute()
            existing_keys.add(key)
            imported += 1

    else:
        # Loyers import: match adresse_bien to existing biens
        biens_result = write_client.table("biens").select("id,adresse").eq("id_sci", str(sci_id)).execute()
        adresse_to_bien: dict[str, str] = {}
        for bien in (biens_result.data or []):
            if bien.get("adresse"):
                adresse_to_bien[bien["adresse"].lower()] = bien["id"]

        for i, row in enumerate(rows, start=2):
            validated = _validate_loyers_row(row, i)
            if isinstance(validated, str):
                errors.append(validated)
                continue

            adresse_key = validated.pop("adresse_bien").lower()
            bien_id = adresse_to_bien.get(adresse_key)
            if not bien_id:
                errors.append(f"Ligne {i}: bien introuvable pour l'adresse '{row.get('adresse_bien', '')}'.")
                continue

            validated["id_bien"] = bien_id
            write_client.table("loyers").insert(validated).execute()
            imported += 1

    logger.info(
        "csv_import_completed",
        sci_id=str(sci_id),
        type=type,
        imported=imported,
        skipped=skipped,
        errors=len(errors),
    )

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "type": type,
    }
