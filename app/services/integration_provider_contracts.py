from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ProviderCapabilityContract:
    provider: str

    executable: bool = False

    supports_pull: frozenset[str] = field(
        default_factory=
            frozenset
    )

    supports_push: frozenset[str] = field(
        default_factory=
            frozenset
    )

    supports_webhooks: bool = False

    supports_health_check: bool = False

    notes: str = (
        "Provider adapter is not registered."
    )


class ProviderContractRegistry:
    def __init__(
        self,
    ) -> None:
        self._contracts: dict[
            str,
            ProviderCapabilityContract,
        ] = {}


    def register(
        self,
        contract:
            ProviderCapabilityContract,
    ) -> None:
        key = (
            contract.provider
            .strip()
            .lower()
        )

        if not key:
            raise ValueError(
                "Provider cannot be blank."
            )

        self._contracts[
            key
        ] = contract


    def resolve(
        self,
        provider: str,
    ) -> ProviderCapabilityContract:
        key = (
            provider
            .strip()
            .lower()
        )

        contract = (
            self._contracts
            .get(
                key
            )
        )


        if contract is not None:
            return contract


        return ProviderCapabilityContract(
            provider=key,
            executable=False,
            notes=(
                "No executable provider contract "
                "has been registered."
            ),
        )


    def all(
        self,
    ) -> list[
        ProviderCapabilityContract
    ]:
        return sorted(
            self._contracts.values(),
            key=lambda item:
                item.provider,
        )


contracts = ProviderContractRegistry()
