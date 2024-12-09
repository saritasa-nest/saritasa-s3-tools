import contextlib

from . import constants, keys
from .client import S3Client
from .configs import S3FileTypeConfig

with contextlib.suppress(ImportError):
    from .async_client import AsyncS3Client

with contextlib.suppress(ImportError):
    from . import testing

with contextlib.suppress(ImportError):
    from . import factory

__all__ = (
    "AsyncS3Client",
    "S3Client",
    "S3FileTypeConfig",
    "constants",
    "factory",
    "keys",
    "testing",
)
