import http

import httpx
from rest_framework import status, test
from rest_framework.response import Response

import saritasa_s3_tools.django
from example.app import models


def test_s3_upload_field_with_str_value(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
):
    """Check that S3UploadURLField can represent just str value."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-files",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_200_OK, response.data
    file_url, file_key = saritasa_s3_tools.testing.upload_file_and_verify(
        filepath=__file__,
        s3_params=saritasa_s3_tools.client.S3UploadParams(**response.data),
        is_minio=True,
    )
    signed_file_url = (
        saritasa_s3_tools.django.S3UploadURLField().to_representation(
            value=file_key,
        )
    )
    assert signed_file_url
    with httpx.Client() as client:
        response = client.get(url=signed_file_url)
        assert response.status_code == http.HTTPStatus.OK
