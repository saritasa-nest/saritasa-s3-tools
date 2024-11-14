from django.core.files.storage import default_storage

from .. import client


def get_s3_client() -> client.S3Client:
    """Get s3 client based on Django default storage."""
    return client.S3Client(
        boto3_client=default_storage.connection.meta.client,  # type: ignore
        default_bucket=default_storage.bucket_name,  # type: ignore
    )
