import pytest
from icecream import ic
from datetime import datetime
from typing import Iterable

from fastapi.testclient import TestClient

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from minio import Minio
from .minio_config_test import minio_settings

from app.main import app
from app.models.models import Base, UsersORM, FilesORM
from app.routers.auth import bcrypt_context

SQLALCHEMY_DATABASE_URL = "sqlite:///tests/.testdb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

session_factory_test = sessionmaker(
    autoflush=False,
    bind=engine,
)

Base.metadata.create_all(bind=engine)


def get_test_db():
    db = session_factory_test()

    try:
        yield db
    finally:
        db.close()


def get_test_s3_client():
    client = Minio(
        minio_settings.MINIO_ENDPOINT_TEST,
        access_key=minio_settings.MINIO_ACCESS_KEY_TEST,
        secret_key=minio_settings.MINIO_SECRET_KEY_TEST,
        secure=False,
    )

    return client


def get_test_user():
    return {
        "username": "test_user",
        "id": "1",
    }


@pytest.fixture
def clear_database():
    with session_factory_test() as session:
        session.execute(text("DELETE FROM users;"))
        session.execute(text("DELETE FROM files;"))
        session.commit()

    yield

    with session_factory_test() as session:
        session.execute(text("DELETE FROM users;"))
        session.execute(text("DELETE FROM files;"))
        session.commit()


@pytest.fixture
def s3_client():
    client = get_test_s3_client()
    if client is None:
        pytest.fail("S3 client is None")
    return client


@pytest.fixture
def test_user() -> Iterable[UsersORM]:
    with session_factory_test() as session:
        session.execute(text("DELETE FROM users;"))
        session.execute(text("DELETE FROM files;"))
        session.commit()

    user = UsersORM(
        username="test_user",
        email="test_user@gmail.com",
        hashed_password=bcrypt_context.hash("testpass"),
    )

    db = session_factory_test()
    db.add(user)
    db.commit()

    yield user

    with session_factory_test() as session:
        session.execute(text("DELETE FROM users;"))
        session.execute(text("DELETE FROM files;"))
        session.commit()


@pytest.fixture
def test_file(test_user):
    db = session_factory_test()

    file = FilesORM(
        file_name="testfile.txt",
        user_id=test_user.id,
        upload_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(file)
    db.commit()
    db.refresh(file)

    yield file

    db.delete(file)
    db.commit()


test_client = TestClient(app)
