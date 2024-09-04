from django.core import exceptions
from django.core.files import utils
from django.db import models

from .. import configs


class S3FileFieldMixin:
    """Mixin which adds support for s3 configuration.

    This mixin will upload to proper path by using key generator from config.

    """

    def __init__(
        self,
        # This arg is none because Django tries to init field with no args.
        s3_config: configs.S3FileTypeConfig | None = None,
        verbose_name: str | None = None,
        **kwargs,
    ) -> None:
        self.s3_config = s3_config
        super().__init__(
            verbose_name=verbose_name,  # type: ignore
            **kwargs,
        )

    def generate_filename(
        self,
        instance: models.Model,
        filename: str,
    ) -> str:
        """Generate filename via config."""
        if not self.s3_config:
            raise exceptions.ImproperlyConfigured(  # pragma: no cover
                "Please set s3_config for field",
            )
        filename = self.s3_config.key(filename=filename)
        filename = utils.validate_file_name(  # type: ignore
            filename,
            allow_relative_path=True,
        )
        return self.storage.generate_filename(filename)  # type: ignore


class S3FileField(S3FileFieldMixin, models.FileField):
    """FileField with S3 capabilities."""


class S3ImageField(S3FileFieldMixin, models.ImageField):
    """FileField with S3 capabilities."""
