import pytest

import saritasa_s3_tools

saritasa_s3_tools.S3FileTypeConfig(
    name="files",
    key=saritasa_s3_tools.keys.S3KeyWithPrefix("files"),
    content_length_range=(1, 20000000),
)

saritasa_s3_tools.S3FileTypeConfig(
    name="expires",
    key=saritasa_s3_tools.keys.S3KeyWithUUID("expires"),
    expires_in=1,
)


@pytest.fixture
def anyio_backend() -> str:
    """Specify async backend."""
    return "asyncio"
