import collections.abc
import io
import random

import factory
import PIL.Image
import PIL.ImageColor

import mypy_boto3_s3

from . import client, configs

BucketGetter = collections.abc.Callable[
    [],
    str,
]


class S3FileField(factory.LazyAttribute):
    """Generate file and upload to s3."""

    _boto3_client: mypy_boto3_s3.S3Client | None = None

    def __init__(
        self,
        s3_config: str,
        s3_region: client.RegionGetter | str,
        bucket: BucketGetter | str,
        access_key_getter: client.AccessKeyGetter,
        s3_endpoint_url_getter: client.S3EndpointUrlGetter | None = None,
        filename: str = "example.txt",
        data: bytes = b"Test",
    ) -> None:
        self.access_key_getter = access_key_getter
        self.s3_endpoint_url_getter = s3_endpoint_url_getter
        self.bucket = bucket
        self.s3_region = s3_region
        self.filename = filename
        self.s3_config = s3_config
        self.data = data

        super().__init__(
            function=self._generate,
        )

    def _get_boto3(self) -> mypy_boto3_s3.S3Client:
        if not self._boto3_client:
            self._boto3_client = client.get_boto3_s3_client(
                region=self.s3_region,
                s3_endpoint_url_getter=self.s3_endpoint_url_getter,
                access_key_getter=self.access_key_getter,
            )
        return self._boto3_client

    def _get_s3_client(self) -> client.S3Client:
        """Set up s3 client."""
        if isinstance(self.bucket, str):
            bucket = self.bucket
        if callable(self.bucket):
            bucket = self.bucket()
        return client.S3Client(
            boto3_client=self._get_boto3(),
            default_bucket=bucket,
        )

    def _generate_file_data(self) -> bytes:
        """Generate data for file."""
        return self.data

    def _generate(
        self,
        *args,  # noqa: ANN002
        **kwargs,
    ) -> str:
        """Generate file and upload it to s3."""
        return self._get_s3_client().upload_file(
            filename=self.filename,
            file_obj=io.BytesIO(self._generate_file_data()),
            config=configs.S3FileTypeConfig.configs[self.s3_config],
        )


class S3ImageFileField(S3FileField):
    """Generate image file and upload to s3."""

    def __init__(
        self,
        s3_config: str,
        s3_region: str,
        bucket: str,
        access_key_getter: client.AccessKeyGetter,
        s3_endpoint_url_getter: client.S3EndpointUrlGetter | None = None,
        filename: str = "example.jpg",
        data: bytes = b"",
        color: str = "",
        width: int = 0,
        height: int = 0,
    ) -> None:
        self.color = color
        self.width = width
        self.height = height
        super().__init__(
            s3_config=s3_config,
            s3_region=s3_region,
            bucket=bucket,
            access_key_getter=access_key_getter,
            s3_endpoint_url_getter=s3_endpoint_url_getter,
            data=data,
            filename=filename,
        )

    def _generate_file_data(self) -> bytes:
        """Generate image data for file."""
        width = self.width or self.height or 100
        height = self.height or self.width or 100
        color = self.color or random.choice(  # noqa: S311
            list(PIL.ImageColor.colormap.keys()),
        )

        thumb_io = io.BytesIO()
        with PIL.Image.new("RGB", (width, height), color) as thumb:
            thumb.save(thumb_io, format="JPEG")
        return thumb_io.getvalue()
