from rest_framework import serializers

import saritasa_s3_tools.django

from .. import models


class ModelWithFilesSerializer(
    saritasa_s3_tools.django.S3FieldsConfigMixin,
    serializers.ModelSerializer,
):
    """Serializer to show info model with files."""

    class Meta:
        model = models.ModelWithFiles
        fields = "__all__"
