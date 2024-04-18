import re

import pytest

import saritasa_s3_tools


def test_config_duplicate() -> None:
    """Check that it's impossible to create duplicate of config."""
    with pytest.raises(
        ValueError,
        match=re.escape("files config is already defined"),
    ):
        saritasa_s3_tools.S3FileTypeConfig(
            name="files",
            key=saritasa_s3_tools.keys.S3KeyWithPrefix("files"),
        )
