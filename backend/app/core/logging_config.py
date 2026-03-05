# backend/app/core/logging_config.py
import logging
import sys
import structlog
from typing import Literal

def configure_logging(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    log_format: Literal["json", "console"] = "json"
) -> None:
    """
    Configure structured logging avec structlog.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        log_format: Format de sortie (json pour prod, console pour dev)
    """
    # Configuration du niveau de log Python standard
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level)
    )

    # Processeurs communs
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Renderer selon le format
    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configuration structlog
    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Logger initial pour confirmer configuration
    logger = structlog.get_logger(__name__)
    logger.info("logging_configured", log_level=log_level, log_format=log_format)
