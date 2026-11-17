"""Shared pytest fixtures — isolated from real data/ and production secrets."""

from pathlib import Path

import pytest

from app import ADMIN_USERNAME, create_app


@pytest.fixture
def app(tmp_path: Path):
    servers_file = tmp_path / "servers.json"
    servers_file.write_text("[]", encoding="utf-8")
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-not-for-production",
            "WTF_CSRF_ENABLED": False,
            "SERVERS_FILE": str(servers_file),
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/login", data={"username": ADMIN_USERNAME, "password": "admin123"})
    return client
