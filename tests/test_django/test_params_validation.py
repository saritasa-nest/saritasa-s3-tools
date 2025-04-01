import humanize
import pytest
import pytest_lazy_fixtures
from rest_framework import status, test
from rest_framework.response import Response

from example.app import models


@pytest.mark.parametrize(
    argnames="user",
    argvalues=[
        None,
        pytest_lazy_fixtures.lf("default_user"),
    ],
)
def test_auth_validation(
    api_client: test.APIClient,
    user: models.User,
    s3_get_params_url: str,
) -> None:
    """Test that anon user won't be able to get params."""
    api_client.force_authenticate(user=user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-files",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": 5000,
        },
    )  # type: ignore
    if user is None:
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            response.data
        )
        assert (
            response.data["config"][0]  # type: ignore
            == "Current user can't use this destination"
        ), response.data
        return
    assert response.status_code == status.HTTP_200_OK, response.data


@pytest.mark.parametrize(
    argnames="user",
    argvalues=[
        None,
        pytest_lazy_fixtures.lf("default_user"),
    ],
)
def test_anon_auth_validation(
    api_client: test.APIClient,
    user: models.User,
    s3_get_params_url: str,
) -> None:
    """Test that if no auth config was set, anyone could upload file."""
    api_client.force_authenticate(user=user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-anon-files",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_200_OK, response.data


@pytest.mark.parametrize(
    argnames="content_length",
    argvalues=[
        500,
        30000000,
    ],
)
def test_content_length_validation_lower(
    api_client: test.APIClient,
    default_user: models.User,
    s3_get_params_url: str,
    content_length: int,
) -> None:
    """Test that user needs to set correct content_length."""
    api_client.force_authenticate(user=default_user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-files",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": content_length,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert response.data["content_length"][0] == (  # type: ignore
        f"Invalid file size - {humanize.naturalsize(content_length)} of "
        "test.txt. Need between 1.0 kB and 20.0 MB."
    ), response.data
    return


def test_content_type_validation(
    api_client: test.APIClient,
    default_user: models.User,
    s3_get_params_url: str,
) -> None:
    """Test that user needs to set correct content_type."""
    api_client.force_authenticate(user=default_user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-files",
            "filename": "test.txt",
            "content_type": "test/pytest",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
    assert response.data["content_type"][0] == (  # type: ignore
        "Invalid file type - `test/pytest` of `test.txt`. "
        "Expected: text/plain."
    ), response.data
    return


@pytest.mark.parametrize(
    argnames="user",
    argvalues=[
        None,
        pytest_lazy_fixtures.lf("default_user"),
    ],
)
def test_all_files_allowed_validation(
    api_client: test.APIClient,
    user: models.User,
    s3_get_params_url: str,
) -> None:
    """Test that all files can be allowed."""
    api_client.force_authenticate(user=user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-all-file-types",
            "filename": "test.txt",
            "content_type": "test/test",
            "content_length": 5000,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_200_OK, response.data


@pytest.mark.parametrize(
    argnames="user",
    argvalues=[
        None,
        pytest_lazy_fixtures.lf("default_user"),
    ],
)
def test_all_file_sizes_allowed_validation(
    api_client: test.APIClient,
    user: models.User,
    s3_get_params_url: str,
) -> None:
    """Test that all files sizes can be allowed."""
    api_client.force_authenticate(user=user)
    response: Response = api_client.post(
        path=s3_get_params_url,
        data={
            "config": "django-all-file-sizes",
            "filename": "test.txt",
            "content_type": "text/plain",
            "content_length": 5000 * 10**10,
        },
    )  # type: ignore
    assert response.status_code == status.HTTP_200_OK, response.data
