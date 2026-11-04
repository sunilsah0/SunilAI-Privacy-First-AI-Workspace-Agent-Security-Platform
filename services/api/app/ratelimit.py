"""Simple in-memory rate limiting.

Good for ONE API process (which is how the release runs). With several workers each one
would count separately. Counters are lost when the API restarts.
"""
import os
import time
from collections import deque

from fastapi import HTTPException, Request

ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
TRUST_PROXY = os.getenv("TRUST_PROXY", "0") == "1"


def client_ip(request: Request) -> str:
    """Behind our own proxy the real address is the LAST entry the proxy added.
    Without TRUST_PROXY a caller could fake the header, so we ignore it."""
    if TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def too_many(retry_seconds: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="Too many requests. Please wait a little and try again.",
        headers={"Retry-After": str(max(int(retry_seconds), 1))},
    )


class Limiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    def reset_all(self) -> None:
        self._hits.clear()

    def _recent(self, key: str, window: float) -> tuple[deque[float], float]:
        now = time.monotonic()
        queue = self._hits.setdefault(key, deque())
        while queue and now - queue[0] > window:
            queue.popleft()
        if len(self._hits) > 20000:
            self._prune(now)
        return queue, now

    def _prune(self, now: float) -> None:
        stale = [k for k, q in self._hits.items() if not q or now - q[-1] > 3600]
        for k in stale:
            del self._hits[k]

    def check(self, key: str, limit: int, window: float) -> None:
        """Count one request. Refuse with 429 once the limit is reached."""
        if not ENABLED:
            return
        queue, now = self._recent(key, window)
        if len(queue) >= limit:
            raise too_many(window - (now - queue[0]) + 1)
        queue.append(now)

    def is_blocked(self, key: str, limit: int, window: float) -> int:
        """Seconds to wait if the key is over the limit, otherwise 0. Does not count."""
        if not ENABLED:
            return 0
        queue, now = self._recent(key, window)
        return int(window - (now - queue[0]) + 1) if len(queue) >= limit else 0

    def record(self, key: str, window: float) -> None:
        if not ENABLED:
            return
        queue, now = self._recent(key, window)
        queue.append(now)

    def clear(self, key: str) -> None:
        self._hits.pop(key, None)


limiter = Limiter()
