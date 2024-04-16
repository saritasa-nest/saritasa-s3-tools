# saritasa-s3-tools

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/saritasa-nest/saritasa-s3-tools/checks.yml)
![PyPI](https://img.shields.io/pypi/v/saritasa-s3-tools)
![PyPI - Status](https://img.shields.io/pypi/status/saritasa-s3-tools)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/saritasa-s3-tools)
![PyPI - License](https://img.shields.io/pypi/l/saritasa-s3-tools)
![PyPI - Downloads](https://img.shields.io/pypi/dm/saritasa-s3-tools)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Extension for boto3 to ease work with s3

## Installation

```bash
pip install saritasa-s3-tools
```

or if you are using [poetry](https://python-poetry.org/)

```bash
poetry add saritasa-s3-tools
```

To install all optional dependencies add `[all]`

## Features

* `S3Client` and `AsyncS3Client` for integrations with s3 buckets
* `S3FileTypeConfig` for defining configuration parameters for direct upload to s3
* `S3Key` for generating unique keys for s3 upload
* `pytest` plugin with fixtures for `boto3`, `S3Client` and `AsyncS3Client`

## Direct upload example

```python
import saritasa_s3_tools
import pathlib
import xml.etree.ElementTree

s3_client = saritasa_s3_tools.S3Client(
    boto3_client=boto3_client,
    default_bucket=s3_bucket,
)
s3_params = s3_client.generate_params(
    filename=pathlib.Path(__file__).name,
    config=saritasa_s3_tools.S3FileTypeConfig.configs["files"],
    content_type="application/x-python-code",
    extra_metadata={
        "test": "123",
    },
)
with (
    httpx.Client() as client,
    pathlib.Path(__file__).open("rb") as upload_file,
):
    upload_response = client.post(
        url=s3_params.url,
        data={
            key: value
            for key, value in s3_params.params.items()
            if value is not None
        },
        files={"file": upload_file.read()},
    )
parsed_response = xml.etree.ElementTree.fromstring(  # noqa: S314
    upload_response.content.decode(),
)
file_key = parsed_response[2].text
file_url = parsed_response[0].text
```
