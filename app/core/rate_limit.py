from __future__ import annotations

from dataclasses import dataclass
import time

from app.core.redis import redis_client


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


class RedisFixedWindowRateLimiter:
    def __init__(
        self,
        prefix: str = "medibook:ratelimit",
    ) -> None:
        self.prefix = prefix

    async def check(
        self,
        *,
        scope: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        limit = max(1, int(limit))
        window_seconds = max(1, int(window_seconds))

        now = int(time.time())
        bucket = now // window_seconds

        key = (
            f"{self.prefix}:"
            f"{scope}:"
            f"{identifier}:"
            f"{bucket}"
        )

        async with redis_client.pipeline(
            transaction=True
        ) as pipe:
            await pipe.incr(key)

            await pipe.expire(
                key,
                window_seconds + 5,
            )

            result = await pipe.execute()

        count = int(result[0])

        reset_seconds = (
            window_seconds
            -
            (now % window_seconds)
        )

        return RateLimitDecision(
            allowed=count <= limit,
            limit=limit,
            remaining=max(
                0,
                limit - count,
            ),
            reset_seconds=reset_seconds,
        )
