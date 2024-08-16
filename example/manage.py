#!/usr/bin/env python
import os
import sys

from rich import traceback as rich_traceback

# https://rich.readthedocs.io/en/latest/traceback.html
# Prettify traceback
rich_traceback.install()

if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "example.settings",
    )

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
