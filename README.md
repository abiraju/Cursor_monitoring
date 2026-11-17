# InfraMonitor

Local demo only — Flask UI for Linux server monitoring (CPU, memory, network, ports).

**CI:** GitHub Actions runs `pytest` (+ light `ruff` lint) on push/PR. **No remote deploy** — run locally where Cursor is running.

## Auth

| Item | Value |
|------|--------|
| Username | `admin` |
| Password (demo) | `admin123` |
| Storage | Hashed with Werkzeug (not plaintext) |

Flow: **sign in** → Overview → add/edit servers → detail metrics → **sign out**.  
CSRF tokens protect login and mutating forms. Session cookie is HttpOnly + SameSite=Lax.  
If you see **CSRF session token is missing**, hard-refresh `/login` and allow cookies for `127.0.0.1` (often caused by an app restart mid-login).

Do **not** commit real SSH passwords. `data/` is gitignored.

## Run

```bash
cd /home/jumpuser32/Desktop/Cursor_Monitoring_Application
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5600**

Optional: `export SECRET_KEY=your-local-secret` (otherwise a key is kept in `data/.secret_key`, gitignored).

## Usage

1. Sign in as `admin`
2. **Add server**
   - **Local:** check “Monitor this machine” (no SSH)
   - **Remote:** IP/hostname + SSH username/password (Linux host reachable from this machine)
3. Overview shows high-level metrics (auto-refresh **8s**)
4. **Details** shows CPU %, memory used/total, network counters, listening ports
5. Edit / Delete from overview (delete asks for confirm)

### Metrics

| Metric | Meaning |
|--------|---------|
| CPU | Usage percent |
| Memory | Used / total GB and percent |
| Network | Cumulative bytes/packets sent & received |
| Ports | Listening sockets (may be empty if OS denies access) |

### Remote SSH troubleshooting

- Timeout / unreachable: check IP, firewall, SSH service
- Authentication failed: verify user/password (password auth must be enabled)
- Errors render as text only (Jinja escapes them)

Server inventory is stored locally in `data/servers.json` (not committed).

## Tests

```bash
source .venv/bin/activate
pytest
```

| File | Coverage |
|------|----------|
| `tests/test_auth.py` | Login, hash storage, logout, redirects |
| `tests/test_servers.py` | Add/edit/delete, local vs remote validation, no password echo |
| `tests/test_metrics.py` | Local `psutil` helpers + mocked SSH (no live hosts) |

## CI

`.github/workflows/ci.yml` installs deps, runs `pytest`, and a light `ruff` lint. Deploy stays local only.
