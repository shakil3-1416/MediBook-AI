from __future__ import annotations

import logging
import time

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import (
    Request,
)

from app.core.observability import (
    log_event,
    new_request_id,
    new_trace_id,
    request_id_var,
    request_metrics,
    trace_id_var,
)


logger = logging.getLogger(
    "medibook.http"
)


class ObservabilityMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request:
            Request,
        call_next,
    ):
        incoming_request_id = (
            request.headers.get(
                "x-request-id"
            )
            or ""
        ).strip()


        request_id = (
            incoming_request_id[
                :128
            ]
            if incoming_request_id
            else new_request_id()
        )


        incoming_trace_id = (
            request.headers.get(
                "x-trace-id"
            )
            or ""
        ).strip()


        trace_id = (
            incoming_trace_id[
                :128
            ]
            if incoming_trace_id
            else new_trace_id()
        )


        request_token = (
            request_id_var.set(
                request_id
            )
        )

        trace_token = (
            trace_id_var.set(
                trace_id
            )
        )


        started = (
            time.perf_counter()
        )

        status_code = 500


        try:
            response = await call_next(
                request
            )

            status_code = (
                response.status_code
            )


            response.headers[
                "X-Request-ID"
            ] = request_id

            response.headers[
                "X-Trace-ID"
            ] = trace_id


            return response


        except Exception:
            duration_ms = (
                time.perf_counter()
                -
                started
            ) * 1000.0


            log_event(
                logger,
                logging.ERROR,
                "http.request.failed",
                method=
                    request.method,

                path=
                    request.url.path,

                status_code=500,

                duration_ms=
                    round(
                        duration_ms,
                        2,
                    ),
            )

            raise


        finally:
            duration_ms = (
                time.perf_counter()
                -
                started
            ) * 1000.0


            route = (
                request.scope.get(
                    "route"
                )
            )


            route_path = (
                getattr(
                    route,
                    "path",
                    None,
                )
                or request.url.path
            )


            request_metrics.observe(
                method=
                    request.method,

                route=
                    route_path,

                status_code=
                    status_code,

                duration_ms=
                    duration_ms,
            )


            log_event(
                logger,
                (
                    logging.ERROR
                    if status_code
                    >= 500
                    else
                    logging.WARNING
                    if status_code
                    >= 400
                    else
                    logging.INFO
                ),
                "http.request.completed",
                method=
                    request.method,

                route=
                    route_path,

                status_code=
                    status_code,

                duration_ms=
                    round(
                        duration_ms,
                        2,
                    ),
            )


            request_id_var.reset(
                request_token
            )

            trace_id_var.reset(
                trace_token
            )
