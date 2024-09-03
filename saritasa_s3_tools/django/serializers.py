import typing

import humanize
from django.conf import settings
from django.db import models
from rest_framework import exceptions, request, serializers

from .. import configs, constants
from . import drf_fields


class S3FieldsConfigMixin:
    """Extend serializer_field_mapping with s3 fields.

    Deprecate it once encode/django-rest-framework#9507 is accepted.

    """

    @property
    def serializer_field_mapping(
        self,
    ) -> dict[type[models.Field], type[serializers.Field]]:
        """Extend serializer mapping with s3 fields."""
        serializer_field_mapping = super().serializer_field_mapping  # type: ignore
        serializer_field_mapping[models.FileField] = (
            drf_fields.S3UploadURLField
        )
        serializer_field_mapping[models.ImageField] = (
            drf_fields.S3UploadURLField
        )
        return serializer_field_mapping


class S3RequestParamsSerializer(serializers.Serializer):
    """Serializer for validation s3 uploading fields."""

    config = drf_fields.S3FileTypeConfigField()
    filename = serializers.CharField()
    content_type = serializers.CharField()
    content_length = serializers.IntegerField()

    def __init__(
        self,
        context_request: request.Request | None = None,
        *args,  # noqa: ANN002
        **kwargs,
    ) -> None:
        """Set current user."""
        super().__init__(*args, **kwargs)
        self._request: request.Request | None = context_request
        self._user = getattr(self._request, "user", None)

    def validate_config(
        self,
        config: configs.S3FileTypeConfig,
    ) -> configs.S3FileTypeConfig:
        """Check that user can use dest."""
        if config.auth and not config.auth(self._user):
            raise exceptions.ValidationError(
                "Current user can't use this destination",
            )
        return config

    def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Perform validations.

        Check what input data is valid for specified configuration.

        """
        errors: dict[str, str] = {}
        config: configs.S3FileTypeConfig = attrs["config"]
        filename: str = attrs["filename"]
        content_type: str = attrs["content_type"]
        content_length: int = attrs["content_length"]
        if config.allowed and content_type not in config.allowed:
            expected = ", ".join(config.allowed)
            errors["content_type"] = (
                f"Invalid file type - `{content_type}` of `{filename}`. "
                f"Expected: {expected}."
            )
        if config.content_length_range:
            min_bound, max_bound = config.content_length_range
            if min_bound > content_length:
                errors["content_length"] = (
                    "Invalid file size "
                    f"- {humanize.naturalsize(content_length)} "
                    f"of {filename}. "
                    f"Need between {humanize.naturalsize(min_bound)} "
                    f"and {humanize.naturalsize(max_bound)}."
                )
            if max_bound < content_length:
                errors["content_length"] = (
                    "Invalid file size "
                    f"- {humanize.naturalsize(content_length)} "
                    f"of {filename}. "
                    f"Need between {humanize.naturalsize(min_bound)} "
                    f"and {humanize.naturalsize(max_bound)}."
                )
        if errors:
            raise exceptions.ValidationError(errors)
        return attrs


class S3ParamsSerializer(serializers.Serializer):
    """Serializer for showing params for s3 upload."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        fields = getattr(
            settings,
            "SARITASA_S3_TOOLS_UPLOAD_PARAMS",
            constants.s3v4_signature_fields,
        )
        for field in fields:
            self.fields[field] = serializers.CharField(
                label=field,
                required=False,
                allow_null=True,
            )


class S3UploadSerializer(serializers.Serializer):
    """Serializer auto swagger documentation.

    This serializer used just for packages that capable to generate
    openapi/swagger specs, so that front-end team
    could see specs for response for view.

    """

    url = serializers.URLField()
    params = S3ParamsSerializer()
