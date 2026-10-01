from __future__ import annotations

from collections import defaultdict, deque
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
import json
import logging
import threading
import time
import uuid
from typing import Any


request_id_var: ContextVar[
    str | None
] = ContextVar(
    "medibook_request_id",
    default=None,
)


trace_id_var: ContextVar[
    str | None
] = ContextVar(
    "medibook_trace_id",
    default=None,
)


SENSITIVE_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "credential",
    "private_key",
    "access_key",
)


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    )


def new_request_id() -> str:
    return str(
        uuid.uuid4()
    )


def new_trace_id() -> str:
    return uuid.uuid4().hex


def current_request_id() -> str | None:
    return request_id_var.get()


def current_trace_id() -> str | None:
    return trace_id_var.get()


def is_sensitive_key(
    key: str,
) -> bool:
    lowered = key.lower()

    return any(
        fragment in lowered
        for fragment
        in SENSITIVE_FRAGMENTS
    )


def sanitize_log_value(
    value: Any,
    *,
    depth: int = 0,
) -> Any:
    if depth > 4:
        return "[truncated]"

    if isinstance(
        value,
        dict,
    ):
        result = {}

        for key, item in value.items():
            string_key = str(
                key
            )

            if is_sensitive_key(
                string_key
            ):
                result[
                    string_key
                ] = "[redacted]"

            else:
                result[
                    string_key
                ] = sanitize_log_value(
                    item,
                    depth=
                        depth + 1,
                )

        return result


    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            sanitize_log_value(
                item,
                depth=
                    depth + 1,
            )
            for item
            in list(
                value
            )[:50]
        ]


    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:
        return value


    return str(
        value
    )


class JsonFormatter(
    logging.Formatter
):
    def format(
        self,
        record:
            logging.LogRecord,
    ) -> str:
        payload = {
            "timestamp":
                utcnow()
                .isoformat(),

            "level":
                record.levelname,

            "logger":
                record.name,

            "message":
                record.getMessage(),

            "request_id":
                current_request_id(),

            "trace_id":
                current_trace_id(),
        }


        extras = getattr(
            record,
            "medibook_fields",
            None,
        )


        if isinstance(
            extras,
            dict,
        ):
            payload.update(
                sanitize_log_value(
                    extras
                )
            )


        if record.exc_info:
            payload[
                "exception_type"
            ] = (
                record.exc_info[
                    0
                ].__name__
                if record.exc_info[
                    0
                ]
                else None
            )


        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
            separators=(
                ",",
                ":",
            ),
        )


def configure_observability_logging(
    *,
    level: int = logging.INFO,
) -> None:
    root = logging.getLogger()

    marker = (
        "_medibook_observability_handler"
    )


    for handler in root.handlers:
        if getattr(
            handler,
            marker,
            False,
        ):
            root.setLevel(
                level
            )
            return


    handler = logging.StreamHandler()

    setattr(
        handler,
        marker,
        True,
    )

    handler.setFormatter(
        JsonFormatter()
    )


    root.addHandler(
        handler
    )

    root.setLevel(
        level
    )


def log_event(
    logger:
        logging.Logger,
    level: int,
    message: str,
    **fields: Any,
) -> None:
    logger.log(
        level,
        message,
        extra={
            "medibook_fields":
                sanitize_log_value(
                    fields
                ),
        },
    )


@dataclass(
    slots=True
)
class RequestMetric:
    timestamp: float

    method: str

    route: str

    status_code: int

    duration_ms: float


class RequestMetricsRegistry:
    """
    Process-local rolling request metrics.

    These are deliberately bounded and contain no request
    or response bodies.
    """

    def __init__(
        self,
        *,
        max_samples: int = 5000,
    ) -> None:
        self._samples: deque[
            RequestMetric
        ] = deque(
            maxlen=
                max_samples
        )

        self._lock = (
            threading.Lock()
        )


    def observe(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        with self._lock:
            self._samples.append(
                RequestMetric(
                    timestamp=
                        time.time(),

                    method=
                        method,

                    route=
                        route,

                    status_code=
                        status_code,

                    duration_ms=
                        duration_ms,
                )
            )


    def snapshot(
        self,
        *,
        window_seconds: int = 300,
    ) -> dict[
        str,
        Any,
    ]:
        cutoff = (
            time.time()
            -
            max(
                1,
                int(
                    window_seconds
                ),
            )
        )


        with self._lock:
            samples = [
                item
                for item
                in self._samples
                if item.timestamp
                >= cutoff
            ]


        total = len(
            samples
        )


        errors = sum(
            1
            for item
            in samples
            if item.status_code
            >= 500
        )


        client_errors = sum(
            1
            for item
            in samples
            if 400
            <= item.status_code
            < 500
        )


        durations = sorted(
            item.duration_ms
            for item
            in samples
        )


        def percentile(
            fraction: float,
        ) -> float:
            if not durations:
                return 0.0

            index = min(
                len(
                    durations
                )
                - 1,
                max(
                    0,
                    int(
                        round(
                            (
                                len(
                                    durations
                                )
                                - 1
                            )
                            * fraction
                        )
                    ),
                ),
            )

            return round(
                durations[
                    index
                ],
                2,
            )


        route_counts = defaultdict(
            int
        )


        for item in samples:
            route_counts[
                f"{item.method} {item.route}"
            ] += 1


        busiest = sorted(
            route_counts.items(),
            key=lambda pair:
                (
                    -pair[
                        1
                    ],
                    pair[
                        0
                    ],
                ),
        )[:20]


        return {
            "scope":
                "process_local",

            "window_seconds":
                int(
                    window_seconds
                ),

            "requests":
                total,

            "server_errors":
                errors,

            "client_errors":
                client_errors,

            "server_error_rate":
                (
                    round(
                        errors
                        /
                        total,
                        4,
                    )
                    if total
                    else 0.0
                ),

            "latency_ms": {
                "p50":
                    percentile(
                        0.50
                    ),

                "p95":
                    percentile(
                        0.95
                    ),

                "p99":
                    percentile(
                        0.99
                    ),
            },

            "busiest_routes": [
                {
                    "route":
                        name,

                    "requests":
                        count,
                }
                for name, count
                in busiest
            ],
        }


request_metrics = (
    RequestMetricsRegistry()
)
