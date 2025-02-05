# Version history

We follow [Semantic Versions](https://semver.org/).

## Unreleased

## 0.3.2

- Make `S3UploadURLField` support just `str` values

## 0.3.1

- Manually validate length in `S3UploadURLField`
This is needed so that in api specs there would be no length limit

## 0.3.0

- Confirm support for python 3.13
- Add `get_s3_client` shortcut for `django` module
- Make `pytest` plugin auto-detect if it's `django` project, so that it could
use `django` storage for `s3` setup
- Remove explicit `max_length` limit in `S3UploadURLField`
  It causes issues with auto spec generation and validation.
  Since it can return full urls with auth query, which can easily pass
  a limit specified in model field(which is by default 100), it causes
  confusion for openapi specs validators.

## 0.2.1

- Fix validators setup in `S3FileFieldMixin`

## 0.2.0

- Refactor and improve validation on keys in django module
- Rename `S3KeyWithUUID` to `WithPrefixUUIDFileName`
- Rename `S3KeyWithPrefix` to `WithPrefixUUIDFolder`

## 0.1.0

- Beta release
