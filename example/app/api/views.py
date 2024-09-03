from rest_framework import viewsets

from .. import models
from . import serializers


class ModelWithFilesViewSet(
    viewsets.ModelViewSet,
):
    """Viewset for test model."""

    serializer_class = serializers.ModelWithFilesSerializer
    queryset = models.ModelWithFiles.objects.all()
