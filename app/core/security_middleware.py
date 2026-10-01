from __future__ import annotations

import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.observability import log_event
from app.core.rate_limit import RedisFixedWindowRateLimiter


logger = logging.getLogger(
    "medibook.security"
)

rate_limiter = RedisFixedWindowRateLimiter()


def _env_int(
    name: str,
    default: int,
) -> int:
    try:
        return max(
            1,
            int(
                os.getenv(
                    name,
                    str(default),
                )
            ),
        )
    except Exception:
        return default


def rate_limit_enabled() -> bool:
    return (
        os.getenv(
            "MEDIBOOK_RATE_LIMIT_ENABLED",
            "true",
        )
        .strip()
        .lower()
        not in {
            "false",
            "0",
            "no",
            "off",
        }
    )


def rate_limit_policy(
    path: str,
) -> tuple[str, int, int] | None:
    path = path.strip().lower()

    if path.startswith(
        "/api/v1/auth/"
    ):
        return (
            "auth",
            _env_int(
                "MEDIBOOK_RATE_LIMIT_AUTH_PER_MINUTE",
                30,
            ),
            60,
        )

    if path.startswith(
        "/api/v1/chat"
    ):
        return (
            "chat",
            _env_int(
                "MEDIBOOK_RATE_LIMIT_CHAT_PER_MINUTE",
                30,
            ),
            60,
        )

    if (
        path.startswith(
            "/api/v1/widget"
        )
        or path.startswith(
            "/api/v1/widget-conversations"
        )
    ):
        return (
            "widget",
            _env_int(
                "MEDIBOOK_RATE_LIMIT_WIDGET_PER_MINUTE",
                120,
            ),
            60,
        )

    if path.startswith(
        "/api/v1/hospital-public"
    ):
        return (
            "hospital-public",
            _env_int(
                "MEDIBOOK_RATE_LIMIT_PUBLIC_PER_MINUTE",
                240,
            ),
            60,
        )

    return None


def apply_security_headers(
    response,
):
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "X-Permitted-Cross-Domain-Policies"
    ] = "none"

    response.headers[
        "Permissions-Policy"
    ] = (
        "geolocation=(), "
        "camera=(), "
        "microphone=()"
    )

    return response


class SecurityHardeningMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        policy = rate_limit_policy(
            request.url.path
        )

        if (
            policy is not None
            and rate_limit_enabled()
        ):
            scope, limit, window = policy

            identifier = (
                request.client.host
                if request.client
                else "unknown"
            )

            try:
                decision = await rate_limiter.check(
                    scope=scope,
                    identifier=identifier,
                    limit=limit,
                    window_seconds=window,
                )

                if not decision.allowed:
                    log_event(
                        logger,
                        logging.WARNING,
                        "security.rate_limit.exceeded",
                        scope=scope,
                        path=request.url.path,
                    )

                    response = JSONResponse(
                        status_code=429,
                        content={
                            "detail":
                                "Too many requests.",
                        },
                    )

                    response.headers[
                        "Retry-After"
                    ] = str(
                        decision.reset_seconds
                    )

                    response.headers[
                        "X-RateLimit-Limit"
                    ] = str(
                        decision.limit
                    )

                    response.headers[
                        "X-RateLimit-Remaining"
                    ] = "0"

                    return apply_security_headers(
                        response
                    )

            except Exception as exc:
                # Redis degradation must not make the
                # appointment API unavailable.

                log_event(
                    logger,
                    logging.ERROR,
                    "security.rate_limit.backend_unavailable",
                    error_type=
                        exc.__class__.__name__,
                )

        response = await call_next(
            request
        )

        return apply_security_headers(
            response
        )
