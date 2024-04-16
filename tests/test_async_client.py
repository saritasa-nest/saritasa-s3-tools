import io
import pathlib

import pytest

import saritasa_s3_tools


@pytest.mark.usefixtures("anyio_backend")
async def test_upload(
    async_s3_client: saritasa_s3_tools.AsyncS3Client,
) -> None:
    """Test file upload in async env."""
    s3_params = await async_s3_client.async_generate_params(
        filename=pathlib.Path(__file__).name,
        config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
        content_type="application/x-python-code",
        extra_metadata={
            "test": "123",
        },
    )
    _, file_key = saritasa_s3_tools.testing.upload_file_and_verify(
        filepath=__file__,
        s3_params=s3_params,
    )
    meta_data = await async_s3_client.async_get_file_metadata(
        key=file_key,
    )
    assert meta_data["Metadata"]["config-name"] == "files"
    assert meta_data["Metadata"]["test"] == "123"
    file_data = await async_s3_client.async_download_file(
        key=file_key,
        file_obj=io.BytesIO(),
    )
    file_data.seek(0)
    with pathlib.Path(__file__).open("rb") as upload_file:
        assert file_data.read() == upload_file.read()


@pytest.mark.usefixtures("anyio_backend")
async def test_direct_upload(
    async_s3_client: saritasa_s3_tools.AsyncS3Client,
) -> None:
    """Test direct file upload in async env."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = await async_s3_client.async_upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    assert await async_s3_client.async_is_file_in_bucket(
        key=upload_key,
    ), upload_key


@pytest.mark.usefixtures("anyio_backend")
async def test_delete(
    async_s3_client: saritasa_s3_tools.AsyncS3Client,
) -> None:
    """Test file deletion."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = await async_s3_client.async_upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    await async_s3_client.async_delete_object(key=upload_key)
    assert not await async_s3_client.async_is_file_in_bucket(
        key=upload_key,
    ), upload_key


@pytest.mark.usefixtures("anyio_backend")
async def test_copy(
    async_s3_client: saritasa_s3_tools.AsyncS3Client,
) -> None:
    """Test file copy."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = await async_s3_client.async_upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    copy_key = saritasa_s3_tools.keys.S3KeyWithPrefix("copy")(None)
    await async_s3_client.async_copy_object(
        key=copy_key,
        source_key=upload_key,
    )
    assert await async_s3_client.async_is_file_in_bucket(
        key=copy_key,
    ), copy_key
