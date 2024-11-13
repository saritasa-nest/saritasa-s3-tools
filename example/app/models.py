from django.contrib.auth.models import AbstractUser
from django.db import models

import saritasa_s3_tools.django


class User(AbstractUser):
    """User model."""


class ModelWithFiles(models.Model):
    """Test model with different files configs."""

    file = saritasa_s3_tools.django.S3FileField(
        blank=True,
        null=True,
        s3_config=saritasa_s3_tools.S3FileTypeConfig(  # pyright: ignore
            name="django-files",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFolder(
                "django-files",
            ),
            allowed=("text/plain",),
            auth=lambda user: bool(user and user.is_authenticated),
            content_length_range=(1000, 20000000),
        ),
    )

    all_file_types = saritasa_s3_tools.django.S3FileField(
        blank=True,
        null=True,
        s3_config=saritasa_s3_tools.S3FileTypeConfig(  # pyright: ignore
            name="django-all-file-types",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFolder(
                "django-all-file-types",
            ),
            content_length_range=(5000, 20000000),
        ),
    )

    all_file_sizes = saritasa_s3_tools.django.S3FileField(
        blank=True,
        null=True,
        s3_config=saritasa_s3_tools.S3FileTypeConfig(  # pyright: ignore
            name="django-all-file-sizes",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFolder(
                "django-all-file-sizes",
            ),
        ),
    )

    anon_files = saritasa_s3_tools.django.S3FileField(
        blank=True,
        null=True,
        s3_config=saritasa_s3_tools.S3FileTypeConfig(  # pyright: ignore
            name="django-anon-files",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFileName(
                "django-anon-files",
            ),
        ),
    )

    image = saritasa_s3_tools.django.S3ImageField(
        blank=True,
        null=True,
        s3_config=saritasa_s3_tools.S3FileTypeConfig(  # pyright: ignore
            name="django-images",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFolder(
                "django-images",
            ),
            allowed=("image/png",),
            content_length_range=(5000, 20000000),
        ),
    )

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.pk}"
