import collections.abc
import contextlib

import pytest

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
    boto3_client: mypy_boto3_s3.S3Client,
) -> collections.abc.Callable[[str], None]:
    """Get bucket cleaner."""

    def _clean(bucket: str) -> None:
        while True:
            s3_objects: list[
                mypy_boto3_s3.type_defs.ObjectIdentifierTypeDef
            ] = [
                {"Key": s3_object.get("Key", "")}
                for s3_object in boto3_client.list_objects_v2(
                    Bucket=bucket,
                    MaxKeys=1000,
                ).get(
                    "Contents",
                    [],
                )
                if s3_object.get("Key", "")
            ]
            if not s3_objects:
                return
            boto3_client.delete_objects(
                Bucket=bucket,
                Delete={
                    "Objects": s3_objects,
                },
            )

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
            s3_bucket_cleaner(bucket)
            boto3_client.delete_bucket(Bucket=bucket)
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
    mypy_boto3_s3.type_defs.CreateBucketOutputTypeDef,
    None,
    None,
]:
    """Create s3 bucket."""
    with s3_bucket_factory(s3_bucket_name) as bucket:
        yield bucket


@pytest.fixture(scope="session")
def s3_client(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_bucket_name: str,
    s3_bucket: mypy_boto3_s3.type_defs.CreateBucketOutputTypeDef,
) -> saritasa_s3_tools.S3Client:
    """Set up s3 client."""
    return saritasa_s3_tools.S3Client(
        boto3_client=boto3_client,
        default_bucket=s3_bucket_name,
    )


@pytest.fixture(scope="session")
def async_s3_client(
    boto3_client: mypy_boto3_s3.S3Client,
    s3_bucket_name: str,
    s3_bucket: mypy_boto3_s3.type_defs.CreateBucketOutputTypeDef,
) -> saritasa_s3_tools.S3Client:
    """Set up async s3 client."""
    return saritasa_s3_tools.AsyncS3Client(
        boto3_client=boto3_client,
        default_bucket=s3_bucket_name,
    )
