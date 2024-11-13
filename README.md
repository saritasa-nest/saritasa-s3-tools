# saritasa-s3-tools

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/saritasa-nest/saritasa-s3-tools/checks.yaml)
[![PyPI](https://img.shields.io/pypi/v/saritasa-s3-tools)](https://pypi.org/project/saritasa-s3-tools/)
![PyPI - Status](https://img.shields.io/pypi/status/saritasa-s3-tools)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/saritasa-s3-tools)
![PyPI - Django Version](https://img.shields.io/pypi/frameworkversions/django/saritasa-s3-tools)
![PyPI - License](https://img.shields.io/pypi/l/saritasa-s3-tools)
![PyPI - Downloads](https://img.shields.io/pypi/dm/saritasa-s3-tools)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Extension for boto3 to ease work with s3

## Table of contents

* [Installation](#installation)
* [Features](#features)
* [Django](#django)
* [Optional dependencies](#optional-dependencies)
* [Direct upload example](#direct-upload-example)
* [Pytest](#pytest-plugin)

## Installation

```bash
pip install saritasa-s3-tools
```

or if you are using [poetry](https://python-poetry.org/)

```bash
poetry add saritasa-s3-tools
```

## Features

* `S3Client` and `AsyncS3Client` for integrations with s3 buckets. This clients
are extension to boto3 clients with proper typing, support for async and
method to generate signed urls for file upload.
* `S3FileTypeConfig` for defining configuration parameters for direct upload to s3.
[Check out more](saritasa_s3_tools/configs.py#L24)
* `S3Key` for generating unique keys for s3 upload, used for `S3FileTypeConfig`
* `S3FileField` and `S3ImageFileField` - [factory-boy](https://github.com/FactoryBoy/factory_boy) fields for generating files and saving it in `s3`
* `pytest` plugin with fixtures for `boto3`, `S3Client` and `AsyncS3Client` and etc
* `Django` plugin for setting up models and api

## Django

`saritasa-s3-tools` comes with django plugin which helps with models
config and api(`Django Rest Framework` and `drf_spectacular`).
You can try it out in `example` folder.

### Setup model

First you need to add file/image fields to you model, like below

```python
import saritasa_s3_tools.django

from django.db import models

class ModelWithFiles(models.Model):
    """Test model with different files configs."""

    file = saritasa_s3_tools.django.S3FileField(
        blank=True,
        null=True,
        # S3FileTypeConfig is needed so that we could understand where to save
        # file, who can save file, what files can be save and what are size
        # constraints
        s3_config=saritasa_s3_tools.S3FileTypeConfig(
            name="django-files",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFolder("django-files"),
            allowed=("text/plain",),
            auth=lambda user: bool(user and user.is_authenticated),
            content_length_range=(1000, 20000000),
        ),
    )

    image = saritasa_s3_tools.django.S3ImageField(
        blank=True,
        null=True,
        s3_config=saritasa_s3_tools.S3FileTypeConfig(
            name="django-images",
            key=saritasa_s3_tools.keys.WithPrefixUUIDFolder("django-images"),
            allowed=("image/png",),
            content_length_range=(5000, 20000000),
        ),
    )
```

### Setup serializers

Then add `S3FieldsConfigMixin` mixin to your serializer, like this

```python
from rest_framework import serializers

import saritasa_s3_tools.django

from .. import models


class ModelWithFilesSerializer(
    saritasa_s3_tools.django.S3FieldsConfigMixin,
    serializers.ModelSerializer,
):
    """Serializer to show info model with files."""

    class Meta:
        model = models.ModelWithFiles
        fields = "__all__"

```

### Setup view

Then just add `S3GetParamsView` view to your project urls like that.

```python
from django.urls import path

path(
    "s3/",
    include("saritasa_s3_tools.django.urls"),
    name="saritasa-s3-tools",
),
```

### Setup pytest

Just add this to core `conftest.py` file

```python
import pytest


@pytest.fixture(scope="session", autouse=True)
def _adjust_s3_bucket(django_adjust_s3_bucket: None) -> None:
    """Set bucket to a test one."""
```

### Note about signature version

By default we assume `s3v4` version for signature. We recommend that you would
set `AWS_S3_SIGNATURE_VERSION` to `s3v4`. If you need other versions, set it in
`AWS_S3_SIGNATURE_VERSION` and update `SARITASA_S3_TOOLS_UPLOAD_PARAMS`
(defaults are [here](saritasa_s3_tools/constants.py)) setting
to reflect expected fields that would return.

## Optional dependencies

* `[async]` - Add this to enable async support
* `[factory]` - Add this to enable factory-boy field `S3FileField` and `S3ImageFileField`
from `saritasa_s3_tools.factory`
* `[testing]` - Add this to enable testing helping functions from
`saritasa_s3_tools.testing.shortcuts`
* `[django]` - Add this to enable [django support](#django)
* `[django-openapi]` - Add this to enable [drf-spectacular support](#django)

To install all optional dependencies add `[all]`

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

## pytest plugin

`saritasa-s3-tools` comes with pytest plugin which can setup boto3 instances
and create/clean up buckets for testing. Supports `pytest-xdist`.

### Fixtures

* `access_key_getter`, `s3_endpoint_url_getter`, `s3_region` - are used to
configure boto3 session and clients/resources that are used in tests.
You can override them or set values in ini file for pytest. Plugin will tell
what you are missing.
* `aws_session` - Returns `boto3.Session`
* `aws_config` - Returns `botocore.config.Config`, override if you need
customization, None by default.
* `boto3_resource` - Returns s3 resource or in typing `mypy_boto3_s3.S3ServiceResource`
* `boto3_client`- Returns s3 client or in typing `mypy_boto3_s3.S3Client`
* `s3_bucket_name` - Name of bucket for testing, default: `saritasa-s3-tools`
or `s3_bucket_name` from ini file.
* `s3_bucket_cleaner` - Returns function which cleans all files from bucket
* `s3_bucket_factory` - Returns manager which creates bucket, and when it's no
longer needed deletes it
* `s3_bucket` - Creates bucket via `s3_bucket_factory` and return it's name
* `s3_client` - Returns `saritasa_s3_tools.S3Client`
* `async_s3_client` - Returns `saritasa_s3_tools.AsyncS3Client`
