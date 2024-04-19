import collections.abc

import pytest

import botocore.credentials
import mypy_boto3_s3

import saritasa_s3_tools


def pytest_addoption(parser: pytest.Parser) -> None:
    """Set up cmd args."""
    parser.addoption(
        "--sqlalchemy-echo",
        action="store_true",
        default=False,
        help="Should sqlalchemy print sql queries",
    )
    parser.addini(
        "s3_access_key",
        "Access key for s3.",
    )
    parser.addini(
        "s3_secret_key",
        "Secret key for s3.",
    )
    parser.addini(
        "s3_endpoint_url",
        "Endpoint for s3.",
    )
    parser.addini(
        "s3_region",
        "Region for s3.",
    )
    parser.addini(
        "s3_bucket",
        "Bucket for s3.",
    )


@pytest.fixture
def access_key_getter(
    request: pytest.FixtureRequest,
) -> collections.abc.Callable[
    [],
    botocore.credentials.Credentials,
]:
    """Set up cred getter."""
    if (
        s3_access_key := request.config.inicfg.get(
            "s3_access_key",
            "",
        )
    ) and (
        s3_secret_key := request.config.inicfg.get(
            "s3_secret_key",
            "",
        )
    ):
        return lambda: botocore.credentials.Credentials(
            access_key=str(s3_access_key),
            secret_key=str(s3_secret_key),
        )
    raise NotImplementedError(  # pragma: no cover
        "Please set up `access_key_getter` fixture or "
        "set `s3_access_key` and `s3_secret_key` in `.ini` file.",
    )


@pytest.fixture
def s3_endpoint_url_getter(
    request: pytest.FixtureRequest,
) -> (
    collections.abc.Callable[
        [],
        str | None,
    ]
    | None
):
    """Set up url getter."""
    if s3_endpoint_url := request.config.inicfg.get("s3_endpoint_url", ""):
        return lambda: str(s3_endpoint_url)
    return None  # pragma: no cover


@pytest.fixture
def s3_region(
    request: pytest.FixtureRequest,
) -> str:
    """Get s3 region."""
    return str(request.config.inicfg.get("s3_region", ""))


@pytest.fixture
def boto3_client(
    access_key_getter: collections.abc.Callable[
        [],
        botocore.credentials.Credentials,
    ],
    s3_endpoint_url_getter: collections.abc.Callable[
        [],
        str | None,
    ]
    | None,
    s3_region: str,
) -> mypy_boto3_s3.S3Client:
    """Prepare boto3 client."""
    return saritasa_s3_tools.client.get_boto3_s3_client(
        access_key_getter=access_key_getter,
        s3_endpoint_url_getter=s3_endpoint_url_getter,
        region=s3_region,
    )


@pytest.fixture
def s3_bucket(
    request: pytest.FixtureRequest,
) -> str:
    """Get the name of s3 bucket."""
    if bucket := request.config.inicfg.get("s3_bucket", ""):
        return str(bucket)
    raise NotImplementedError(  # pragma: no cover
        "Please set up `s3_bucket` fixture",
    )


@pytest.fixture
def s3_client(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_bucket: str,
) -> saritasa_s3_tools.S3Client:
    """Set up s3 client."""
    return saritasa_s3_tools.S3Client(
        boto3_client=boto3_client,
        default_bucket=s3_bucket,
    )


@pytest.fixture
def async_s3_client(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_bucket: str,
) -> saritasa_s3_tools.S3Client:
    """Set up async s3 client."""
    return saritasa_s3_tools.AsyncS3Client(
        boto3_client=boto3_client,
        default_bucket=s3_bucket,
    )
