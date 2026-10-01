from app.api.v1.auth_verification import router as auth_verification_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.observability import (
    configure_observability_logging,
)
from app.core.observability_middleware import (
    ObservabilityMiddleware,
)
from app.core.production_readiness import production_cors_origins, validate_production_environment


validate_production_environment(app_debug=settings.app_debug)

configure_observability_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
)

# MediBook public hospital widget API
app.add_middleware(
    CORSMiddleware,
    allow_origins=production_cors_origins([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
    }


app.include_router(
    api_router,
    prefix="/api/v1",
)

# V1 API registration rule (M6 OpenAPI gate):
# api_router (app/api/v1/router.py) is the single registration point for
# the routers it lists. FastAPI keeps included routers nested, so
# path-presence checks against app.routes cannot see their routes, and
# re-including or re-mounting them below registers duplicate operations.

# MEDIBOOK_WIDGET_CONVERSATION_LEAF_ROUTES
# Widget-conversation endpoints are registered explicitly on the final app
# so they cannot disappear because of nested-router topology.
from app.api.v1.widget_conversations import (
    create_conversation as _mb_wc_create,
    list_conversations as _mb_wc_list,
    get_conversation as _mb_wc_get,
    add_message as _mb_wc_add_message,
    edit_user_message as _mb_wc_edit_message,
)

_final_paths = {
    getattr(_route, "path", "")
    for _route in app.routes
}

if "/api/v1/widget-conversations" not in _final_paths:
    app.add_api_route(
        "/api/v1/widget-conversations",
        _mb_wc_create,
        methods=["POST"],
        tags=["widget-conversations"],
    )

if "/api/v1/widget-conversations/{hospital_slug}" not in _final_paths:
    app.add_api_route(
        "/api/v1/widget-conversations/{hospital_slug}",
        _mb_wc_list,
        methods=["GET"],
        tags=["widget-conversations"],
    )

if "/api/v1/widget-conversations/{hospital_slug}/{conversation_id}" not in _final_paths:
    app.add_api_route(
        "/api/v1/widget-conversations/{hospital_slug}/{conversation_id}",
        _mb_wc_get,
        methods=["GET"],
        tags=["widget-conversations"],
    )

if "/api/v1/widget-conversations/{conversation_id}/messages" not in _final_paths:
    app.add_api_route(
        "/api/v1/widget-conversations/{conversation_id}/messages",
        _mb_wc_add_message,
        methods=["POST"],
        tags=["widget-conversations"],
    )

if "/api/v1/widget-conversations/{conversation_id}/messages/{message_id}" not in _final_paths:
    app.add_api_route(
        "/api/v1/widget-conversations/{conversation_id}/messages/{message_id}",
        _mb_wc_edit_message,
        methods=["PATCH"],
        tags=["widget-conversations"],
    )


# MEDIBOOK_HOSPITAL_OPERATIONS_V1
from app.api.v1.hospital_operations import (
    router as hospital_operations_router,
)

app.include_router(
    hospital_operations_router,
    prefix="/api/v1",
)

app.include_router(auth_verification_router, prefix="/api/v1")

# MEDIBOOK_IDENTITY_V2_ROUTER
from app.api.v1.identity_v2 import (
    router as identity_v2_router,
)

app.include_router(
    identity_v2_router,
    prefix="/api/v1",
)


# M6_FINAL_OBSERVABILITY_MIDDLEWARE
from app.core.observability_middleware import ObservabilityMiddleware

if not any(
    getattr(m, "cls", None) is ObservabilityMiddleware
    for m in app.user_middleware
):
    app.add_middleware(ObservabilityMiddleware)

app.openapi_schema = None


# M6_FINAL_SECURITY_MIDDLEWARE
from app.core.security_middleware import SecurityHardeningMiddleware

if not any(
    getattr(middleware, "cls", None)
    is SecurityHardeningMiddleware
    for middleware in app.user_middleware
):
    app.add_middleware(
        SecurityHardeningMiddleware
    )

app.openapi_schema = None


# M6_FINAL_ROUTE_CONVERGENCE
from fastapi.routing import APIRoute as _M6APIRoute

_m6_seen = set()
_m6_routes = []

for _m6_route in app.router.routes:
    if isinstance(
        _m6_route,
        _M6APIRoute,
    ):
        _m6_methods = tuple(
            sorted(
                method
                for method
                in (
                    _m6_route.methods
                    or set()
                )
                if method
                not in {
                    "HEAD",
                    "OPTIONS",
                }
            )
        )

        _m6_key = (
            _m6_route.path,
            _m6_methods,
        )

        if _m6_key in _m6_seen:
            continue

        _m6_seen.add(
            _m6_key
        )

    _m6_routes.append(
        _m6_route
    )

app.router.routes[:] = _m6_routes
app.openapi_schema = None
