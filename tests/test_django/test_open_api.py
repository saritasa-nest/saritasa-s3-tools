import pathlib

from django.core.management import call_command


def test_open_api(tmp_path: pathlib.Path) -> None:
    """Validate that schema is properly generated."""
    call_command(
        "spectacular",
        file=tmp_path / "schema.yaml",
        validate=True,
        fail_on_warn=True,
    )
