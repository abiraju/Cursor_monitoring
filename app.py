"""InfraMonitor — local demo Flask app (auth, CRUD, metrics, CSRF)."""

from __future__ import annotations

import os
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from monitor.metrics import collect_for_server
from storage import (
    DEFAULT_DATA_FILE,
    find_server,
    load_servers,
    new_server_id,
    save_servers,
)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")
REFRESH_SECONDS = 8


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=None,
        SERVERS_FILE=str(DEFAULT_DATA_FILE),
        DEBUG=False,
    )
    if test_config:
        app.config.update(test_config)

    CSRFProtect(app)

    def servers_path() -> Path:
        return Path(app.config["SERVERS_FILE"])

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("logged_in"):
            return redirect(url_for("overview"))

        error = None
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            if username == ADMIN_USERNAME and check_password_hash(
                ADMIN_PASSWORD_HASH, password
            ):
                session.clear()
                session["logged_in"] = True
                session["username"] = ADMIN_USERNAME
                next_url = request.args.get("next") or url_for("overview")
                if not next_url.startswith("/"):
                    next_url = url_for("overview")
                return redirect(next_url)
            error = "Invalid username or password."

        return render_template("login.html", error=error)

    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def overview():
        cards = []
        for server in load_servers(servers_path()):
            cards.append({"server": server, "metrics": collect_for_server(server)})
        return render_template(
            "overview.html",
            cards=cards,
            refresh_seconds=REFRESH_SECONDS,
        )

    @app.route("/servers/<server_id>")
    @login_required
    def detail(server_id: str):
        server = find_server(servers_path(), server_id)
        if not server:
            flash("Server not found.", "error")
            return redirect(url_for("overview"))
        metrics = collect_for_server(server)
        return render_template(
            "detail.html",
            server=server,
            metrics=metrics,
            refresh_seconds=REFRESH_SECONDS,
        )

    @app.route("/servers/new", methods=["GET", "POST"])
    @login_required
    def server_new():
        if request.method == "POST":
            return _save_server_form(None)
        return render_template("server_form.html", server=None, title="Add server")

    @app.route("/servers/<server_id>/edit", methods=["GET", "POST"])
    @login_required
    def server_edit(server_id: str):
        server = find_server(servers_path(), server_id)
        if not server:
            flash("Server not found.", "error")
            return redirect(url_for("overview"))
        if request.method == "POST":
            return _save_server_form(server_id)
        return render_template("server_form.html", server=server, title="Edit server")

    @app.route("/servers/<server_id>/delete", methods=["POST"])
    @login_required
    def server_delete(server_id: str):
        path = servers_path()
        existing = find_server(path, server_id)
        if not existing:
            flash("Server not found.", "error")
            return redirect(url_for("overview"))
        servers = [s for s in load_servers(path) if s.get("id") != server_id]
        save_servers(path, servers)
        flash("Server removed.", "ok")
        return redirect(url_for("overview"))

    def _save_server_form(server_id: str | None):
        path = servers_path()
        name = (request.form.get("name") or "").strip()
        host = (request.form.get("host") or "").strip()
        is_local = request.form.get("is_local") == "on"
        ssh_user = (request.form.get("ssh_user") or "").strip()
        ssh_password = request.form.get("ssh_password") or ""

        if not name:
            name = "Local host" if is_local else (host or "Server")

        if not is_local and not host:
            flash("Hostname or IP is required for remote servers.", "error")
            return redirect(request.url)

        if not is_local:
            existing = find_server(path, server_id) if server_id else None
            if server_id and existing:
                if not ssh_password:
                    ssh_password = existing.get("ssh_password", "")
                if not ssh_user:
                    ssh_user = existing.get("ssh_user", "")
            if not ssh_user or not ssh_password:
                flash("SSH username and password are required for remote servers.", "error")
                return redirect(request.url)

        payload = {
            "id": server_id or new_server_id(),
            "name": name,
            "host": "localhost" if is_local else host,
            "is_local": is_local,
            "ssh_user": "" if is_local else ssh_user,
            "ssh_password": "" if is_local else ssh_password,
        }

        servers = load_servers(path)
        if server_id:
            if not find_server(path, server_id):
                flash("Server not found.", "error")
                return redirect(url_for("overview"))
            servers = [payload if s.get("id") == server_id else s for s in servers]
            flash("Server updated.", "ok")
        else:
            servers.append(payload)
            flash("Server added.", "ok")

        save_servers(path, servers)
        return redirect(url_for("overview"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5600, debug=False)
