"""Collect CPU, memory, network, and port metrics locally or over SSH."""

from __future__ import annotations

import re
import socket
from typing import Any

import psutil

try:
    import paramiko
except ImportError:  # pragma: no cover
    paramiko = None


def _bytes_to_gb(n: float) -> float:
    return round(n / (1024**3), 2)


def collect_local(cpu_interval: float = 0.1) -> dict[str, Any]:
    """Local metrics via psutil only (no shell)."""
    cpu = psutil.cpu_percent(interval=cpu_interval)
    mem = psutil.virtual_memory()
    net = psutil.net_io_counters()
    ports: list[dict[str, Any]] = []
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.status == psutil.CONN_LISTEN and c.laddr:
                ports.append(
                    {
                        "proto": "tcp" if c.type == socket.SOCK_STREAM else "udp",
                        "address": c.laddr.ip,
                        "port": c.laddr.port,
                    }
                )
    except (psutil.AccessDenied, PermissionError):
        ports = []

    seen: set[tuple] = set()
    unique_ports: list[dict[str, Any]] = []
    for p in sorted(ports, key=lambda x: (x["port"], x["address"])):
        key = (p["proto"], p["address"], p["port"])
        if key not in seen:
            seen.add(key)
            unique_ports.append(p)

    return {
        "ok": True,
        "error": None,
        "cpu_percent": cpu,
        "memory": {
            "used_gb": _bytes_to_gb(mem.used),
            "total_gb": _bytes_to_gb(mem.total),
            "percent": mem.percent,
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
        "ports": unique_ports[:50],
    }


def _ssh_run_all(host: str, username: str, password: str, timeout: int = 8) -> tuple[str, str, str, str]:
    if paramiko is None:
        raise RuntimeError("paramiko is not installed")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )

        def run(cmd: str) -> str:
            _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            if err and not out:
                raise RuntimeError(err.strip())
            return out

        out_cpu = run(
            r"""top -bn1 | awk -F',' '/Cpu\(s\)/{for(i=1;i<=NF;i++) if($i ~ /id/){gsub(/[^0-9.]/,"",$i); print 100-$i; exit}}'"""
        )
        out_mem = run("free -b")
        out_net = run("cat /proc/net/dev")
        out_ports = run("ss -tln 2>/dev/null || netstat -tln 2>/dev/null")
        return out_cpu, out_mem, out_net, out_ports
    finally:
        client.close()


def _parse_remote(out_cpu: str, out_mem: str, out_net: str, out_ports: str) -> dict[str, Any]:
    cpu = 0.0
    m = re.search(r"([\d.]+)", out_cpu.strip())
    if m:
        cpu = float(m.group(1))

    mem_used = mem_total = 0
    mem_pct = 0.0
    for line in out_mem.splitlines():
        if line.lower().startswith("mem:"):
            parts = line.split()
            if len(parts) >= 3:
                mem_total = int(parts[1])
                mem_used = int(parts[2])
                if mem_total:
                    mem_pct = round(mem_used * 100 / mem_total, 1)
            break

    bytes_recv = bytes_sent = packets_recv = packets_sent = 0
    for line in out_net.splitlines():
        if ":" not in line or line.strip().startswith("Inter"):
            continue
        try:
            iface, rest = line.split(":", 1)
            cols = rest.split()
            if len(cols) >= 16 and iface.strip() != "lo":
                bytes_recv += int(cols[0])
                packets_recv += int(cols[1])
                bytes_sent += int(cols[8])
                packets_sent += int(cols[9])
        except (ValueError, IndexError):
            continue

    ports: list[dict[str, Any]] = []
    for line in out_ports.splitlines():
        match = re.search(r"([\d.:a-fA-F\[\]]+):(\d+)\s", line)
        if not match:
            match = re.search(r"([\d.:a-fA-F\[\]]+):(\d+)$", line.strip())
        if match:
            ports.append({"proto": "tcp", "address": match.group(1), "port": int(match.group(2))})

    seen: set[tuple] = set()
    unique_ports: list[dict[str, Any]] = []
    for p in sorted(ports, key=lambda x: x["port"]):
        key = (p["address"], p["port"])
        if key not in seen:
            seen.add(key)
            unique_ports.append(p)

    return {
        "ok": True,
        "error": None,
        "cpu_percent": cpu,
        "memory": {
            "used_gb": _bytes_to_gb(mem_used),
            "total_gb": _bytes_to_gb(mem_total),
            "percent": mem_pct,
        },
        "network": {
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "packets_sent": packets_sent,
            "packets_recv": packets_recv,
        },
        "ports": unique_ports[:50],
    }


def collect_ssh(host: str, username: str, password: str) -> dict[str, Any]:
    """Remote metrics over SSH. Password is never logged."""
    try:
        parsed = _parse_remote(*_ssh_run_all(host, username, password))
        return parsed
    except Exception as exc:  # noqa: BLE001 — surface failure to UI
        return {
            "ok": False,
            "error": str(exc),
            "cpu_percent": None,
            "memory": None,
            "network": None,
            "ports": [],
        }


def collect_for_server(server: dict[str, Any]) -> dict[str, Any]:
    if server.get("is_local"):
        try:
            return collect_local()
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": str(exc),
                "cpu_percent": None,
                "memory": None,
                "network": None,
                "ports": [],
            }
    return collect_ssh(
        server.get("host", ""),
        server.get("ssh_user", ""),
        server.get("ssh_password", ""),
    )
