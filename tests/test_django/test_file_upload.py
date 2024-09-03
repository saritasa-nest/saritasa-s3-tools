from django.conf import settings
from django.test import override_settings
from django.urls import reverse_lazy
from rest_framework import status, test
from rest_framework.response import Response

import saritasa_s3_tools
from example.app import factories, models


def test_file_upload(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_api_url: str,
) -> None:
    """Test whole file upload workflow."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=s3_api_url,
        data={
            "config": "django-files",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_200_OK, response.data
    file_url, _ = saritasa_s3_tools.testing.upload_file_and_verify(
        filepath=__file__,
        s3_params=saritasa_s3_tools.client.S3UploadParams(**response.data),
    )
    response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": file_url,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_201_CREATED, response.data


@override_settings(AWS_LOCATION="tests")
def test_file_validation_with_location_setting(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_api_url: str,
) -> None:
    """Test what file url is validated when location setting is enabled."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": factories.ModelWithFilesFactory().file.url,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_201_CREATED, response.data


@override_settings(AWS_QUERYSTRING_AUTH=False)
def test_file_validation_with_no_query_params(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_api_url: str,
) -> None:
    """Test what file url is validated when url passed with no query auth."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": factories.ModelWithFilesFactory().file.url,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_201_CREATED, response.data


@override_settings(AWS_QUERYSTRING_AUTH=False)
def test_file_validation_not_found(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_api_url: str,
) -> None:
    """Test what non-existent file url won't be allowed."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": settings.AWS_S3_ENDPOINT_URL + "/cool-picture.png",
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert response.data["file"][0] == "File does not exist."


def test_file_validation_non_s3_file(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_api_url: str,
) -> None:
    """Test what non-existent file url won't be allowed."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": "https://www.google.com/cool-picture.png",
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert response.data["file"][0] == "File does not exist."
