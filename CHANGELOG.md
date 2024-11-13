# Version history

We follow [Semantic Versions](https://semver.org/).

## Unreleased

- Confirm support for python 3.13
- Add `get_s3_client` shortcut for `django` module
- Make `pytest` plugin auto-detect if it's `django` project, so that it could
use `django` storage for `s3` setup

## 0.2.1

- Fix validators setup in `S3FileFieldMixin`

## 0.2.0

- Refactor and improve validation on keys in django module
- Rename `S3KeyWithUUID` to `WithPrefixUUIDFileName`
- Rename `S3KeyWithPrefix` to `WithPrefixUUIDFolder`

## 0.1.0

- Beta release
