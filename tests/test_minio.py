import pytest
from minio.error import S3Error
from .dependencies import s3_client


BUCKET_NAME = "test-bucket"


def test_s3_client_not_none(s3_client):
    assert s3_client is not None, "S3 client should not be None"


def test_create_bucket(s3_client):
    try:
        if not s3_client.bucket_exists(BUCKET_NAME):
            s3_client.make_bucket(BUCKET_NAME)
        assert s3_client.bucket_exists(
            BUCKET_NAME
        ), f"Bucket {BUCKET_NAME} should be created"
    except S3Error as e:
        pytest.fail(f"Error creating bucket: {e}")


def test_delete_bucket(s3_client):
    try:
        if s3_client.bucket_exists(BUCKET_NAME):
            s3_client.remove_bucket(BUCKET_NAME)
        assert not s3_client.bucket_exists(
            BUCKET_NAME
        ), f"Bucket {BUCKET_NAME} should be deleted"
    except S3Error as e:
        pytest.fail(f"Error deleting bucket: {e}")
