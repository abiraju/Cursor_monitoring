"""Local + remote metrics tests (Phases 3–4). No live SSH in CI."""

from types import SimpleNamespace
from unittest.mock import patch

from monitor.metrics import (
    _parse_remote,
    collect_for_server,
    collect_local,
    collect_ssh,
)


def test_collect_local_returns_expected_keys():
    metrics = collect_local(cpu_interval=0)
    assert metrics["ok"] is True
    assert isinstance(metrics["cpu_percent"], (int, float))
    assert "used_gb" in metrics["memory"]
    assert "bytes_recv" in metrics["network"]
    assert isinstance(metrics["ports"], list)


def test_collect_local_handles_access_denied_on_ports():
    class AccessDenied(Exception):
        pass

    with patch("monitor.metrics.psutil") as mock_psutil:
        mock_psutil.AccessDenied = AccessDenied
        mock_psutil.cpu_percent.return_value = 12.5
        mock_psutil.virtual_memory.return_value = SimpleNamespace(
            used=1_000_000_000, total=4_000_000_000, percent=25.0
        )
        mock_psutil.net_io_counters.return_value = SimpleNamespace(
            bytes_sent=10, bytes_recv=20, packets_sent=1, packets_recv=2
        )
        mock_psutil.net_connections.side_effect = AccessDenied()

        metrics = collect_local(cpu_interval=0)
        assert metrics["ok"] is True
        assert metrics["ports"] == []


def test_parse_remote_basic():
    out_cpu = "15.5\n"
    out_mem = "Mem:  4294967296  1073741824  0\n"
    out_net = (
        "Inter-|   Receive                                                |  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets\n"
        "  eth0: 1000 1 0 0 0 0 0 0 2000 2 0 0 0 0 0 0\n"
        "    lo: 10 1 0 0 0 0 0 0 10 1 0 0 0 0 0 0\n"
    )
    out_ports = "LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"
    metrics = _parse_remote(out_cpu, out_mem, out_net, out_ports)
    assert metrics["ok"] is True
    assert metrics["cpu_percent"] == 15.5
    assert metrics["memory"]["percent"] == 25.0
    assert metrics["network"]["bytes_recv"] == 1000
    assert metrics["network"]["bytes_sent"] == 2000
    assert any(p["port"] == 22 for p in metrics["ports"])


def test_collect_ssh_auth_failure_mocked():
    with patch("monitor.metrics._ssh_run_all", side_effect=Exception("Authentication failed.")):
        metrics = collect_ssh("10.0.0.1", "user", "bad-pass")
        assert metrics["ok"] is False
        assert "Authentication failed" in metrics["error"]


def test_collect_ssh_success_mocked():
    with patch(
        "monitor.metrics._ssh_run_all",
        return_value=(
            "8.0\n",
            "Mem:  2000 1000 0\n",
            "eth0: 5 1 0 0 0 0 0 0 6 1 0 0 0 0 0 0\n",
            "LISTEN 0 128 127.0.0.1:5600 0.0.0.0:*\n",
        ),
    ):
        metrics = collect_ssh("10.0.0.1", "user", "fake")
        assert metrics["ok"] is True
        assert metrics["cpu_percent"] == 8.0


def test_collect_for_server_local_path():
    server = {"is_local": True, "host": "localhost"}
    with patch("monitor.metrics.collect_local", return_value={"ok": True, "cpu_percent": 1}) as mocked:
        result = collect_for_server(server)
        assert result["ok"] is True
        mocked.assert_called_once()


def test_collect_for_server_remote_path():
    server = {
        "is_local": False,
        "host": "10.0.0.9",
        "ssh_user": "u",
        "ssh_password": "p",
    }
    with patch("monitor.metrics.collect_ssh", return_value={"ok": False, "error": "down"}) as mocked:
        result = collect_for_server(server)
        assert result["error"] == "down"
        mocked.assert_called_once_with("10.0.0.9", "u", "p")
