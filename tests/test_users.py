import pytest
from icecream import ic

from app.main import app
from app.data.dependencies import get_db
from app.routers.auth import get_current_user


from .dependencies import (
    test_client,
    get_test_db,
    get_test_user,
    test_user,
    clear_database,
)

app.dependency_overrides[get_db] = get_test_db
app.dependency_overrides[get_current_user] = get_test_user


def test_register_user(clear_database):
    response = test_client.post(
        "/auth/register",
        data={
            "email": "new_user@gmail.com",
            "username": "new_user",
            "password": "newpass",
            "password2": "newpass",
        },
    )

    assert response.status_code == 200
    assert b"User successfully created" in response.content


def test_register_user_existing_username(test_user):
    response = test_client.post(
        "/auth/register",
        data={
            "email": "new_user2@gmail.com",
            "username": "test_user",  # already exists
            "password": "newpass",
            "password2": "newpass",
        },
    )

    assert response.status_code == 200
    assert b"Username or email already exists" in response.content


def test_register_user_password_mismatch():
    response = test_client.post(
        "/auth/register",
        data={
            "email": "new_user3@gmail.com",
            "username": "new_user3",
            "password": "newpass1",
            "password2": "newpass2",  # different passwords
        },
    )

    assert response.status_code == 200
    assert b"Passwords do not match" in response.content


def test_login_user(test_user):
    response = test_client.post(
        "/auth/",
        data={"username": "test_user", "password": "testpass"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "access_token" in response.cookies


def test_login_user_wrong_password(test_user):
    response = test_client.post(
        "/auth/",
        data={"username": "test_user", "password": "wrongpass"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"Incorrect username or password" in response.content


def test_logout_user(test_user):
    # Log in
    response = test_client.post(
        "/auth/",
        data={"username": "test_user", "password": "testpass"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "access_token" in response.cookies

    # Log out
    response = test_client.get("/auth/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies
    assert b"Logout successful" in response.content
