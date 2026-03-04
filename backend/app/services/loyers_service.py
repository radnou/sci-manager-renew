"""Backward-compatible placeholder for Phase 2 migration."""


def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
