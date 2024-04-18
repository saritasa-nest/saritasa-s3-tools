import pathlib
import xml.etree.ElementTree

import httpx

from .. import client


def upload_file(
    filepath: str,
    s3_params: client.S3UploadParams,
) -> httpx.Response:
    """Upload file to s3."""
    url = s3_params.url
    params = s3_params.params
    # Test file upload itself
    with (
        httpx.Client() as client,
        pathlib.Path(filepath).open("rb") as upload_file,
    ):
        upload_response = client.post(
            url=url,
            data={
                key: value
                for key, value in params.items()
                if value is not None
            },
            files={"file": upload_file.read()},
        )
    return upload_response


def upload_file_and_verify(
    filepath: str,
    s3_params: client.S3UploadParams,
) -> tuple[str, str]:
    """Upload and verify that file is uploaded."""
    upload_response = upload_file(
        filepath=filepath,
        s3_params=s3_params,
    )
    assert upload_response.is_success, upload_response.content  # noqa: S101
    parsed_response = xml.etree.ElementTree.fromstring(  # noqa: S314
        upload_response.content.decode(),
    )
    file_key = parsed_response[2].text
    file_url = parsed_response[0].text
    assert file_url, upload_response.content  # noqa: S101
    assert file_key, upload_response.content  # noqa: S101
    return file_url, file_key
