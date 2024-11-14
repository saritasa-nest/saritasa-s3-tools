import contextlib
import dataclasses
import typing

from rest_framework import (
    decorators,
    permissions,
    response,
    status,
    viewsets,
)
from rest_framework.request import Request

from .. import client
from . import serializers, shortcuts


class S3GetParamsView(viewsets.GenericViewSet):
    """View for getting params for s3 to upload file to S3."""

    serializer_class = serializers.S3RequestParamsSerializer
    permission_classes = (permissions.AllowAny,)

    @decorators.action(
        methods=["POST"],
        url_path="get-params",
        url_name="get-params",
        detail=False,
    )
    def get_params(
        self,
        request: Request,
    ) -> response.Response:
        """Get parameters for upload to S3 bucket.

        Current endpoint returns all required for s3 upload data,
        which should be later sent to `url` as `form-data` url with
        'file'. Workflow: First, you make request to this endpoint. Then send
        response data to `url` via `POST` as form-data with file included. In
        response you will get an url which you can use in API for value of file
        related fields like avatar for example.

        """
        serializer = self.serializer_class(
            context_request=request,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        s3_client = self.get_s3_client()
        params = s3_client.generate_params(
            filename=serializer.data["filename"],  # type: ignore
            config=serializer.data["config"],  # type: ignore
            content_type=serializer.data["content_type"],  # type: ignore
            extra_metadata=self.get_extra_meta_data(user=request.user),
        )
        return response.Response(
            status=status.HTTP_200_OK,
            data=serializers.S3UploadSerializer(
                instance=dataclasses.asdict(params),
            ).data,
        )

    def get_s3_client(self) -> client.S3Client:
        """Get s3 client for params generation."""
        return shortcuts.get_s3_client()

    def get_extra_meta_data(
        self,
        user: typing.Any,
    ) -> dict[str, str]:
        """Extend meta data for file."""
        return {
            "user-id": str(user.pk),
        }


with contextlib.suppress(ImportError):
    import drf_spectacular.utils

    drf_spectacular.utils.extend_schema_view(
        get_params=drf_spectacular.utils.extend_schema(
            request=serializers.S3RequestParamsSerializer,
            responses=serializers.S3UploadSerializer,
        ),
    )(S3GetParamsView)
