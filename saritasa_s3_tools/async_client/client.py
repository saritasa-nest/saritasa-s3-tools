import collections.abc
import functools
import typing

import anyio

import mypy_boto3_s3.type_defs

from .. import client, configs

ReturnT = typing.TypeVar("ReturnT")
ParamT = typing.ParamSpec("ParamT")


class AsyncS3Client(client.S3Client):
    """Async Client for interacting with s3 based on boto3 client."""

    async def run_sync_as_async(
        self,
        func: collections.abc.Callable[ParamT, ReturnT],
        *args: ParamT.args,
        **kwargs: ParamT.kwargs,
    ) -> ReturnT:
        """Make sync function run in async env."""
        return await anyio.to_thread.run_sync(  # type: ignore
            functools.partial(func, *args, **kwargs),
        )

    async def async_generate_params(
        self,
        filename: str,
        config: configs.S3FileTypeConfig,
        content_type: str,
        bucket: str = "",
        upload_folder: str = "",
        extra_metadata: dict[str, str] | None = None,
    ) -> client.S3UploadParams:
        """Generate params for s3 upload in async env."""
        return await self.run_sync_as_async(
            self.generate_params,
            filename=filename,
            upload_folder=upload_folder,
            config=config,
            bucket=bucket,
            content_type=content_type,
            extra_metadata=extra_metadata,
        )

    async def async_upload_file(
        self,
        filename: str,
        config: configs.S3FileTypeConfig,
        file_obj: mypy_boto3_s3.type_defs.FileobjTypeDef,
        bucket: str = "",
    ) -> str:
        """Upload file to s3 in async env."""
        return await self.run_sync_as_async(
            self.upload_file,
            filename=filename,
            config=config,
            bucket=bucket,
            file_obj=file_obj,
        )

    async def async_download_file(
        self,
        key: str,
        file_obj: mypy_boto3_s3.type_defs.FileobjTypeDef,
        bucket: str = "",
    ) -> mypy_boto3_s3.type_defs.FileobjTypeDef:
        """Download file from s3 in async env."""
        return await self.run_sync_as_async(
            self.download_file,
            file_obj=file_obj,
            bucket=bucket,
            key=key,
        )

    async def async_get_file_metadata(
        self,
        key: str,
        bucket: str = "",
    ) -> mypy_boto3_s3.type_defs.HeadObjectOutputTypeDef:
        """Get file's metadata in async env."""
        return await self.run_sync_as_async(
            self.get_file_metadata,
            bucket=bucket,
            key=key,
        )

    async def async_is_file_in_bucket(
        self,
        key: str,
        bucket: str = "",
    ) -> bool:
        """Check if file is in bucket in async env."""
        return await self.run_sync_as_async(
            self.is_file_in_bucket,
            bucket=bucket,
            key=key,
        )

    async def async_copy_object(
        self,
        key: str,
        source_key: str,
        bucket: str = "",
        source_bucket: str = "",
    ) -> None:
        """Copy file object from copy source to key path in async env."""
        return await self.run_sync_as_async(
            self.copy_object,
            key=key,
            source_key=source_key,
            bucket=bucket,
            source_bucket=source_bucket,
        )

    async def async_delete_object(
        self,
        key: str,
        bucket: str = "",
    ) -> None:
        """Delete file object from s3 bucket is async env."""
        return await self.run_sync_as_async(
            self.delete_object,
            key=key,
            bucket=bucket,
        )
