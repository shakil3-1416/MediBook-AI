import pytest

from app.services.profile_image_storage import (
    InvalidProfileImage,
    validate_profile_image,
)


PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"test"
)


def test_accepts_png_signature():

    assert (
        validate_profile_image(
            PNG,
            "image/png",
        )
        ==
        ".png"
    )


def test_rejects_fake_png():

    with pytest.raises(
        InvalidProfileImage,
    ):
        validate_profile_image(
            b"not-an-image",
            "image/png",
        )


def test_rejects_unsupported_type():

    with pytest.raises(
        InvalidProfileImage,
    ):
        validate_profile_image(
            b"anything",
            "image/svg+xml",
        )
