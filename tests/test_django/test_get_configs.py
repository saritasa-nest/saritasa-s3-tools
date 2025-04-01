from django.urls import reverse_lazy
from rest_framework import status, test
from rest_framework.response import Response

import saritasa_s3_tools
from example.app import models


def test_list_configs(
    api_client: test.APIClient,
    default_user: models.User,
):
    """Test that we can list config."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.get(
        path=reverse_lazy("s3-list-configs"),
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    assert len(response.data) == len(
        saritasa_s3_tools.configs.S3FileTypeConfig.configs.keys(),
    )


def test_retrieve_config(
    api_client: test.APIClient,
    default_user: models.User,
):
    """Test that we can retrieve config."""
    api_client.force_authenticate(default_user)
    expected_name = next(
        iter(saritasa_s3_tools.configs.S3FileTypeConfig.configs.keys()),
    )
    response: Response = api_client.get(
        path=reverse_lazy(
            "s3-retrieve-config",
            kwargs={
                "name": expected_name,
            },
        ),
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["name"] == expected_name, response.data


def test_retrieve_unknown_config(
    api_client: test.APIClient,
    default_user: models.User,
):
    """Test that unknown config is handled properly."""
    api_client.force_authenticate(default_user)
    response: Response = api_client.get(
        path=reverse_lazy(
            "s3-retrieve-config",
            kwargs={
                "name": "unknown-config",
            },
        ),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.data
