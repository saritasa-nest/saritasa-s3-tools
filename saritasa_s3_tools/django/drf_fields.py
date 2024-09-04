import typing
import urllib.parse

from django.conf import settings
from django.core import exceptions as django_exceptions
from django.core import validators
from django.core.files.storage import default_storage
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, fields, serializers

import botocore.exceptions

from .. import configs


class S3FileTypeConfigField(serializers.ChoiceField):
    """Custom Choice field for s3 configs.

    Represent config choice in api and covert this choice to proper
    S3FileTypeConfig instance.

    """

    def __init__(self, **kwargs) -> None:
        super().__init__(choices=(), **kwargs)

    def _get_choices(self) -> dict[str, str]:
        """Get choices from S3FileTypeConfig."""
        current_choices = tuple(
            (
                config_name,
                config_name,
            )
            for config_name in configs.S3FileTypeConfig.configs
        )
        choices = super()._get_choices()
        if current_choices != choices:
            self._set_choices(current_choices)
        return super()._get_choices()

    def _set_choices(self, choices: tuple[tuple[str, str], ...]) -> None:
        """Update choices.

        Redefined to avoid recursion.

        """
        self.grouped_choices = fields.to_choices_dict(choices)
        self._choices = fields.flatten_choices_dict(
            self.grouped_choices,
        )

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = {
            str(key): key for key in self._choices
        }

    choices = property(_get_choices, _set_choices)

    def to_internal_value(
        self,
        data: typing.Any,
    ) -> configs.S3FileTypeConfig | None:
        """Convert api data to S3FileTypeConfig."""
        try:
            return configs.S3FileTypeConfig.configs[str(data)]
        except KeyError:
            self.fail("invalid_choice", input=data)


class S3UploadURLField(serializers.URLField):
    """URL serializer field for S3 `files or keys or URLs or objects`.

    Convert url to a valid s3 key for bucket. On validation check that
    key is present in bucket.

    Example:
    -------
    https://www.saritasa-s3-tools.s3.localhost/some-folder/file.txt will
    become `some-folder/file.txt` which is location of file in bucket (key).
    Same result will apply if AWS_LOCATION is used.
    https://www.saritasa-s3-tools.s3.localhost/locations/some-folder/file.txt
    will become `some-folder/file.txt`.

    """

    def __init__(self, **kwargs) -> None:
        """Make custom initialization.

        Add URLValidator to self, but don't add it to self.validators, because
        now validation is called after `to_internal_value`. So it provides
        validation before `to_internal_value`.

        """
        super(serializers.URLField, self).__init__(**kwargs)
        self.url_validator = validators.URLValidator(
            message=self.error_messages["invalid"],
        )

        # Append this validator to enable invalid code for spec
        validator_for_spec = validators.MinLengthValidator(
            0,
            message=self.error_messages["invalid"],
        )
        validator_for_spec.code = "invalid"
        self.validators.append(validator_for_spec)

    def to_internal_value(self, data: typing.Any) -> str:
        """Validate `data` and convert it to internal value.

        Cut domain from url to save it in file field.

        """
        if not isinstance(data, str):
            self.fail("invalid")
        self.url_validator(value=data)

        # Crop server domain and port and get relative path to avatar
        file_url = urllib.parse.urlparse(url=data).path

        # Crop S3 bucket name
        file_url = file_url.split(
            f"{settings.AWS_STORAGE_BUCKET_NAME}/",
        )[-1].lstrip("/")

        # Normalize url
        file_url = urllib.parse.unquote_plus(file_url)

        # Remove aws-location prefix to keep only file name as key
        aws_location = getattr(settings, "AWS_LOCATION", "")
        if aws_location and file_url.startswith(aws_location):
            file_url = file_url.split(f"{aws_location}/")[-1]

        # If url comes not from s3, then botocore on url validation will
        # raise ParamValidationError
        try:
            if not default_storage.exists(file_url):
                raise exceptions.ValidationError(
                    _("File does not exist."),
                )
        except botocore.exceptions.ParamValidationError as error:
            raise exceptions.ValidationError(
                error,
            ) from error  # pragma: no cover
        except django_exceptions.SuspiciousFileOperation as error:
            raise exceptions.ValidationError(
                error,
            ) from error  # pragma: no cover
        return file_url

    def to_representation(self, value: typing.Any) -> str | None:
        """Return full file url."""
        if not value:
            return None
        return value.url
