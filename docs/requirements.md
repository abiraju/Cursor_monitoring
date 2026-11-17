# PRD: Demo Linux Server Monitoring

## 1. Overview

Small local demo app for internal L1/L2/L3 and app teams to view live Linux server metrics without SSH-ing into each host.

**Scope:** Demo only. Run on the same machine as Cursor. Keep setup and steps minimal.

## 2. Problem

Today, checking real-time CPU, memory, network, and port usage requires logging into each server.

## 3. Users

| Role | Access |
|------|--------|
| `admin` | Only user. Sign in, view metrics, add/edit/remove servers. |

No other user accounts.

## 4. Goals / Done criteria

- Sign in as `admin`
- Add one or more Linux servers (or monitor the local host)
- See live CPU, memory, network, and port usage
- Overview of all servers + per-server detail page
- Runs locally with Python + Flask

## 5. Core features

### 5.1 Auth

- Single user: username `admin`
- Password stored as a hash (not plain text)
- Fixed demo credentials (document in README; e.g. `admin` / hashed `admin123`)
- Unauthenticated users redirected to sign-in

### 5.2 Server management

- Add Linux servers with:
  - Display name (optional)
  - IP or hostname
  - SSH username
  - SSH password
- Support **local host** monitoring without SSH (run metrics on the machine where the app runs)
- Edit and delete servers (admin only)
- Metrics UI is read-only; only server CRUD uses edit controls

### 5.3 Metrics (real-time)

Collect and show only:

| Metric | Notes |
|--------|--------|
| CPU | Usage % |
| Memory | Used / total (and %) |
| Network | Basic throughput or interface stats |
| Ports | Listening / in-use ports |

No disk, process lists, history, or alerting in this demo.

### 5.4 UI

- Attractive, simple Flask UI
- **Overview page:** all monitored servers with high-level status/metrics
- **Detail page:** one server’s CPU, memory, network, ports
- **Auto-refresh** on overview and detail (e.g. every 5–10 seconds)
- Read-only for metrics; edit buttons only for server add/edit/delete

## 6. Tech stack

- Python 3
- Flask (backend + UI templates/static)
- Password hashing (e.g. Werkzeug)
- SSH client library for remote hosts (e.g. Paramiko)
- Local metrics via OS APIs (e.g. `psutil`) when target is local

## 7. Non-goals

- Multi-user / RBAC
- Historical charts, alerts, notifications
- Windows/non-Linux targets
- Production hardening, HTTPS, or cloud deploy
- Agent installed on remote servers (SSH on demand is enough)

## 8. Local run (minimal)

1. Create venv, install dependencies from `requirements.txt`
2. Set or use default hashed `admin` password
3. Run on **port 5600**: `python app.py` (or `flask run --port 5600`)
4. Open `http://127.0.0.1:5600` → sign in → add local and/or remote Linux servers → view overview/detail

## 9. Acceptance checklist

- [x] Login works only for `admin` with hashed password
- [x] Can add server (IP/hostname + SSH user/password) and edit/delete it
- [x] Can monitor local host without SSH
- [x] Overview lists all servers
- [x] Detail page shows CPU, memory, network, ports
- [x] Pages auto-refresh
- [x] App runs locally with Flask
- [x] CSRF on forms; CI via GitHub Actions (test/lint only, local deploy)
