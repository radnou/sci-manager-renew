"""Bail d'exclusion mutuelle pour les tâches de fond (audit C9).

Le cron de notifications démarre dans le `lifespan` de FastAPI, donc une fois
par worker uvicorn. Sans verrou, chaque cycle s'exécutait autant de fois qu'il y
a de workers et les clients recevaient les relances en double.

Le verrou tient dans un unique UPDATE conditionnel :

    update cron_leases set locked_until = ... where name = ? and locked_until < now()

PostgreSQL sérialise les écritures concurrentes sur une même ligne : le second
worker réévalue `locked_until` après le commit du premier, ne voit plus la
condition satisfaite, et repart avec zéro ligne modifiée. Pas de fenêtre de
course, et pas besoin de `pg_advisory_lock` — inaccessible via PostgREST, qui
n'entretient pas de session.

`locked_until` sert aussi d'expiration : un worker tué en cours de cycle ne
bloque pas la tâche au-delà de la durée du bail.
"""

from __future__ import annotations

import os
import socket
from datetime import UTC, datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)

TABLE = "cron_leases"


def holder_id() -> str:
    """Identifiant du détenteur — diagnostic uniquement, jamais utilisé comme verrou."""
    return f"{socket.gethostname()}:{os.getpid()}"


def acquire_lease(client, name: str, duree: timedelta) -> bool:
    """Tenter de prendre le bail `name` pour `duree`. Retourne True si obtenu.

    En cas d'erreur (table absente, base injoignable), retourne False : mieux
    vaut sauter un cycle que risquer de le jouer en double. Le cycle suivant
    retentera.
    """
    maintenant = datetime.now(UTC)
    valeurs = {
        "locked_until": (maintenant + duree).isoformat(),
        "holder": holder_id(),
        "updated_at": maintenant.isoformat(),
    }

    try:
        # Chemin nominal : le bail existe et est expiré. UPDATE conditionnel,
        # donc atomique — un seul worker peut voir la condition satisfaite.
        resultat = (
            client.table(TABLE)
            .update(valeurs)
            .eq("name", name)
            .lt("locked_until", maintenant.isoformat())
            .execute()
        )
        if resultat.data:
            logger.info("cron_lease_acquired", lease=name, holder=valeurs["holder"])
            return True

        # Zéro ligne modifiée : soit le bail est détenu, soit il n'a jamais été
        # créé. On distingue les deux, sinon la toute première exécution ne
        # partirait jamais.
        existant = client.table(TABLE).select("name").eq("name", name).execute()
        if existant.data:
            logger.info("cron_lease_held_by_other", lease=name)
            return False

        # Première exécution. Deux workers peuvent tenter l'insertion en même
        # temps : la clé primaire en élimine un, qui repart bredouille.
        client.table(TABLE).insert({"name": name, **valeurs}).execute()
        logger.info("cron_lease_created", lease=name, holder=valeurs["holder"])
        return True

    except Exception as exc:
        logger.warning("cron_lease_acquire_failed", lease=name, error=str(exc))
        return False


def release_lease(client, name: str) -> None:
    """Libérer le bail à la fin d'un cycle réussi.

    Optionnel : `locked_until` expire de lui-même. Utile surtout aux tests et
    aux tâches que l'on veut pouvoir relancer aussitôt.
    """
    try:
        client.table(TABLE).update(
            {
                "locked_until": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        ).eq("name", name).eq("holder", holder_id()).execute()
    except Exception as exc:
        logger.warning("cron_lease_release_failed", lease=name, error=str(exc))
