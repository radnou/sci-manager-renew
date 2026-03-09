import pytest

from app.core.external_services import is_retryable_exception, run_with_retry


def test_is_retryable_exception_matches_transient_errors():
    assert is_retryable_exception(RuntimeError("connection refused"))
    assert is_retryable_exception(RuntimeError("service unavailable"))
    assert not is_retryable_exception(RuntimeError("invalid payload"))


@pytest.mark.asyncio
async def test_run_with_retry_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}

    async def fake_sleep(_delay: float):
        return None

    monkeypatch.setattr("app.core.external_services.asyncio.sleep", fake_sleep)

    async def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("connection refused")
        return "ok"

    result = await run_with_retry(operation="test.retry", func=flaky)
    assert result == "ok"
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_run_with_retry_does_not_retry_non_retryable(monkeypatch):
    calls = {"count": 0}

    async def fake_sleep(_delay: float):
        return None

    monkeypatch.setattr("app.core.external_services.asyncio.sleep", fake_sleep)

    def failing():
        calls["count"] += 1
        raise RuntimeError("invalid payload")

    with pytest.raises(RuntimeError, match="invalid payload"):
        await run_with_retry(operation="test.no_retry", func=failing)

    assert calls["count"] == 1
