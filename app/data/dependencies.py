from icecream import ic

from minio import Minio
from minio.error import S3Error
from app.data.database import session_factory

from .minio_config import minio_settings


def get_db():
    try:
        db = session_factory()
        yield db
    finally:
        db.close()


def get_s3_client():
    client = Minio(
        minio_settings.MINIO_ENDPOINT,
        access_key=minio_settings.MINIO_ACCESS_KEY,
        secret_key=minio_settings.MINIO_SECRET_KEY,
        secure=False,
    )

    bucket_name = "files-bucket"

    try:

        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            # ic(f"Bucket {bucket_name} created successfully.")

        else:
            pass
            # ic(f"Bucket {bucket_name} already exists.")

    except S3Error as e:
        ic(f"Error connecting to S3: {e}")
        return None

    return client
