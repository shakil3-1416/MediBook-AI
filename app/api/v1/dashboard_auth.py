from __future__ import annotations

from fastapi import (
    Depends,
    HTTPException,
)

# ------------------------------------------------------
# MediBook already has an authenticated user dependency.
# We resolve it dynamically here so we do not duplicate
# JWT/session logic or disturb patient authentication.
# ------------------------------------------------------


def _load_dependency():

    candidates = [
        (
            "app.api.deps.auth",
            "get_current_user",
        ),
        (
            "app.api.dependencies.auth",
            "get_current_user",
        ),
        (
            "app.core.auth",
            "get_current_user",
        ),
        (
            "app.api.v1.auth",
            "get_current_user",
        ),
    ]

    import importlib

    for module_name, attr in candidates:

        try:
            module = importlib.import_module(
                module_name
            )
        except Exception:
            continue

        dependency = getattr(
            module,
            attr,
            None,
        )

        if dependency is not None:
            return dependency

    raise RuntimeError(
        "Existing MediBook get_current_user "
        "dependency could not be located."
    )


get_current_user = _load_dependency()


async def dashboard_user(
    current_user=Depends(
        get_current_user
    ),
):

    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    return current_user
