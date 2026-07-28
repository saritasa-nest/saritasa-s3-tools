import dataclasses
import typing

from . import keys


class S3FileTypeConfigMeta(type):
    """Meta class for S3FileTypeConfig."""

    def __call__(
        cls,
        *args,  # noqa: ANN002
        **kwargs,
    ) -> "S3FileTypeConfig":
        """Update mapping of S3SupportedFieldConfigs."""
        instance: S3FileTypeConfig = super().__call__(*args, **kwargs)
        if instance.name in S3FileTypeConfig.configs:
            raise ValueError(f"{instance.name} config is already defined")
        S3FileTypeConfig.configs[instance.name] = instance
        return instance


@dataclasses.dataclass(frozen=True)
class S3FileTypeConfig(metaclass=S3FileTypeConfigMeta):
    """Configuration for S3 file upload."""

    configs: typing.ClassVar[dict[str, "S3FileTypeConfig"]] = {}

    name: str
    # S3Key are used to generate file's path
    key: keys.S3Key
    # Mime types are allowed, None - for all
    allowed: tuple[str, ...] | None = None
    # Perform checks against user
    auth: typing.Callable[[typing.Any | None], bool] | None = None
    # Define allowed size limits for file (in bytes)
    content_length_range: tuple[int, int] | None = None
    # In how much second pre-signed URL for upload will expire
    expires_in: int = 3600
    success_action_status: int = 201
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition
    content_disposition: typing.Literal["attachment", "inline"] = "attachment"

    def get_short_description(self) -> str:
        """Get short description for config."""
        allowed_types = (
            ", ".join(self.allowed) if self.allowed else "All types"
        )
        content_length_range = (
            (
                f"{self.content_length_range[0]}-"
                f"{self.content_length_range[1]} bytes"
            )
            if self.content_length_range
            else "Any length"
        )
        return (
            f"*Allowed types*: {allowed_types}, "
            f"*Content length range*: {content_length_range}, "
            f"*Expires in*: {self.expires_in} seconds, "
            f"*Success action status*: {self.success_action_status}, "
            f"*Content disposition*: {self.content_disposition}"
        )
