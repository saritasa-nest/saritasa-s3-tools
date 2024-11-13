import mypy_boto3_s3


def test_fixture(
    boto3_resource_from_config: mypy_boto3_s3.S3ServiceResource,
    s3_bucket_name: str,
) -> None:
    """Test that alternative fixture for s3 resource is working."""
    boto3_resource_from_config.Bucket(s3_bucket_name).objects.all()
