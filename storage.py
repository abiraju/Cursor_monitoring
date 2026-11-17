"""Local JSON persistence for monitored servers (data/ is gitignored)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

DEFAULT_DATA_FILE = Path(__file__).resolve().parent / "data" / "servers.json"


def ensure_store(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def load_servers(path: Path) -> list[dict[str, Any]]:
    ensure_store(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_servers(path: Path, servers: list[dict[str, Any]]) -> None:
    ensure_store(path)
    path.write_text(json.dumps(servers, indent=2), encoding="utf-8")


def find_server(path: Path, server_id: str) -> dict[str, Any] | None:
    for server in load_servers(path):
        if server.get("id") == server_id:
            return server
    return None


def new_server_id() -> str:
    return str(uuid.uuid4())
