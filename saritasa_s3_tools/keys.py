import abc
import pathlib
import re
import unicodedata
import uuid


class S3Key:
    """Base class for s3 keys."""

    uuid_regex = r"[\d|\w]{8}-[\d|\w]{4}-[\d|\w]{4}-[\d|\w]{4}-[\d|\w]{12}"

    @abc.abstractmethod
    def __call__(self, filename: str | None) -> str:
        """Abstract method for calling keys."""

    def remove_special_characters(self, filename: str) -> str:
        """Remove characters from filename that are not allowed in some OS."""
        special_characters = r"<>:\"/\\|?*"
        return filename.translate({ord(i): None for i in special_characters})

    def normalize_string_value(self, value: str) -> str:
        """Normalize string value.

        1. Remove leading and trailing whitespaces.
        2. Replace all space characters with the Space char.
        3. Normalize Unicode string using `NFKC` form. See the details:
        https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize

        """
        cleaned = " ".join(value.strip().split()).strip()
        return unicodedata.normalize("NFKC", cleaned)

    def clean_filename(self, filename: str) -> str:
        """Remove `garbage` characters that cause problems with file names."""
        cleaned = self.remove_special_characters(filename)
        normalized = self.normalize_string_value(cleaned)

        return normalized

    def get_random_filename(self, filename: str) -> str:
        """Get random filename.

        Generation random filename that contains unique identifier and
        filename extension like: ``photo.jpg``.

        Args:
        ----
            filename (str): Name of file.

        Returns:
        -------
            new_filename (str): ``9841422d-c041-45a5-b7b3-467179f4f127.ext``.

        """
        path = str(uuid.uuid4())
        ext = pathlib.Path(filename).suffix.lower()

        return "".join((path, ext))

    def validate(self, key: str) -> bool:
        """Check that input key is matching Key pattern."""
        return True  # pragma: no cover


class WithPrefixUUIDFileName(S3Key):
    """Generate S3 key with prefix folder and uuid filename.

    Example:
    -------
        prefix/{UUID.extension}

    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.removesuffix("/")

    def __call__(self, filename: str | None) -> str:
        """Return prefixed S3 key."""
        if not filename:
            return f"{self.prefix}/{uuid.uuid4()}.incorrect"
        return f"{self.prefix}/{self.get_random_filename(filename)}"

    def validate(self, key: str) -> bool:
        """Check that input key is matching Key pattern."""
        return bool(
            re.compile(pattern=rf"{self.prefix}/{self.uuid_regex}\..+").match(
                key,
            ),
        )


class WithPrefixUUIDFolder(S3Key):
    """Generate S3 key with prefix folder and uuid folder.

    Example:
    -------
        prefix/{UUID}/filename

    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.removesuffix("/")

    def __call__(self, filename: str | None) -> str:
        """Create key for destination using filename."""
        if not filename:
            return f"{self.prefix}/{uuid.uuid4()}/{uuid.uuid4()}.incorrect"
        return f"{self.prefix}/{uuid.uuid4()}/{self.clean_filename(filename)}"

    def validate(self, key: str) -> bool:
        """Check that input key is matching Key pattern."""
        return bool(
            re.compile(
                pattern=rf"{self.prefix}/{self.uuid_regex}/.+\..+",
            ).match(
                key,
            ),
        )
