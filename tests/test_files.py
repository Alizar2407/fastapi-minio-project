from app.main import app
from app.data.dependencies import get_db, get_s3_client
from app.routers.auth import get_current_user


from .dependencies import (
    test_client,
    get_test_db,
    get_test_user,
    get_test_s3_client,
)

app.dependency_overrides[get_db] = get_test_db
app.dependency_overrides[get_current_user] = get_test_user
app.dependency_overrides[get_s3_client] = get_test_s3_client

BUCKET_NAME = "files-bucket"


def test_list_files(test_user):
    response = test_client.get("/files/")
    assert response.status_code == 200


def test_get_upload_link(test_user, s3_client):
    if not s3_client.bucket_exists(BUCKET_NAME):
        s3_client.make_bucket(BUCKET_NAME)

    filename = "testfile.txt"
    response = test_client.get(f"/files/upload/?filename={filename}")

    assert response.status_code == 200
    assert b"Here is your file upload link:" in response.content


def test_download_file(test_user, test_file):
    response = test_client.get(
        f"/files/download/{test_file.id}",
        follow_redirects=False,
    )

    assert response.status_code == 307


def test_unauthorized_access():
    def get_none_user():
        return None

    previous_dependency = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = get_none_user

    response = test_client.get(
        "/files/",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "location" in response.headers
    assert response.headers["location"] == "/auth"

    app.dependency_overrides[get_current_user] = previous_dependency
