import collections.abc

from django.core import exceptions
from django.core.files import utils
from django.db import models
from django.db.models.fields import files
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

import botocore.exceptions

from .. import configs


class S3FileFieldMixin:
    """Mixin which adds support for s3 configuration.

    This mixin will upload to proper path by using key generator from config.

    """

    def __init__(
        self,
        # This arg is none because Django tries to init field with no args.
        s3_config: configs.S3FileTypeConfig | None = None,
        validate_key_pattern: bool = True,
        verbose_name: str | None = None,
        **kwargs,
    ) -> None:
        self.s3_config = s3_config
        self.validate_key_pattern = validate_key_pattern
        super().__init__(
            verbose_name=verbose_name,  # type: ignore
            **kwargs,
        )

    @cached_property
    def validators(
        self,
    ) -> collections.abc.Sequence[
        collections.abc.Callable[[files.FieldFile | str], None],
    ]:
        """Get validators."""
        validators = super().validators  # type: ignore
        validators.append(self._validate_file_existence)
        if self.validate_key_pattern:
            validators.append(self._validate_key)
        return validators

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

    def _validate_file_existence(
        self,
        value: files.FieldFile | str,
    ) -> None:
        """Check key is present in bucket."""
        is_field_file = isinstance(value, files.FieldFile)
        file_obj = getattr(value, "_file", None)
        if is_field_file and file_obj:
            # Skip if value has reference to actual file
            return  # pragma: no cover

        try:
            if not self.storage.exists(str(value)):  # type: ignore
                raise exceptions.ValidationError(
                    _("File does not exist."),
                )
        # If url comes not from s3, then botocore on key validation will
        # raise ParamValidationError
        except botocore.exceptions.ParamValidationError as error:
            raise exceptions.ValidationError(
                error,
            ) from error  # pragma: no cover
        except exceptions.SuspiciousFileOperation as error:
            raise exceptions.ValidationError(
                error,
            ) from error  # pragma: no cover

    def _validate_key(
        self,
        value: files.FieldFile | str,
    ) -> None:
        """Check that key valid for s3 config."""
        is_field_file = isinstance(value, files.FieldFile)
        file_obj = getattr(value, "_file", None)
        if is_field_file and file_obj:
            # Skip if value has reference to actual file
            # It will be saved with key generated by config
            return  # pragma: no cover

        if not self.s3_config:
            raise exceptions.ImproperlyConfigured(  # pragma: no cover
                "Please set s3_config for field",
            )

        if not self.s3_config.key.validate(str(value)):
            raise exceptions.ValidationError(
                _("File's path doesn't match with config's pattern."),
            )


class S3FileField(S3FileFieldMixin, models.FileField):
    """FileField with S3 capabilities."""


class S3ImageField(S3FileFieldMixin, models.ImageField):
    """FileField with S3 capabilities."""
