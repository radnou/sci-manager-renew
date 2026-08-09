"""Sémantique des sondes de santé.

Deux défauts constatés en production le 2026-08-10, opposés l'un à l'autre :

1. En maintenance, `/health/live` renvoyait 503 sur une application saine.
   `maintenance_middleware` n'exemptait que `/api/v1/health` et
   `/api/v1/health/ready`, chemins qui n'existent pas : le routeur health est
   monté sans préfixe. Le healthcheck de `docker-compose.yml` sonde
   `/health/live` : le conteneur passait donc unhealthy à chaque maintenance.

2. Pendant un arrêt, `/health/live` ET `/health/ready` renvoyaient 200 alors
   que `logging_middleware` rejetait 100 % du reste du trafic en 503. Un
   backend bloqué en shutdown se déclarait sain et n'était jamais redémarré.

Ces tests figent le comportement attendu :

                 | liveness | readiness
  nominal        |   200    |   200
  maintenance    |   200    |   503
  arrêt en cours |   503    |   503
"""

from __future__ import annotations

import pytest

from app.core import lifecycle


@pytest.fixture(autouse=True)
def _reset_lifecycle():
    """Isole l'état d'arrêt : aucun test ne doit le fuiter sur le suivant."""

    """
    lifecycle.shutdown_event.clear()
    yield
    lifecycle.shutdown_event.clear()

# ── Nominal ────────────────────────────────────────────────────────


def test_liveness_ok_en_fonctionnement_normal(client):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_health_ok_en_fonctionnement_normal(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Arrêt en cours ─────────────────────────────────────────────────


def test_liveness_signale_503_pendant_arret(client):
    """Sans ça, Docker croit le conteneur sain et ne le redémarre jamais."""
    lifecycle.shutdown_event.set()
    r = client.get("/health/live")
    assert r.status_code == 503
    assert r.json()["status"] == "shutting_down"
    assert r.json()["alive"] is False


def test_health_signale_503_pendant_arret(client):
    lifecycle.shutdown_event.set()
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["status"] == "shutting_down"


def test_readiness_signale_503_pendant_arret_sans_sonder_les_dependances(client):
    """La réponse doit précéder les sondes réseau : elles coûtent ~500 ms."""
    lifecycle.shutdown_event.set()
    r = client.get("/health/ready")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "shutting_down"
    assert body["ready_for_traffic"] is False
    # Court-circuit : aucune dépendance n'a été interrogée.
    assert "checks" not in body


# ── Mode maintenance ───────────────────────────────────────────────


def test_liveness_reste_200_en_maintenance(client, monkeypatch):
    """Le processus est sain : le healthcheck Docker ne doit pas le tuer."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "maintenance_mode", True, raising=False)
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_readiness_signale_503_en_maintenance(client, monkeypatch):
    """L'application ne sert pas de trafic : elle n'est pas prête."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "maintenance_mode", True, raising=False)
    r = client.get("/health/ready")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "maintenance"
    assert body["ready_for_traffic"] is False


def test_maintenance_nexempte_pas_les_routes_applicatives(client, monkeypatch):
    """Le reste de l'API doit bien être bloqué : la garde n'est pas trop large."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "maintenance_mode", True, raising=False)
    r = client.get("/api/v1/scis")
    assert r.status_code == 503


@pytest.mark.parametrize(
    "path", ["/health", "/health/live", "/health/ready", "/health/flags"]
)
def test_toutes_les_routes_health_traversent_la_maintenance(client, monkeypatch, path):
    """Aucune ne doit être bloquée PAR LE MIDDLEWARE.

    Un 503 émis par l'endpoint lui-même (readiness) est légitime ; un 503 du
    middleware de maintenance ne l'est pas — c'est le défaut d'origine, qui
    visait des chemins `/api/v1/health*` inexistants.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "maintenance_mode", True, raising=False)
    r = client.get(path)
    body = r.json()
    assert body.get("code") != "maintenance_mode", (
        f"{path} a été bloqué par maintenance_middleware au lieu d'être exempté"
    )
