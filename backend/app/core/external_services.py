from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable, TypeVar

import structlog

from app.core.config import settings

T = TypeVar("T")

logger = structlog.get_logger(__name__)


def is_retryable_exception(exc: Exception) -> bool:
    retryable_tokens = (
        "timeout",
        "tempor",
        "connection reset",
        "connection refused",
        "service unavailable",
        "too many requests",
        "rate limit",
    )
    message = str(exc).lower()
    return any(token in message for token in retryable_tokens)


async def run_with_retry(
    *,
    operation: str,
    func: Callable[[], T] | Callable[[], Awaitable[T]],
    allow_retry: bool = True,
    context: dict[str, Any] | None = None,
) -> T:
    attempts = max(settings.external_retry_attempts, 1)
    base_delay_ms = max(settings.external_retry_base_delay_ms, 1)
    payload = context or {}

    for attempt in range(1, attempts + 1):
        try:
            result = func()
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as exc:
            retryable = allow_retry and is_retryable_exception(exc) and attempt < attempts
            logger.warning(
                "external_call_failed",
                operation=operation,
                attempt=attempt,
                retryable=retryable,
                error=str(exc),
                **payload,
            )
            if not retryable:
                raise

            delay_ms = int(base_delay_ms * (2 ** (attempt - 1)) + random.randint(0, base_delay_ms))
            await asyncio.sleep(delay_ms / 1000)


def coerce_timeout(timeout_value: float | None, default: float) -> float:
    if timeout_value is None:
        return default
    return max(float(timeout_value), 0.1)
