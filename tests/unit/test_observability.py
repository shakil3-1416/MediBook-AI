from __future__ import annotations

import json
import logging

from app.core.observability import (
    JsonFormatter,
    RequestMetricsRegistry,
    request_id_var,
    sanitize_log_value,
    trace_id_var,
)


def test_sensitive_log_fields_are_redacted():
    value = sanitize_log_value(
        {
            "provider":
                "fake",

            "api_key":
                "do-not-print",

            "nested": {
                "access_token":
                    "secret-token",

                "safe":
                    "ok",
            },
        }
    )

    assert (
        value[
            "api_key"
        ]
        ==
        "[redacted]"
    )

    assert (
        value[
            "nested"
        ][
            "access_token"
        ]
        ==
        "[redacted]"
    )

    assert (
        value[
            "nested"
        ][
            "safe"
        ]
        ==
        "ok"
    )


def test_json_formatter_contains_correlation_ids():
    request_token = (
        request_id_var.set(
            "request-test"
        )
    )

    trace_token = (
        trace_id_var.set(
            "trace-test"
        )
    )

    try:
        formatter = JsonFormatter()

        record = (
            logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname=__file__,
                lineno=1,
                msg="hello",
                args=(),
                exc_info=None,
            )
        )

        rendered = json.loads(
            formatter.format(
                record
            )
        )

        assert (
            rendered[
                "request_id"
            ]
            ==
            "request-test"
        )

        assert (
            rendered[
                "trace_id"
            ]
            ==
            "trace-test"
        )

    finally:
        request_id_var.reset(
            request_token
        )

        trace_id_var.reset(
            trace_token
        )


def test_request_metrics_snapshot():
    registry = RequestMetricsRegistry(
        max_samples=10
    )

    registry.observe(
        method="GET",
        route="/health",
        status_code=200,
        duration_ms=10.0,
    )

    registry.observe(
        method="GET",
        route="/boom",
        status_code=500,
        duration_ms=30.0,
    )

    snapshot = registry.snapshot(
        window_seconds=60
    )

    assert (
        snapshot[
            "requests"
        ]
        ==
        2
    )

    assert (
        snapshot[
            "server_errors"
        ]
        ==
        1
    )

    assert (
        snapshot[
            "server_error_rate"
        ]
        ==
        0.5
    )
