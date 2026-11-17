"""Server CRUD tests (Phase 2)."""

import json
import re
from pathlib import Path


def _server_ids(app) -> list[str]:
    path = Path(app.config["SERVERS_FILE"])
    return [s["id"] for s in json.loads(path.read_text(encoding="utf-8"))]


def test_add_local_server(auth_client):
    response = auth_client.post(
        "/servers/new",
        data={"name": "This box", "is_local": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"This box" in response.data
    assert b"Server added." in response.data


def test_remote_requires_host_and_ssh(auth_client):
    response = auth_client.post(
        "/servers/new",
        data={"name": "Remote", "host": "", "ssh_user": "", "ssh_password": ""},
        follow_redirects=True,
    )
    assert b"Hostname or IP is required" in response.data


def test_add_remote_server(auth_client, app):
    response = auth_client.post(
        "/servers/new",
        data={
            "name": "Remote1",
            "host": "10.0.0.5",
            "ssh_user": "ubuntu",
            "ssh_password": "fake-secret",
        },
        follow_redirects=True,
    )
    assert b"Remote1" in response.data
    assert b"10.0.0.5" in response.data
    assert _server_ids(app)


def test_edit_does_not_echo_ssh_password(auth_client, app):
    auth_client.post(
        "/servers/new",
        data={
            "name": "Remote2",
            "host": "10.0.0.6",
            "ssh_user": "ops",
            "ssh_password": "super-secret-password",
        },
    )
    server_id = _server_ids(app)[0]
    overview = auth_client.get("/")
    assert b"Edit" in overview.data
    assert b"super-secret-password" not in overview.data

    edit = auth_client.get(f"/servers/{server_id}/edit")
    assert edit.status_code == 200
    assert b"super-secret-password" not in edit.data
    assert b'name="ssh_password"' in edit.data
    assert not re.search(rb'name="ssh_password"[^>]*value="[^"]+"', edit.data)


def test_edit_and_delete(auth_client, app):
    auth_client.post(
        "/servers/new",
        data={"name": "ToEdit", "is_local": "on"},
        follow_redirects=True,
    )
    server_id = _server_ids(app)[0]

    edited = auth_client.post(
        f"/servers/{server_id}/edit",
        data={"name": "Renamed", "is_local": "on"},
        follow_redirects=True,
    )
    assert b"Renamed" in edited.data
    assert b"Server updated." in edited.data

    deleted = auth_client.post(
        f"/servers/{server_id}/delete",
        follow_redirects=True,
    )
    assert b"Server removed." in deleted.data
    assert b"Renamed" not in deleted.data
    assert _server_ids(app) == []


def test_crud_requires_login(client):
    assert client.get("/servers/new", follow_redirects=False).status_code == 302
    assert (
        client.post("/servers/new", data={"is_local": "on"}, follow_redirects=False).status_code
        == 302
    )
