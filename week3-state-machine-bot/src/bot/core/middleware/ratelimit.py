"""Per-user token-bucket rate limiting (in-memory).

Simple and sufficient at Week 1 scale; the bucket map resets on restart,
which is acceptable — persistent limits can move to the DB later.
"""

from __future__ import annotations

import time

from ..contracts import HandlerContext
from ..errors import RateLimited


class RateLimiter:
    """Burst of `capacity` commands allowed, then one per `refill_seconds`."""

    def __init__(self, capacity: int = 5, refill_seconds: float = 10.0):
        self.capacity = capacity
        self.refill_seconds = refill_seconds
        self._buckets: dict[tuple[str, str], tuple[float, float]] = {}

    def _key(self, ctx: HandlerContext) -> tuple[str, str]:
        return (ctx.message.platform, ctx.message.platform_user_id)

    async def __call__(self, ctx: HandlerContext) -> None:
        key = self._key(ctx)
        now = time.monotonic()
        tokens, ts = self._buckets.get(key, (float(self.capacity), now))

        # refill: one token per refill_seconds, up to burst capacity
        elapsed = now - ts
        tokens = min(self.capacity, tokens + elapsed / self.refill_seconds)
        if tokens < 1.0:
            self._buckets[key] = (tokens, now)
            raise RateLimited()
        self._buckets[key] = (tokens - 1.0, now)
