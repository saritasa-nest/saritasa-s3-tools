import pytest
from django.core import exceptions

from example.app import factories


def test_model_mimetype_validation():
    """Check that model field validation works for mimetype."""
    with pytest.raises(exceptions.ValidationError) as exc_info:
        factories.ModelWithFilesInvalidTypesFactory.build().full_clean()
    assert "image" in exc_info.value.message_dict
    assert (
        exc_info.value.message_dict["image"][0]
        == "File's mime type doesn't match with config's allowed types: "
        "image/png, image/jpeg."
    )
