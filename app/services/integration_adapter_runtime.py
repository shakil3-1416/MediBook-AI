from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from typing import Any

from app.services.integration_provider_contracts import (
    ProviderCapabilityContract,
    contracts,
)


class IntegrationAdapterError(
    RuntimeError
):
    pass


class IntegrationAdapterUnavailable(
    IntegrationAdapterError
):
    pass


class IntegrationOwnershipError(
    IntegrationAdapterError
):
    pass


@dataclass(
    slots=True
)
class SyncPayload:
    resource: str

    direction: str

    config: dict[
        str,
        Any,
    ]

    ownership: dict[
        str,
        Any,
    ]


@dataclass(
    slots=True
)
class SyncResult:
    records_seen: int = 0

    records_changed: int = 0

    detail: dict[
        str,
        Any,
    ] | None = None


class RuntimeIntegrationAdapter(
    ABC
):
    provider: str


    @abstractmethod
    async def pull(
        self,
        payload:
            SyncPayload,
    ) -> SyncResult:
        raise NotImplementedError


    @abstractmethod
    async def push(
        self,
        payload:
            SyncPayload,
    ) -> SyncResult:
        raise NotImplementedError


class UnavailableExternalAdapter(
    RuntimeIntegrationAdapter
):
    """
    Safe default for Connected/Hybrid integrations
    without a real provider implementation.

    Never pretends a sync succeeded.
    """

    def __init__(
        self,
        provider: str,
    ) -> None:
        self.provider = provider


    async def pull(
        self,
        payload:
            SyncPayload,
    ) -> SyncResult:
        del payload

        raise IntegrationAdapterUnavailable(
            f"Provider adapter '{self.provider}' "
            "is not implemented."
        )


    async def push(
        self,
        payload:
            SyncPayload,
    ) -> SyncResult:
        del payload

        raise IntegrationAdapterUnavailable(
            f"Provider adapter '{self.provider}' "
            "is not implemented."
        )


class AdapterRegistry:
    def __init__(
        self,
    ) -> None:
        self._factories = {}


    def register(
        self,
        provider: str,
        factory,
        *,
        supports_pull:
            frozenset[str] =
            frozenset(),
        supports_push:
            frozenset[str] =
            frozenset(),
        supports_webhooks:
            bool = False,
        supports_health_check:
            bool = False,
        notes:
            str = "",
    ) -> None:
        key = (
            provider
            .strip()
            .lower()
        )

        if not key:
            raise ValueError(
                "Provider cannot be blank."
            )

        self._factories[
            key
        ] = factory

        contracts.register(
            ProviderCapabilityContract(
                provider=key,
                executable=True,
                supports_pull=
                    frozenset(
                        supports_pull
                    ),
                supports_push=
                    frozenset(
                        supports_push
                    ),
                supports_webhooks=
                    supports_webhooks,
                supports_health_check=
                    supports_health_check,
                notes=(
                    notes
                    or
                    "Executable adapter registered."
                ),
            )
        )


    def resolve(
        self,
        provider: str,
    ) -> RuntimeIntegrationAdapter:
        key = (
            provider
            .strip()
            .lower()
        )

        factory = (
            self._factories
            .get(
                key
            )
        )

        if factory is None:
            return (
                UnavailableExternalAdapter(
                    key
                )
            )

        adapter = factory()

        if not isinstance(
            adapter,
            RuntimeIntegrationAdapter,
        ):
            raise TypeError(
                "Registered adapter must implement "
                "RuntimeIntegrationAdapter."
            )

        return adapter


registry = AdapterRegistry()
