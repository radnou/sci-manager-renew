from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Référentiel de rôles, aligné sur ASSOCIE_ROLE_OPTIONS
# (frontend/src/lib/high-value/associes.ts) et sur la contrainte
# `associes_role_check` (migration 043).
# `gerant` et `co_gerant` sont les rôles de gouvernance : eux seuls peuvent
# gérer les associés (cf. _require_gerant dans api/v1/associes.py).
AssocieRole = Literal["gerant", "co_gerant", "associe", "usufruitier"]

GOVERNANCE_ROLES: frozenset[str] = frozenset({"gerant", "co_gerant"})


class AssocieBase(BaseModel):
    id_sci: str
    nom: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    nb_parts: int | None = Field(default=None, ge=0)
    part: float | None = Field(default=None, gt=0)
    role: str = Field(default="associe", min_length=2, max_length=40)
    user_id: str | None = None


class AssocieCreate(AssocieBase):
    pass


class AssocieUpdate(BaseModel):
    """Champs modifiables d'un associé.

    Sécurité (audit C3) : `user_id` est volontairement absent — le rattachement
    d'un compte à un associé passe uniquement par l'invitation email
    (`associe_linking`), jamais par un payload client. `role` reste modifiable
    mais l'endpoint exige désormais le rôle gérant (`_require_gerant`).
    """

    nom: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    nb_parts: int | None = Field(default=None, ge=0)
    part: float | None = None
    role: AssocieRole | None = None


class AssocieResponse(AssocieBase):
    id: str
    is_account_member: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    warning: str | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
