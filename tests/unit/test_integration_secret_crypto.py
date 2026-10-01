from __future__ import annotations

from cryptography.fernet import (
    Fernet,
)
import pytest

from app.services.integration_secret_crypto import (
    ENVELOPE_MARKER,
    IntegrationMasterKeyMissing,
    REDACTED_VALUE,
    contains_plaintext_secret,
    decrypt_sensitive_config,
    encrypt_sensitive_config,
    is_encrypted_envelope,
    redact_sensitive_config,
)


def _key() -> str:
    return (
        Fernet.generate_key()
        .decode(
            "ascii"
        )
    )


def test_encrypts_only_sensitive_values(
    monkeypatch,
):
    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    original = {
        "provider":
            "example",

        "base_url":
            "https://example.test",

        "api_key":
            "secret-api-key",

        "nested": {
            "access_token":
                "token-123",

            "region":
                "bd",
        },
    }


    encrypted = (
        encrypt_sensitive_config(
            original
        )
    )


    assert (
        encrypted[
            "provider"
        ]
        ==
        "example"
    )

    assert (
        encrypted[
            "base_url"
        ]
        ==
        "https://example.test"
    )

    assert is_encrypted_envelope(
        encrypted[
            "api_key"
        ]
    )

    assert is_encrypted_envelope(
        encrypted[
            "nested"
        ][
            "access_token"
        ]
    )

    assert (
        encrypted[
            "api_key"
        ][
            ENVELOPE_MARKER
        ]
        is True
    )

    assert (
        "secret-api-key"
        not in str(
            encrypted
        )
    )

    assert (
        "token-123"
        not in str(
            encrypted
        )
    )


def test_round_trip(
    monkeypatch,
):
    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    original = {
        "client_id":
            "public-id",

        "client_secret":
            "secret",

        "metadata": {
            "webhook_secret":
                "hook",
        },
    }


    encrypted = (
        encrypt_sensitive_config(
            original
        )
    )

    decrypted = (
        decrypt_sensitive_config(
            encrypted
        )
    )


    assert (
        decrypted
        ==
        original
    )


def test_encryption_is_idempotent(
    monkeypatch,
):
    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    original = {
        "api_key":
            "secret",
    }


    once = encrypt_sensitive_config(
        original
    )

    twice = encrypt_sensitive_config(
        once
    )


    assert (
        once
        ==
        twice
    )


def test_public_response_redacts_plaintext_and_ciphertext(
    monkeypatch,
):
    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    original = {
        "api_key":
            "secret",

        "base_url":
            "https://example.test",
    }


    encrypted = encrypt_sensitive_config(
        original
    )

    public = redact_sensitive_config(
        encrypted
    )


    assert (
        public[
            "api_key"
        ]
        ==
        REDACTED_VALUE
    )

    assert (
        public[
            "base_url"
        ]
        ==
        "https://example.test"
    )

    assert (
        "secret"
        not in str(
            public
        )
    )

    assert (
        "ciphertext"
        not in str(
            public
        )
    )


def test_plaintext_secret_detection(
    monkeypatch,
):
    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    plain = {
        "api_key":
            "plain",
    }

    encrypted = encrypt_sensitive_config(
        plain
    )


    assert contains_plaintext_secret(
        plain
    )

    assert not contains_plaintext_secret(
        encrypted
    )


def test_master_key_required_for_encryption(
    monkeypatch,
):
    monkeypatch.delenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        raising=False,
    )

    with pytest.raises(
        IntegrationMasterKeyMissing
    ):
        encrypt_sensitive_config(
            {
                "api_key":
                    "secret",
            }
        )


def test_hospital_integration_orm_guard_encrypts_config(
    monkeypatch,
):
    from app.models.hospital import (
        HospitalIntegration,
    )

    from app.services.integration_config_security import (
        _encrypt_model_config,
    )

    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    integration = HospitalIntegration()

    integration.config = {
        "provider_url":
            "https://example.test",

        "api_key":
            "plain-secret",

        "nested": {
            "webhook_secret":
                "hook-secret",
        },
    }

    _encrypt_model_config(
        integration
    )

    assert (
        integration.config[
            "provider_url"
        ]
        ==
        "https://example.test"
    )

    assert is_encrypted_envelope(
        integration.config[
            "api_key"
        ]
    )

    assert is_encrypted_envelope(
        integration.config[
            "nested"
        ][
            "webhook_secret"
        ]
    )

    assert (
        "plain-secret"
        not in str(
            integration.config
        )
    )

    assert (
        "hook-secret"
        not in str(
            integration.config
        )
    )


def test_orm_guard_is_idempotent(
    monkeypatch,
):
    from app.models.hospital import (
        HospitalIntegration,
    )

    from app.services.integration_config_security import (
        _encrypt_model_config,
    )

    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    integration = HospitalIntegration()

    integration.config = {
        "api_key":
            "secret",
    }

    _encrypt_model_config(
        integration
    )

    once = integration.config

    _encrypt_model_config(
        integration
    )

    assert (
        integration.config
        ==
        once
    )


def test_runtime_and_public_forms_are_separate(
    monkeypatch,
):
    from app.services.integration_config_security import (
        prepare_integration_config_for_public_response,
        prepare_integration_config_for_runtime,
        prepare_integration_config_for_storage,
    )

    monkeypatch.setenv(
        "MEDIBOOK_INTEGRATION_MASTER_KEY",
        _key(),
    )

    original = {
        "base_url":
            "https://example.test",

        "access_token":
            "runtime-token",
    }

    stored = (
        prepare_integration_config_for_storage(
            original
        )
    )

    runtime = (
        prepare_integration_config_for_runtime(
            stored
        )
    )

    public = (
        prepare_integration_config_for_public_response(
            stored
        )
    )

    assert runtime == original

    assert (
        public[
            "access_token"
        ]
        ==
        REDACTED_VALUE
    )

    assert (
        "runtime-token"
        not in str(
            public
        )
    )

    assert (
        "ciphertext"
        not in str(
            public
        )
    )
