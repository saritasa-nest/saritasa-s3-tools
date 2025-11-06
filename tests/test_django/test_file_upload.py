import collections.abc
import typing

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse_lazy
from rest_framework import status, test
from rest_framework.response import Response

import saritasa_s3_tools
from example.app import factories, models


@pytest.mark.parametrize(
    argnames="value",
    argvalues=[
        "url",
        "key",
        "key_from_params",
    ],
)
def test_file_upload(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
    value: str,
) -> None:
    """Test whole file upload workflow."""
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
    value_to_send: str
    match value:
        case "key":
            value_to_send = file_key
        case "url":
            value_to_send = file_url
        case "key_from_params":
            value_to_send = response.data["params"]["key"]
    response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": value_to_send,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert file_key in response.data["file"], response.data


def test_file_upload_invalid_config_used(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
) -> None:
    """Test file upload when invalid config for model is used."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-all-file-types",
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
    response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": response.data["params"]["key"],
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert (
        response.data["file"][0]
        == "File's path doesn't match with config's pattern."
    ), response.data


def test_file_upload_unknown_config_used(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
) -> None:
    """Test file upload when unknown config is used."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "not-found",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert (
        response.data["config"][0] == '"not-found" is not a valid choice.'
    ), response.data


@override_settings(AWS_LOCATION="tests")
def test_file_validation_with_location_setting(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
    django_storage_changer: collections.abc.Callable[[str, typing.Any], None],
) -> None:
    """Test what file url is validated when location setting is enabled."""
    django_storage_changer("location", "tests")
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": factories.ModelWithFilesFactory.create().file.url,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_201_CREATED, response.data


def test_file_validation_with_no_query_params(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
    django_storage_changer: collections.abc.Callable[[str, typing.Any], None],
) -> None:
    """Test what file url is validated when url passed with no query auth."""
    django_storage_changer("querystring_auth", False)
    api_client.force_authenticate(default_user)
    factories.ModelWithFilesFactory.create().full_clean()
    response: Response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": factories.ModelWithFilesFactory.create().file.url,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_201_CREATED, response.data


def test_file_validation_not_found(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
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
    s3_get_params_url: str,
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


def test_file_upload_with_wrong_file_name(
    api_client: test.APIClient,
    default_user: models.User | None,
    s3_get_params_url: str,
) -> None:
    """Test filename contains escape characters.

    In that case package raises validation error.

    """
    api_client.force_authenticate(default_user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-files",
            "filename": "te+st.txt",
            "content_type": "text/plain",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_200_OK, response.data
    file_url, _ = saritasa_s3_tools.testing.upload_file_and_verify(
        filepath=__file__,
        s3_params=saritasa_s3_tools.client.S3UploadParams(**response.data),
        is_minio=True,
    )
    response = api_client.post(
        path=reverse_lazy("model-api-list"),
        data={
            "file": file_url,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert response.data["file"][0] == "Not a valid string."
