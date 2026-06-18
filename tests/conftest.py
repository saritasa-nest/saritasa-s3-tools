import typing

import pytest

import saritasa_s3_tools

saritasa_s3_tools.S3FileTypeConfig(
    name="files",
    key=saritasa_s3_tools.keys.WithPrefixUUIDFolder("files"),
    content_length_range=(1, 20000000),
)

saritasa_s3_tools.S3FileTypeConfig(
    name="expires",
    key=saritasa_s3_tools.keys.WithPrefixUUIDFileName("expires"),
    expires_in=1,
)


@pytest.fixture
def anyio_backend() -> str:
    """Specify async backend."""
    return "asyncio"


@pytest.fixture(scope="session")
def s3_bucket_policy(
    s3_bucket_name: str,
) -> dict[str, typing.Any]:
    """Get the policy of s3 bucket."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadAvatars",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": (
                    f"arn:aws:s3:::{s3_bucket_name}/django-anon-files/*"
                ),
            },
        ],
    }


@pytest.fixture(scope="session")
def s3_bucket_delete_on_teardown() -> bool:
    """Delete bucket on teardown."""
    return True
