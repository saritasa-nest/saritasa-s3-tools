import collections.abc
import dataclasses
import warnings

import boto3
import botocore.client
import botocore.config
import botocore.credentials
import botocore.exceptions
import botocore.response
import mypy_boto3_s3
import mypy_boto3_s3.type_defs

from . import configs

AccessKeyGetter = collections.abc.Callable[
    [],
    botocore.credentials.Credentials,
]
S3EndpointUrlGetter = collections.abc.Callable[
    [],
    str | None,
]
RegionGetter = collections.abc.Callable[
    [],
    str,
]


def get_boto3_session(
    access_key_getter: AccessKeyGetter,
    region: RegionGetter | str = "",
) -> boto3.session.Session:
    """Get AWS session."""
    if callable(region):
        region = region()  # pragma: no cover
    credentials = access_key_getter()
    return boto3.session.Session(
        aws_session_token=credentials.token or None,
        aws_access_key_id=credentials.access_key or None,
        aws_secret_access_key=credentials.secret_key or None,
        region_name=region,
    )


def get_boto3_s3_client(
    session: boto3.session.Session | None = None,
    access_key_getter: AccessKeyGetter | None = None,
    region: RegionGetter | str = "",
    s3_endpoint_url_getter: S3EndpointUrlGetter | None = None,
    config: botocore.config.Config | None = None,
) -> mypy_boto3_s3.S3Client:
    """Prepare boto3's s3 client for usage."""
    if access_key_getter:
        session = get_boto3_session(
            access_key_getter=access_key_getter,
            region=region,
        )
    if not session:
        raise ValueError(
            "Please pass either session or access_key_getter",
        )  # pragma: no cover

    endpoint_url = None
    if s3_endpoint_url_getter:
        endpoint_url = s3_endpoint_url_getter()

    return session.client(
        service_name="s3",  # type: ignore
        endpoint_url=endpoint_url,
        config=config,
    )


def get_boto3_s3_resource(
    session: boto3.session.Session | None = None,
    access_key_getter: AccessKeyGetter | None = None,
    region: RegionGetter | str = "",
    s3_endpoint_url_getter: S3EndpointUrlGetter | None = None,
    config: botocore.config.Config | None = None,
) -> mypy_boto3_s3.S3ServiceResource:
    """Prepare boto3's s3 resource for usage."""
    if access_key_getter:
        session = get_boto3_session(  # pragma: no cover
            access_key_getter=access_key_getter,
            region=region,
        )
    if not session:
        raise ValueError(
            "Please pass either session or access_key_getter",
        )  # pragma: no cover

    endpoint_url = None
    if s3_endpoint_url_getter:
        endpoint_url = s3_endpoint_url_getter()

    return session.resource(
        service_name="s3",  # type: ignore
        endpoint_url=endpoint_url,
        config=config,
    )


@dataclasses.dataclass
class S3UploadParams:
    """Representation of s3 upload params."""

    url: str
    params: dict[str, str]


