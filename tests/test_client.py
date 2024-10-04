import io
import pathlib
import re
import time
import xml.etree.ElementTree

import httpx
import pytest

import saritasa_s3_tools


def test_upload(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test file upload."""
    s3_params = s3_client.generate_params(
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
    meta_data = s3_client.get_file_metadata(key=file_key)
    assert meta_data["Metadata"]["config-name"] == "files"
    assert meta_data["Metadata"]["test"] == "123"
    file_data = s3_client.download_file(
        key=file_key,
        file_obj=io.BytesIO(),
    )
    file_data.seek(0)
    with pathlib.Path(__file__).open("rb") as upload_file:
        assert file_data.read() == upload_file.read()


def test_direct_upload(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test direct file upload."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = s3_client.upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    assert s3_client.is_file_in_bucket(key=upload_key), upload_key


def test_delete(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test file deletion."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = s3_client.upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    s3_client.delete_object(key=upload_key)
    assert not s3_client.is_file_in_bucket(key=upload_key), upload_key


def test_copy(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test file copy."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = s3_client.upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    copy_key = saritasa_s3_tools.keys.WithPrefixUUIDFileName("copy")(None)
    s3_client.copy_object(
        key=copy_key,
        source_key=upload_key,
    )
    assert s3_client.is_file_in_bucket(key=copy_key), copy_key


def test_presigned_url(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test file generation of presigned url."""
    with pathlib.Path(__file__).open("rb") as upload_file:
        upload_key = s3_client.upload_file(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
            file_obj=upload_file,
        )
    presigned_url = s3_client.generate_presigned_url(key=upload_key)
    with httpx.Client() as client:
        response = client.get(presigned_url)
    assert response.is_success, response.content


def test_upload_expiration(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test file upload expiration."""
    s3_params = s3_client.generate_params(
        filename=pathlib.Path(__file__).name,
        config=saritasa_s3_tools.S3FileTypeConfig.configs["expires"],
        content_type="application/x-python-code",
    )

    time.sleep(
        saritasa_s3_tools.S3FileTypeConfig.configs["expires"].expires_in + 0.1,
    )
    response = saritasa_s3_tools.testing.upload_file(
        filepath=__file__,
        s3_params=s3_params,
    )
    assert not response.is_success, response.content
    error = xml.etree.ElementTree.fromstring(  # noqa: S314
        response.content.decode(),
    )[1].text
    assert (
        error == "Invalid according to Policy: Policy expired."
    ), response.content


def test_meta_data_key_warning(s3_client: saritasa_s3_tools.S3Client) -> None:
    """Test warning about meta data keys."""
    with pytest.warns(
        UserWarning,
        match=re.escape(
            "Use `-` instead of `_` as separator for key. "
            "Example user_id -> user-id.",
        ),
    ):
        s3_client.generate_params(
            filename=pathlib.Path(__file__).name,
            config=saritasa_s3_tools.S3FileTypeConfig.configs["expires"],
            content_type="application/x-python-code",
            extra_metadata={
                "user_id": "1",
            },
        )
