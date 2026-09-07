import contextlib
import dataclasses
import typing

from django.utils.functional import lazy
from rest_framework import (
    decorators,
    permissions,
    response,
    status,
    viewsets,
)
from rest_framework.request import Request

from .. import client, configs
from . import serializers, shortcuts


class S3GetParamsView(viewsets.GenericViewSet):
    """View for getting params for s3 to upload file to S3."""

    serializer_class = serializers.S3RequestParamsSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = ()
    pagination_class = None

    # Required to make BrowsableAPIRenderer` work.
    # DRF's `BrowsableAPIRenderer` calls `get_queryset` from
    # `get_filter_form` for every request.
    # `list_configs` methods returns list of objects,
    # so there is no clean way to bypass this.
    # This will work because `filter_backends` is empty for
    # this viewset.
    queryset = ()

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
        """Get parameters for upload to S3 bucket."""
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


def get_params_endpoint_description() -> str:
    """Get description for `get_params` endpoint."""
    description = (
        "Get parameters for upload to S3 bucket.\n\n"
        "Current endpoint returns all required for s3 upload data, which "
        "should be later sent to `url` as `form-data` url with 'file'. "
        "Workflow: "
        "First, you make request to this endpoint. "
        "Then send response data to `url` via `POST` as form-data with file "
        "included. "
        "In response you will get an url which you can use in API "
        "for value of file related fields like avatar for example.\n\n"
        "---\n\n"
        "**Available configs**:\n\n"
        f"{get_formatted_s3_configs()}"
    )
    return description


def get_formatted_s3_configs() -> str:
    """Get formatted S3 configs for endpoint description."""
    formatted_s3_configs: list[str] = []
    for name, config in configs.S3FileTypeConfig.configs.items():
        allowed_types = (
            ", ".join(config.allowed) if config.allowed else "All types"
        )
        content_length_range = (
            (
                f"{config.content_length_range[0]}-"
                f"{config.content_length_range[1]} bytes"
            )
            if config.content_length_range
            else "Any length"
        )
        formatted_s3_configs.append(
            f"`{name}`\n\n"
            f"| Parameter | Value |\n"
            f"|:---|:---|\n"
            f"| Allowed | {allowed_types} |\n"
            f"| Content length range | {content_length_range} |\n"
            f"| Expires in | {config.expires_in} seconds |\n"
            f"| Success action status | {config.success_action_status} |\n"
            f"| Content disposition | {config.content_disposition} |",
        )
    return "\n\n".join(formatted_s3_configs)


with contextlib.suppress(ImportError):
    import drf_spectacular.utils

    drf_spectacular.utils.extend_schema_view(
        get_params=drf_spectacular.utils.extend_schema(
            request=serializers.S3RequestParamsSerializer,
            responses=serializers.S3UploadSerializer,
            # Generate the description lazily to include the S3 configs after
            # the initial import of this module to ensure they were registered.
            description=lazy(get_params_endpoint_description, str)(),
        ),
    )(S3GetParamsView)