class S3Client:
    """Client for interacting with s3 based on boto3 client."""

    def __init__(
        self,
        boto3_client: mypy_boto3_s3.S3Client,
        default_bucket: str,
        default_download_expiration: int = 3600,
    ) -> None:
        self.boto3_client = boto3_client
        self.default_bucket = default_bucket
        self.default_download_expiration = default_download_expiration

    def _get_fields(
        self,
        config: configs.S3FileTypeConfig,
        content_type: str,
        meta_data: dict[str, str],
    ) -> dict[str, int | str]:
        """Prepare fields for s3 upload."""
        fields: dict[str, int | str] = {
            "success_action_status": config.success_action_status,
            "Content-Type": content_type,
        }
        fields.update(**meta_data)
        if config.content_disposition:
            fields["Content-Disposition"] = config.content_disposition
        return fields

    def _get_conditions(
        self,
        config: configs.S3FileTypeConfig,
        content_type: str,
        meta_data: dict[str, str],
    ) -> list[list[str | int] | dict[str, str | int]]:
        """Prepare conditions for s3 upload."""
        conditions: list[list[str | int] | dict[str, str | int]] = [
            {"success_action_status": str(config.success_action_status)},
            {"Content-Type": content_type},
        ]
        if config.content_length_range:
            conditions.append(
                [
                    "content-length-range",
                    *list(config.content_length_range),
                ],
            )
        if config.content_disposition:
            conditions.append(
                {"Content-Disposition": config.content_disposition},
            )
        for key, value in meta_data.items():
            conditions.append({key: value})
        return conditions

    def prepare_meta_data(
        self,
        config: configs.S3FileTypeConfig,
        extra_metadata: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Prepare metadata."""
        meta_data = {
            "x-amz-meta-config-name": config.name,
        }
        for key, value in (extra_metadata or {}).items():
            meta_data[f"x-amz-meta-{key}"] = value
        return meta_data

    def generate_params(
        self,
        filename: str,
        config: configs.S3FileTypeConfig,
        content_type: str,
        bucket: str = "",
        upload_folder: str = "",
        extra_metadata: dict[str, str] | None = None,
    ) -> S3UploadParams:
        """Generate params for s3 upload."""
        meta_data = self.prepare_meta_data(
            config=config,
            extra_metadata=extra_metadata,
        )
        for key in meta_data:
            if "_" in key:
                warnings.warn(
                    "Use `-` instead of `_` as separator for key. "
                    f"Example {key.replace('x-amz-meta-', '')} -> "
                    f"{key.replace('x-amz-meta-', '').replace('_', '-')}.",
                    stacklevel=2,
                )
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_post.html
        s3_params = self.boto3_client.generate_presigned_post(
            Bucket=bucket or self.default_bucket,
            Key="/".join(
                filter(None, (upload_folder, config.key(filename=filename))),
            ),
            Fields=self._get_fields(
                config=config,
                content_type=content_type,
                meta_data=meta_data,
            ),
            Conditions=self._get_conditions(
                config=config,
                content_type=content_type,
                meta_data=meta_data,
            ),
            ExpiresIn=config.expires_in,
        )
        return S3UploadParams(
            url=s3_params["url"],
            params=s3_params["fields"],
        )

    def upload_file(
        self,
        filename: str,
        config: configs.S3FileTypeConfig,
        file_obj: mypy_boto3_s3.type_defs.FileobjTypeDef,
        bucket: str = "",
    ) -> str:
        """Upload file to s3."""
        key = config.key(filename=filename)
        self.boto3_client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=bucket or self.default_bucket,
            Key=key,
        )
        return key

    def download_file(
        self,
        key: str,
        file_obj: mypy_boto3_s3.type_defs.FileobjTypeDef,
        bucket: str = "",
    ) -> mypy_boto3_s3.type_defs.FileobjTypeDef:
        """Download file from s3."""
        self.boto3_client.download_fileobj(
            Fileobj=file_obj,
            Bucket=bucket or self.default_bucket,
            Key=key,
        )
        return file_obj

    def generate_presigned_url(
        self,
        key: str,
        bucket: str = "",
        expiration: int = 0,
    ) -> str:
        """Generate url for viewing/downloading file."""
        return self.boto3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket or self.default_bucket,
                "Key": key,
            },
            ExpiresIn=expiration or self.default_download_expiration,
        )

    def get_file_metadata(
        self,
        key: str,
        bucket: str = "",
    ) -> mypy_boto3_s3.type_defs.HeadObjectOutputTypeDef:
        """Get file's metadata."""
        return self.boto3_client.head_object(
            Key=key,
            Bucket=bucket or self.default_bucket,
        )

    def is_file_in_bucket(
        self,
        key: str,
        bucket: str = "",
    ) -> bool:
        """Check if file is in bucket."""
        try:
            self.get_file_metadata(
                key=key,
                bucket=bucket,
            )
            return True
        except botocore.exceptions.ClientError as error:
            if error.response.get("Error", {}).get("Code") == "404":
                return False
            raise error  # pragma: no cover

    def copy_object(
        self,
        key: str,
        source_key: str,
        bucket: str = "",
        source_bucket: str = "",
    ) -> None:
        """Copy file object from copy source to key path."""
        self.boto3_client.copy_object(
            Bucket=bucket or self.default_bucket,
            CopySource=f"{source_bucket or self.default_bucket}/{source_key}",
            Key=key,
        )

    def delete_object(
        self,
        key: str,
        bucket: str = "",
    ) -> None:
        """Delete file object from s3 bucket."""
        self.boto3_client.delete_object(
            Bucket=bucket or self.default_bucket,
            Key=key,
        )
