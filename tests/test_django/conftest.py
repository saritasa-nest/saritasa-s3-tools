import pytest
import pytest_django
from django.urls import reverse_lazy
from rest_framework import test

from example.app import factories, models


@pytest.fixture(scope="session", autouse=True)
def django_db_setup(django_db_setup) -> None:  # noqa: PT004, ANN001
    """Set up test db for testing."""


@pytest.fixture(autouse=True)
def _enable_db_access_for_all_tests(django_db_setup, db) -> None:  # noqa: ANN001
    """Enable access to DB for all tests."""


@pytest.fixture(scope="session", autouse=True)
def _adjust_s3_bucket(django_adjust_s3_bucket: None) -> None:
    """Set bucket to a test one."""


@pytest.fixture
def s3_api_url() -> str:
    """Create api client."""
    return reverse_lazy("s3-get-params")


@pytest.fixture
def api_client() -> test.APIClient:
    """Create api client."""
    return test.APIClient()


@pytest.fixture(scope="module")
def default_user(
    django_db_blocker: pytest_django.DjangoDbBlocker,
) -> models.User:
    """Create user."""
    with django_db_blocker.unblock():
        return factories.UserFactory()  # type: ignore
