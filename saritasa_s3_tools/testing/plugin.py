import collections.abc
import contextlib
import typing

import pytest

import boto3
import botocore.config
import botocore.credentials
import botocore.exceptions
import mypy_boto3_s3
import mypy_boto3_s3.type_defs

import saritasa_s3_tools


def pytest_addoption(parser: pytest.Parser) -> None:
    """Set up cmd args."""
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
        "s3_bucket_name",
        "Bucket for s3.",
        default="saritasa-s3-tools",
    )


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def s3_region(
    request: pytest.FixtureRequest,
) -> str:
    """Get s3 region."""
    return str(request.config.inicfg.get("s3_region", ""))


@pytest.fixture(scope="session")
def aws_session(
    access_key_getter: collections.abc.Callable[
        [],
        botocore.credentials.Credentials,
    ],
    s3_region: str,
) -> boto3.session.Session:
    """Get aws session."""
    return saritasa_s3_tools.client.get_boto3_session(
        access_key_getter=access_key_getter,
        region=s3_region,
    )


@pytest.fixture(scope="session")
def aws_config() -> botocore.config.Config | None:
    """Get aws config."""
    return None


@pytest.fixture(scope="session")
def boto3_resource(
    request: pytest.FixtureRequest,
) -> mypy_boto3_s3.S3ServiceResource:
    """Prepare boto3 resource."""
    try:
        return request.getfixturevalue("boto3_resource_from_django")
    except ImportError:  # pragma: no cover
        return request.getfixturevalue("boto3_resource_from_config")


@pytest.fixture(scope="session")
def boto3_resource_from_django() -> mypy_boto3_s3.S3ServiceResource:
    """Get boto3 resource for django storage."""
    from django.core.files.storage import default_storage

    return default_storage.connection  # type: ignore


@pytest.fixture(scope="session")
def boto3_resource_from_config(
    aws_session: boto3.session.Session,
    aws_config: botocore.config.Config,
    s3_endpoint_url_getter: collections.abc.Callable[
        [],
        str | None,
    ]
    | None,
) -> mypy_boto3_s3.S3ServiceResource:
    """Prepare boto3 resource."""
    return saritasa_s3_tools.client.get_boto3_s3_resource(
        session=aws_session,
        s3_endpoint_url_getter=s3_endpoint_url_getter,
        config=aws_config,
    )


@pytest.fixture(scope="session")
def boto3_client(
    boto3_resource: mypy_boto3_s3.S3ServiceResource,
) -> mypy_boto3_s3.S3Client:
    """Prepare boto3 client."""
    return boto3_resource.meta.client


@pytest.fixture(scope="session")
def s3_bucket_name(
    request: pytest.FixtureRequest,
) -> str:
    """Get the name of s3 bucket."""
    worker_input = getattr(
        request.config,
        "workerinput",
        {
            "workerid": "",
        },
    )
    return "-".join(
        filter(
            None,
            (
                str(
                    request.config.inicfg.get(
                        "s3_bucket_name",
                        "saritasa-s3-tools",
                    ),
                ),
                worker_input["workerid"],
            ),
        ),
    )


@pytest.fixture(scope="session")
def s3_bucket_cleaner(
    boto3_resource: mypy_boto3_s3.ServiceResource,
) -> collections.abc.Callable[[str], None]:
    """Get bucket cleaner."""

    def _clean(bucket: str) -> None:
        boto3_resource.Bucket(bucket).objects.all().delete()

    return _clean


@pytest.fixture(scope="session")
def s3_bucket_factory(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_region: str,
    s3_bucket_cleaner: collections.abc.Callable[[str], None],
) -> collections.abc.Callable[
    [str],
    contextlib._GeneratorContextManager[
        mypy_boto3_s3.type_defs.CreateBucketOutputTypeDef
    ],
]:
    """Get factory for generating s3 buckets."""

    @contextlib.contextmanager
    def _create(
        bucket: str,
    ) -> collections.abc.Generator[
        mypy_boto3_s3.type_defs.CreateBucketOutputTypeDef,
        None,
        None,
    ]:
        with contextlib.suppress(botocore.exceptions.ClientError):
            boto3_client.head_bucket(Bucket=bucket)
            s3_bucket_cleaner(bucket)  # pragma: no cover
            boto3_client.delete_bucket(Bucket=bucket)  # pragma: no cover
        yield boto3_client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={
                "LocationConstraint": s3_region,  # type: ignore
            },
        )
        s3_bucket_cleaner(bucket)
        boto3_client.delete_bucket(Bucket=bucket)

    return _create


@pytest.fixture(scope="session")
def s3_bucket(
    s3_bucket_factory: collections.abc.Callable[
        [str],
        contextlib._GeneratorContextManager[
            mypy_boto3_s3.type_defs.CreateBucketOutputTypeDef
        ],
    ],
    s3_bucket_name: str,
) -> collections.abc.Generator[
    str,
    None,
    None,
]:
    """Create s3 bucket."""
    with s3_bucket_factory(s3_bucket_name) as _:
        yield s3_bucket_name


@pytest.fixture(scope="session")
def s3_client(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_bucket: str,
) -> saritasa_s3_tools.S3Client:
    """Set up s3 client."""
    return saritasa_s3_tools.S3Client(
        boto3_client=boto3_client,
        default_bucket=s3_bucket,
    )


@pytest.fixture(scope="session")
def async_s3_client(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_bucket: str,
) -> saritasa_s3_tools.AsyncS3Client:
    """Set up async s3 client."""
    return saritasa_s3_tools.AsyncS3Client(
        boto3_client=boto3_client,
        default_bucket=s3_bucket,
    )


@pytest.fixture
def django_storage_changer() -> (
    collections.abc.Iterator[
        collections.abc.Callable[
            [str, typing.Any],
            None,
        ]
    ]
):
    """Temporary change default storage settings."""
    from django.core.files.storage import default_storage

    old_settings: dict[str, typing.Any] = {}

    def _changer(key: str, value: typing.Any) -> None:
        if key not in old_settings and hasattr(default_storage, key):
            old_settings[key] = getattr(default_storage, key)
        setattr(default_storage, key, value)

    yield _changer
    for key, value in old_settings.items():
        setattr(default_storage, key, value)


@pytest.fixture(scope="session")
def django_adjust_s3_bucket(s3_bucket: str) -> None:
    """Set bucket to a test one."""
    from django.conf import settings
    from django.core.files.storage import default_storage

    default_storage.bucket_name = s3_bucket  # type: ignore
    settings.AWS_STORAGE_BUCKET_NAME = s3_bucket
    return None
