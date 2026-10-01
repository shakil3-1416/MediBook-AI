from __future__ import annotations

from app.services.integration_contract_validation import (
    validate_integration_contract,
    validate_hospital_integration_model,
)

from app.services.integration_config_security import (
    prepare_integration_config_for_public_response,
    prepare_integration_config_for_runtime,
    prepare_integration_config_for_storage,
)

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.control_plane import HospitalOperationsAudit
from app.models.hospital import HospitalIntegration


DOMAINS = {
    "doctors",
    "schedules",
    "appointments",
}

SECRET_MARKERS = (
    "secret",
    "password",
    "token",
    "api_key",
    "apikey",
    "credential",
    "private_key",
)


def utcnow():
    return datetime.now(timezone.utc)


def _is_secret(name: str) -> bool:
    normalized = name.lower()

    return any(
        marker in normalized
        for marker in SECRET_MARKERS
    )


def sanitize_config(value):
    if isinstance(value, dict):
        return {
            key: (
                "***"
                if _is_secret(str(key))
                else sanitize_config(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            sanitize_config(item)
            for item in value
        ]

    return value


def contains_secrets(value) -> bool:
    if isinstance(value, dict):
        return any(
            _is_secret(str(key))
            or contains_secrets(item)
            for key, item in value.items()
        )

    if isinstance(value, list):
        return any(
            contains_secrets(item)
            for item in value
        )

    return False


class IntegrationAdapter(ABC):
    @abstractmethod
    async def health(self) -> dict:
        raise NotImplementedError

    async def sync(self) -> dict:
        raise NotImplementedError(
            "This connector does not implement synchronization."
        )


class ManagedAdapter(IntegrationAdapter):
    async def health(self) -> dict:
        return {
            "status": "connected",
            "message": (
                "MediBook-managed data source is available."
            ),
        }


class ExternalAdapterUnavailable(IntegrationAdapter):
    def __init__(
        self,
        provider: str,
    ):
        self.provider = provider

    async def health(self) -> dict:
        return {
            "status": "degraded",
            "message": (
                f"External adapter for {self.provider} "
                "has not been installed."
            ),
        }


class IntegrationCenter:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    @staticmethod
    def validate_mode(
        source_mode: str,
        ownership: dict | None,
    ) -> dict:
        mode = source_mode.strip().lower()

        if mode not in {
            "managed",
            "connected",
            "hybrid",
        }:
            raise ValueError(
                "source_mode must be managed, connected, or hybrid."
            )

        if mode == "managed":
            return {
                domain: "managed"
                for domain in DOMAINS
            }

        if mode == "connected":
            return {
                domain: "connected"
                for domain in DOMAINS
            }

        ownership = ownership or {}

        missing = DOMAINS - set(
            ownership
        )

        if missing:
            raise ValueError(
                "Hybrid integrations require explicit ownership "
                "for doctors, schedules, and appointments."
            )

        normalized = {}

        for domain in DOMAINS:
            owner = str(
                ownership[domain]
            ).lower()

            if owner not in {
                "managed",
                "connected",
            }:
                raise ValueError(
                    f"Invalid ownership for {domain}."
                )

            normalized[domain] = owner

        return normalized

    @staticmethod
    def adapter(
        integration: HospitalIntegration,
    ) -> IntegrationAdapter:
        if integration.source_mode == "managed":
            return ManagedAdapter()

        return ExternalAdapterUnavailable(
            integration.provider
        )

    async def list(
        self,
        hospital_id: UUID,
    ):
        result = await self.session.execute(
            select(HospitalIntegration)
            .where(
                HospitalIntegration.hospital_id
                == hospital_id
            )
            .order_by(
                HospitalIntegration.provider
            )
        )

        return list(
            result.scalars().all()
        )

    async def get(
        self,
        hospital_id: UUID,
        integration_id: UUID,
    ):
        return await self.session.scalar(
            select(HospitalIntegration).where(
                HospitalIntegration.id
                == integration_id,
                HospitalIntegration.hospital_id
                == hospital_id,
            )
        )

    async def health_check(
        self,
        integration: HospitalIntegration,
    ):
        result = await self.adapter(
            integration
        ).health()

        integration.status = result[
            "status"
        ]

        integration.last_checked_at = utcnow()

        integration.last_error = (
            result["message"]
            if result["status"]
            in {"degraded", "error"}
            else None
        )

        await self.session.flush()

        return result

    async def audit(
        self,
        *,
        hospital_id: UUID,
        actor_user_id: UUID | None,
        integration: HospitalIntegration,
        action: str,
        before: dict | None = None,
    ):
        self.session.add(
            HospitalOperationsAudit(
                hospital_id=hospital_id,
                actor_user_id=actor_user_id,
                entity_type="hospital_integration",
                entity_id=integration.id,
                action=action,
                before_state=before or {},
                after_state=self.serialize(
                    integration
                ),
                metadata_json={},
            )
        )

    @staticmethod
    def serialize(
        integration: HospitalIntegration,
    ):
        return {
            "id": integration.id,
            "provider": integration.provider,
            "integration_type":
                integration.integration_type,
            "source_mode":
                integration.source_mode,
            "status":
                integration.status,
            "sync_status":
                integration.sync_status,
            "ownership":
                integration.ownership or {},
            "config":
                sanitize_config(
                    integration.config or {}
                ),
            "has_secrets":
                contains_secrets(
                    integration.config or {}
                ),
            "is_active":
                integration.is_active,
            "last_checked_at":
                integration.last_checked_at,
            "last_sync_at":
                integration.last_sync_at,
            "last_error":
                integration.last_error,
            "updated_at":
                integration.updated_at,
        }


def integration_config_for_runtime(
    integration,
):
    return prepare_integration_config_for_runtime(
        getattr(
            integration,
            "config",
            None,
        )
    )


def integration_config_for_public_response(
    integration,
):
    return prepare_integration_config_for_public_response(
        getattr(
            integration,
            "config",
            None,
        )
    )


def validate_integration_configuration(
    *,
    source_mode,
    provider,
    ownership,
):
    return validate_integration_contract(
        source_mode=
            source_mode,

        provider=
            provider,

        ownership=
            ownership,
    )
