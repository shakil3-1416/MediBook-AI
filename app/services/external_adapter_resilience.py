from __future__ import annotations

import asyncio
from dataclasses import dataclass
import inspect
import os
import threading
import time


class ExternalAdapterTimeout(
    TimeoutError
):
    pass


class ExternalAdapterCircuitOpen(
    RuntimeError
):
    pass


@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class AdapterCircuitBreaker:
    def __init__(
        self,
    ) -> None:
        self._states: dict[
            str,
            CircuitState,
        ] = {}

        self._lock = threading.Lock()

    def before_call(
        self,
        *,
        key: str,
        cooldown_seconds: float,
    ) -> None:
        now = time.monotonic()

        with self._lock:
            state = self._states.setdefault(
                key,
                CircuitState(),
            )

            if state.opened_at is None:
                return

            if (
                now
                -
                state.opened_at
            ) >= cooldown_seconds:
                state.failures = 0
                state.opened_at = None
                return

            raise ExternalAdapterCircuitOpen(
                "External integration circuit is open."
            )

    def succeeded(
        self,
        *,
        key: str,
    ) -> None:
        with self._lock:
            self._states[
                key
            ] = CircuitState()

    def failed(
        self,
        *,
        key: str,
        threshold: int,
    ) -> None:
        with self._lock:
            state = self._states.setdefault(
                key,
                CircuitState(),
            )

            state.failures += 1

            if state.failures >= threshold:
                state.opened_at = (
                    time.monotonic()
                )


breaker = AdapterCircuitBreaker()


def _float_env(
    name: str,
    default: float,
) -> float:
    try:
        return max(
            0.1,
            float(
                os.getenv(
                    name,
                    str(default),
                )
            ),
        )
    except Exception:
        return default


def _int_env(
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


async def resilient_adapter_call(
    *,
    provider: str,
    operation: str,
    function,
    args: tuple = (),
    kwargs: dict | None = None,
    timeout_seconds: float | None = None,
):
    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else _float_env(
            "MEDIBOOK_ADAPTER_TIMEOUT_SECONDS",
            15.0,
        )
    )

    threshold = _int_env(
        "MEDIBOOK_ADAPTER_CIRCUIT_FAILURES",
        5,
    )

    cooldown = _float_env(
        "MEDIBOOK_ADAPTER_CIRCUIT_COOLDOWN_SECONDS",
        30.0,
    )

    key = (
        f"{provider}:"
        f"{operation}"
    )

    breaker.before_call(
        key=key,
        cooldown_seconds=cooldown,
    )

    try:
        if inspect.iscoroutinefunction(
            function
        ):
            result = await asyncio.wait_for(
                function(
                    *args,
                    **(kwargs or {}),
                ),
                timeout=timeout,
            )
        else:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    function,
                    *args,
                    **(kwargs or {}),
                ),
                timeout=timeout,
            )

            if inspect.isawaitable(
                result
            ):
                result = await asyncio.wait_for(
                    result,
                    timeout=timeout,
                )

        breaker.succeeded(
            key=key
        )

        return result

    except asyncio.TimeoutError as exc:
        breaker.failed(
            key=key,
            threshold=threshold,
        )

        raise ExternalAdapterTimeout(
            "External integration call timed out."
        ) from exc

    except ExternalAdapterCircuitOpen:
        raise

    except Exception:
        breaker.failed(
            key=key,
            threshold=threshold,
        )

        raise
