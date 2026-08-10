"""État de cycle de vie du processus.

Isolé dans son propre module pour que `main.py` et les routeurs puissent le
partager sans import circulaire : `main.py` importe le routeur de
`api/v1/health.py`, qui a besoin de connaître l'état d'arrêt.

Sans ce partage, les sondes de santé ne pouvaient pas refléter l'arrêt en
cours, et un backend bloqué en shutdown répondait 200 sur /health/live
pendant qu'il rejetait 100 % du trafic en 503. Le healthcheck Docker le
croyait sain et ne le redémarrait jamais.
"""

from __future__ import annotations

import asyncio

# Armé par les handlers SIGTERM/SIGINT et par la fin du lifespan.
# Remis à zéro au démarrage.
shutdown_event = asyncio.Event()


def is_shutting_down() -> bool:
    """Le processus a-t-il commencé son arrêt ?"""
    return shutdown_event.is_set()
