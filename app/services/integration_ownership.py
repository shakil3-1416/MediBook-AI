from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class IntegrationOwnershipError(
    ValueError
):
    pass


class DataMode(
    StrEnum
):
    MANAGED = "managed"
    CONNECTED = "connected"
    HYBRID = "hybrid"


class ResourceOwner(
    StrEnum
):
    MEDIBOOK = "medibook"
    EXTERNAL = "external"


class SyncDirection(
    StrEnum
):
    PULL = "pull"
    PUSH = "push"


SUPPORTED_SYNC_RESOURCES = frozenset(
    {
        "appointments",
        "doctors",
        "schedules",
    }
)


OWNER_ALIASES = {
    "medibook":
        ResourceOwner.MEDIBOOK,

    "managed":
        ResourceOwner.MEDIBOOK,

    "local":
        ResourceOwner.MEDIBOOK,

    "internal":
        ResourceOwner.MEDIBOOK,

    "external":
        ResourceOwner.EXTERNAL,

    "connected":
        ResourceOwner.EXTERNAL,

    "provider":
        ResourceOwner.EXTERNAL,

    "remote":
        ResourceOwner.EXTERNAL,
}


@dataclass(
    frozen=True,
    slots=True,
)
class OwnershipDecision:
    allowed: bool

    mode: DataMode

    resource: str

    owner: ResourceOwner | None

    direction: SyncDirection

    reason: str


def normalize_mode(
    value: Any,
) -> DataMode:
    text = str(
        value
        or ""
    ).strip().lower()

    try:
        return DataMode(
            text
        )

    except ValueError as exc:
        raise IntegrationOwnershipError(
            "source_mode must be one of: "
            "managed, connected, hybrid."
        ) from exc


def normalize_resource(
    resource: Any,
) -> str:
    value = str(
        resource
        or ""
    ).strip().lower()

    if value not in (
        SUPPORTED_SYNC_RESOURCES
    ):
        raise IntegrationOwnershipError(
            "Unsupported sync resource: "
            f"{value!r}. "
            "Supported resources are: "
            + ", ".join(
                sorted(
                    SUPPORTED_SYNC_RESOURCES
                )
            )
            + "."
        )

    return value


def normalize_owner(
    value: Any,
) -> ResourceOwner:
    key = str(
        value
        or ""
    ).strip().lower()

    owner = OWNER_ALIASES.get(
        key
    )

    if owner is None:
        raise IntegrationOwnershipError(
            "Resource owner must resolve to "
            "'medibook' or 'external'."
        )

    return owner


def normalize_ownership(
    *,
    source_mode: Any,
    ownership: dict[str, Any] | None,
) -> dict[str, str]:
    mode = normalize_mode(
        source_mode
    )

    raw = dict(
        ownership
        or {}
    )

    normalized: dict[
        str,
        str,
    ] = {}


    for resource, owner in raw.items():
        normalized_resource = (
            normalize_resource(
                resource
            )
        )

        normalized_owner = (
            normalize_owner(
                owner
            )
        )

        normalized[
            normalized_resource
        ] = normalized_owner.value


    if mode == DataMode.MANAGED:
        for resource, owner in (
            normalized.items()
        ):
            if owner != (
                ResourceOwner.MEDIBOOK.value
            ):
                raise IntegrationOwnershipError(
                    "Managed mode cannot declare "
                    f"{resource!r} as externally owned."
                )

        return normalized


    if mode == DataMode.CONNECTED:
        for resource, owner in (
            normalized.items()
        ):
            if owner != (
                ResourceOwner.EXTERNAL.value
            ):
                raise IntegrationOwnershipError(
                    "Connected mode cannot declare "
                    f"{resource!r} as MediBook-owned."
                )

        return normalized


    if not normalized:
        raise IntegrationOwnershipError(
            "Hybrid mode requires explicit "
            "resource ownership."
        )


    return normalized


def ownership_for_resource(
    *,
    source_mode: Any,
    ownership: dict[str, Any] | None,
    resource: Any,
) -> ResourceOwner | None:
    mode = normalize_mode(
        source_mode
    )

    resource_name = normalize_resource(
        resource
    )

    normalized = normalize_ownership(
        source_mode=
            mode,

        ownership=
            ownership,
    )


    if resource_name in normalized:
        return ResourceOwner(
            normalized[
                resource_name
            ]
        )


    if mode == DataMode.MANAGED:
        return ResourceOwner.MEDIBOOK


    if mode == DataMode.CONNECTED:
        return ResourceOwner.EXTERNAL


    return None


def decide_sync_direction(
    *,
    source_mode: Any,
    ownership: dict[str, Any] | None,
    resource: Any,
    direction: Any,
) -> OwnershipDecision:
    mode = normalize_mode(
        source_mode
    )

    resource_name = normalize_resource(
        resource
    )

    try:
        sync_direction = SyncDirection(
            str(
                direction
            ).strip().lower()
        )

    except ValueError as exc:
        raise IntegrationOwnershipError(
            "direction must be 'pull' or 'push'."
        ) from exc


    owner = ownership_for_resource(
        source_mode=
            mode,

        ownership=
            ownership,

        resource=
            resource_name,
    )


    if mode == DataMode.MANAGED:
        return OwnershipDecision(
            allowed=False,
            mode=mode,
            resource=
                resource_name,
            owner=
                ResourceOwner.MEDIBOOK,
            direction=
                sync_direction,
            reason=(
                "Managed mode uses MediBook "
                "as the source of truth and "
                "does not execute external sync."
            ),
        )


    if owner is None:
        return OwnershipDecision(
            allowed=False,
            mode=mode,
            resource=
                resource_name,
            owner=None,
            direction=
                sync_direction,
            reason=(
                "Hybrid mode requires explicit "
                "ownership for this resource."
            ),
        )


    if owner == ResourceOwner.EXTERNAL:
        allowed = (
            sync_direction
            ==
            SyncDirection.PULL
        )

        return OwnershipDecision(
            allowed=allowed,
            mode=mode,
            resource=
                resource_name,
            owner=owner,
            direction=
                sync_direction,
            reason=(
                "External-owned resources may "
                "be pulled into MediBook."
                if allowed
                else
                "External-owned resources cannot "
                "be pushed from MediBook."
            ),
        )


    allowed = (
        sync_direction
        ==
        SyncDirection.PUSH
    )


    return OwnershipDecision(
        allowed=allowed,
        mode=mode,
        resource=
            resource_name,
        owner=owner,
        direction=
            sync_direction,
        reason=(
            "MediBook-owned resources may "
            "be pushed to the external system."
            if allowed
            else
            "MediBook-owned resources cannot "
            "be overwritten by an external pull."
        ),
    )
