import uuid

import factory

from . import models

DEFAULT_PASSWORD = "Test111!"  # noqa: S105


class UserFactory(factory.django.DjangoModelFactory[models.User]):
    """Factory to generate test User instance."""

    email = factory.declarations.LazyAttribute(
        lambda obj: f"{uuid.uuid4()}@saritasa-s3-tools.com",
    )
    username = factory.faker.Faker("user_name")
    first_name = factory.faker.Faker("first_name")
    last_name = factory.faker.Faker("last_name")
    password = factory.django.Password(password=DEFAULT_PASSWORD)

    class Meta:
        model = models.User


class ModelWithFilesFactory(
    factory.django.DjangoModelFactory[models.ModelWithFiles],
):
    """Factory to generate test ModelWithFiles instance."""

    file = factory.django.FileField(
        filename="file.txt",
        data="Test",
    )
    all_file_types = factory.django.FileField(
        filename="file.txt",
        data="Test",
    )
    all_file_sizes = factory.django.FileField(
        filename="file.txt",
        data="Test",
    )
    anon_files = factory.django.FileField(
        filename="file.txt",
        data="Test",
    )
    image = factory.django.ImageField(
        color="magenta",
    )

    class Meta:
        model = models.ModelWithFiles


class ModelWithFilesInvalidTypesFactory(ModelWithFilesFactory):
    """Factory to generate test ModelWithFiles instance with invalid types."""

    image = factory.django.FileField(
        filename="file.txt",
        data="Test",
    )
