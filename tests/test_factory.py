import botocore.credentials

import saritasa_s3_tools


def test_s3_file_factory(
    s3_client: saritasa_s3_tools.S3Client,
    s3_bucket_name: str,
) -> None:
    """Test S3FileField."""
    file_key = saritasa_s3_tools.factory.S3FileField(
        s3_config="files",
        s3_region="us-west-1",
        bucket=s3_bucket_name,
        access_key_getter=lambda: botocore.credentials.Credentials(
            access_key="root",
            secret_key="rootroot",
        ),
        s3_endpoint_url_getter=lambda: "http://s3.minio.localhost:9001",
    ).evaluate(object(), None, None)
    (
        s3_client.is_file_in_bucket(
            file_key,
            bucket=s3_bucket_name,
        ),
        file_key,
    )


def test_s3_image_factory(
    s3_client: saritasa_s3_tools.S3Client,
    s3_bucket_name: str,
) -> None:
    """Test S3ImageFileField."""
    file_key = saritasa_s3_tools.factory.S3ImageFileField(
        s3_config="files",
        s3_region="us-west-1",
        bucket=s3_bucket_name,
        access_key_getter=lambda: botocore.credentials.Credentials(
            access_key="root",
            secret_key="rootroot",
        ),
        s3_endpoint_url_getter=lambda: "http://s3.minio.localhost:9001",
    ).evaluate(object(), None, None)
    assert s3_client.is_file_in_bucket(
        file_key,
        bucket=s3_bucket_name,
    ), file_key
