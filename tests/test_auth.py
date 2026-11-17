"""Auth unit tests (Phase 1)."""

from app import ADMIN_PASSWORD_HASH, ADMIN_USERNAME


def test_password_is_stored_as_hash_not_plaintext():
    assert ADMIN_PASSWORD_HASH != "admin123"
    assert ADMIN_PASSWORD_HASH.startswith(("scrypt:", "pbkdf2:"))


def test_protected_overview_redirects_when_anonymous(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data
    assert b"admin123" not in response.data  # do not embed demo password in HTML


def test_valid_login_reaches_overview(client):
    response = client.post(
        "/login",
        data={"username": ADMIN_USERNAME, "password": "admin123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Servers" in response.data
    assert b"Sign out" in response.data


def test_bad_password_rejected(client):
    response = client.post(
        "/login",
        data={"username": ADMIN_USERNAME, "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password." in response.data
    # Still on login — overview chrome should not appear as authenticated
    assert b"Sign out" not in response.data


def test_non_admin_rejected(client):
    response = client.post(
        "/login",
        data={"username": "other", "password": "admin123"},
        follow_redirects=True,
    )
    assert b"Invalid username or password." in response.data


def test_logout_clears_session(client):
    client.post("/login", data={"username": ADMIN_USERNAME, "password": "admin123"})
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    protected = client.get("/", follow_redirects=False)
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]
