"""ChainClient's cache and breaker must survive concurrent callers."""
import sys
import threading
from datetime import UTC, datetime

from wasel.llm.base import CallMeta, ProviderDown, TaskSpec
from wasel.llm.client import ChainClient, ChainStep


class _Backend:
    def __init__(self, fail=False):
        self.fail = fail

    def complete_json(self, task, model, user, timeout_s):
        if self.fail:
            raise ProviderDown("down")
        return "{}", CallMeta(provider="groq", model=model, latency_ms=1)


def _task():
    return TaskSpec("judge", "s", {}, "sys", (), "v1", 10, 0.0, None, True)


def _hammer(client, threads=16, calls=200):
    errors = []
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)       # force thread switches inside the cache code

    def work(n):
        try:
            for i in range(calls):
                client.extract(_task(), f"k{(n + i) % 5}", parse=lambda raw: raw, meter=None, sandbox_id=None,
                               now=datetime(2026, 1, 1, tzinfo=UTC), role="judge")
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    ts = [threading.Thread(target=work, args=(n,)) for n in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    sys.setswitchinterval(old)
    return errors


def test_concurrent_extract_with_tiny_cache_does_not_raise():
    client = ChainClient([ChainStep("primary", "groq", "m", _Backend(), 6)], cache_size=2)
    assert _hammer(client) == []
    assert len(client._cache) <= 2


def test_concurrent_extract_with_open_breaker_does_not_raise():
    client = ChainClient([ChainStep("primary", "groq", "m", _Backend(fail=True), 6)], cache_size=2)
    assert _hammer(client, calls=100) == []
