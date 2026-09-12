from app.api.v1.auth_verification import router as auth_verification_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.production_readiness import production_cors_origins, validate_production_environment


validate_production_environment(app_debug=settings.app_debug)

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

# Public hospital-scoped API used by embedded MediBook widgets.

# MEDIBOOK_DIRECT_HOSPITAL_PUBLIC_ROUTES
# These routes are registered directly on the final FastAPI app.
# This deliberately avoids nested-router topology ambiguity.

from app.api.v1.hospital_public import (
    hospital_doctors as _medibook_hospital_doctors,
    doctor_slots as _medibook_doctor_slots,
    hospital_widget_config as _medibook_hospital_widget_config,
)

app.add_api_route(
    "/api/v1/hospital-public/{hospital_slug}/doctors",
    _medibook_hospital_doctors,
    methods=["GET"],
    tags=["hospital-public"],
)

app.add_api_route(
    "/api/v1/hospital-public/{hospital_slug}/doctors/{doctor_id}/slots",
    _medibook_doctor_slots,
    methods=["GET"],
    tags=["hospital-public"],
)

app.add_api_route(
    "/api/v1/hospital-public/{hospital_slug}",
    _medibook_hospital_widget_config,
    methods=["GET"],
    tags=["hospital-public"],
)

# MEDIBOOK_WIDGET_CONVERSATION_ROUTER
from app.api.v1.widget_conversations import router as widget_conversation_router

app.include_router(
    widget_conversation_router,
    prefix="/api/v1",
)


# MEDIBOOK_FINAL_ROUTE_RESTORE_V1
#
# The project recreates/constructs the exported FastAPI app before this
# point. Attach the original application router to the FINAL app object,
# then explicitly attach widget conversation endpoints.

from app.api.v1.router import api_router as _medibook_core_api_router

_existing_paths = {
    getattr(_route, "path", "")
    for _route in app.routes
}

# Restore original MediBook API surface only if its core routes are absent.
if not any(
    (
        "/chat" in _path
        or "/appointments" in _path
        or "/conversations" in _path
    )
    for _path in _existing_paths
):
    app.include_router(
        _medibook_core_api_router,
        prefix="/api/v1",
    )

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


# MEDIBOOK_CORE_ROUTER_RECOVERY_V2
#
# Attach the project's existing core API routers to the FINAL exported
# FastAPI app. This runs after all earlier app construction/reassignment.

import importlib as _mb_importlib


def _mb_route_keys(_app):
    return {
        (
            getattr(_route, "path", ""),
            tuple(
                sorted(
                    getattr(_route, "methods", [])
                    or []
                )
            ),
        )
        for _route in _app.routes
    }


def _mb_attach_existing_router(_module_name):
    try:
        _module = _mb_importlib.import_module(
            _module_name
        )
    except Exception:
        return False

    _router = getattr(
        _module,
        "router",
        None,
    )

    if _router is None:
        return False

    _current_paths = {
        getattr(_route, "path", "")
        for _route in app.routes
    }

    _router_paths = [
        getattr(_route, "path", "")
        for _route in _router.routes
    ]

    if not _router_paths:
        return False

    # Routers in app/api/v1 normally expose paths such as
    # /chat/stream, /appointments, /conversations.
    #
    # If they already contain /api/v1, do not double-prefix them.
    _prefix = (
        ""
        if all(
            _path.startswith("/api/v1")
            for _path in _router_paths
        )
        else "/api/v1"
    )

    _expected = {
        f"{_prefix}{_path}"
        for _path in _router_paths
    }

    # Include only if at least one route from this router is absent.
    if _expected.issubset(
        _current_paths
    ):
        return True

    app.include_router(
        _router,
        prefix=_prefix,
    )

    return True


for _mb_module_name in (
    "app.api.v1.chat",
    "app.api.v1.appointments",
    "app.api.v1.conversations",
    "app.api.v1.auth",
):
    _mb_attach_existing_router(
        _mb_module_name
    )


# MEDIBOOK_EXPLICIT_CORE_PREFIX_RECOVERY
#
# These leaf APIRouters intentionally expose relative paths.
# Their domain prefixes were previously supplied by a parent router.
# Attach them directly to the FINAL FastAPI app with explicit prefixes.

from app.api.v1.chat import router as _mb_chat_router
from app.api.v1.appointments import router as _mb_appointments_router
from app.api.v1.conversations import router as _mb_conversations_router
from app.api.v1.auth import router as _mb_auth_router


def _mb_has_path(_path: str) -> bool:
    return any(
        getattr(_route, "path", None) == _path
        for _route in app.routes
    )


# CHAT
if not _mb_has_path("/api/v1/chat/stream"):
    app.include_router(
        _mb_chat_router,
        prefix="/api/v1/chat",
    )


# APPOINTMENTS
if not _mb_has_path("/api/v1/appointments"):
    app.include_router(
        _mb_appointments_router,
        prefix="/api/v1/appointments",
    )


# CONVERSATIONS
if not _mb_has_path("/api/v1/conversations"):
    app.include_router(
        _mb_conversations_router,
        prefix="/api/v1/conversations",
    )


# AUTH
if not _mb_has_path("/api/v1/auth/login"):
    app.include_router(
        _mb_auth_router,
        prefix="/api/v1/auth",
    )


# MEDIBOOK_DIRECT_CORE_ROUTES_V4
#
# Compatibility-safe direct registration.
# Do not copy unsupported APIRoute metadata into FastAPI.add_api_route().

from fastapi.routing import APIRoute

from app.api.v1.chat import router as _mb_chat_leaf
from app.api.v1.appointments import router as _mb_appointments_leaf
from app.api.v1.conversations import router as _mb_conversations_leaf
from app.api.v1.auth import router as _mb_auth_leaf


def _mb_final_paths():
    return {
        getattr(_route, "path", "")
        for _route in app.routes
    }


def _mb_mount_leaf(
    _router,
    _prefix: str,
):
    _existing = _mb_final_paths()

    for _route in _router.routes:

        if not isinstance(
            _route,
            APIRoute,
        ):
            continue

        _full_path = (
            _prefix
            + _route.path
        )

        if _full_path in _existing:
            continue

        # Keep registration deliberately minimal.
        # Endpoint Depends() parameters remain on the original function.
        app.add_api_route(
            _full_path,
            _route.endpoint,
            methods=list(
                _route.methods or []
            ),
            response_model=_route.response_model,
            status_code=_route.status_code,
            tags=_route.tags,
            dependencies=_route.dependencies,
            summary=_route.summary,
            description=_route.description,
            responses=_route.responses,
            deprecated=_route.deprecated,
            name=_route.name,
            include_in_schema=_route.include_in_schema,
        )

        _existing.add(
            _full_path
        )


_mb_mount_leaf(
    _mb_chat_leaf,
    "/api/v1/chat",
)

_mb_mount_leaf(
    _mb_appointments_leaf,
    "/api/v1/appointments",
)

_mb_mount_leaf(
    _mb_conversations_leaf,
    "/api/v1/conversations",
)

_mb_mount_leaf(
    _mb_auth_leaf,
    "/api/v1/auth",
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
