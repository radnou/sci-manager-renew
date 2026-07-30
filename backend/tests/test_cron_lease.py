"""Bail d'exclusion mutuelle du cron (audit C9).

Sans ce verrou, la boucle de notifications tournait dans chaque worker uvicorn :
les clients recevaient relances de loyer et emails de nurture en double. Preuve
relevée en production le 2026-07-30 — le même `signup_nurture_user_lookup_failed`
apparaît deux fois pour le même user_id, à 3 ms d'écart.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.cron_lease import TABLE, acquire_lease, holder_id, release_lease

NOM = "notification_cron"
DUREE = timedelta(hours=23)


@pytest.fixture(autouse=True)
def table_vide(fake_supabase):
    fake_supabase.store[TABLE] = []
    yield
    fake_supabase.store[TABLE] = []


def _bail(fake_supabase) -> dict | None:
    lignes = fake_supabase.store[TABLE]
    return lignes[0] if lignes else None


def test_premiere_execution_cree_le_bail(fake_supabase):
    """Aucune ligne en base : le premier worker doit pouvoir démarrer."""
    assert acquire_lease(fake_supabase, NOM, DUREE) is True

    ligne = _bail(fake_supabase)
    assert ligne is not None
    assert ligne["name"] == NOM
    assert ligne["holder"] == holder_id()
    assert datetime.fromisoformat(ligne["locked_until"]) > datetime.now(UTC)


def test_second_worker_refuse_pendant_la_duree_du_bail(fake_supabase):
    """Le cas qui produisait les emails en double."""
    assert acquire_lease(fake_supabase, NOM, DUREE) is True
    assert acquire_lease(fake_supabase, NOM, DUREE) is False
    assert acquire_lease(fake_supabase, NOM, DUREE) is False

    # Le détenteur d'origine n'a pas été écrasé
    assert len(fake_supabase.store[TABLE]) == 1


def test_bail_expire_le_cycle_suivant_repart(fake_supabase):
    """Le lendemain, le premier worker réveillé doit reprendre la main."""
    acquire_lease(fake_supabase, NOM, DUREE)

    passe = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    fake_supabase.store[TABLE][0]["locked_until"] = passe

    assert acquire_lease(fake_supabase, NOM, DUREE) is True
    assert datetime.fromisoformat(_bail(fake_supabase)["locked_until"]) > datetime.now(
        UTC
    )


def test_un_redeploiement_ne_rejoue_pas_le_cycle(fake_supabase):
    """`asyncio.sleep` repart de zéro à chaque démarrage de processus.

    Sans le bail, tout déploiement relançait un cycle complet immédiatement.
    """
    assert acquire_lease(fake_supabase, NOM, DUREE) is True
    # Redémarrage du processus : nouvelle boucle, bail toujours détenu
    assert acquire_lease(fake_supabase, NOM, DUREE) is False


def test_baux_independants_par_tache(fake_supabase):
    """Deux tâches distinctes ne doivent pas se bloquer l'une l'autre."""
    assert acquire_lease(fake_supabase, NOM, DUREE) is True
    assert acquire_lease(fake_supabase, "autre_tache", DUREE) is True
    assert len(fake_supabase.store[TABLE]) == 2


def test_release_libere_pour_le_detenteur(fake_supabase):
    acquire_lease(fake_supabase, NOM, DUREE)
    release_lease(fake_supabase, NOM)

    assert acquire_lease(fake_supabase, NOM, DUREE) is True


def test_erreur_de_base_ne_declenche_pas_le_cycle(monkeypatch, fake_supabase):
    """En cas de panne, sauter un cycle vaut mieux que le jouer en double."""

    def boom(*_a, **_kw):
        raise RuntimeError("base injoignable")

    monkeypatch.setattr(fake_supabase, "table", boom)

    assert acquire_lease(fake_supabase, NOM, DUREE) is False
