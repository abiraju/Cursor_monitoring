# TODO — Demo Linux Server Monitoring

Small AI-assisted increments. Demo only; run locally on port **5600**.  
Reference: [requirements.md](./requirements.md)

---

## Phase 0 — Project init + basic UI

- [x] **0.1** Initialize project layout (`app.py`, `templates/`, `static/`, `requirements.txt`, `.gitignore`)
  - Security: add `.gitignore` for `.venv/`, `data/`, `__pycache__/`, `.env`, secrets
  - Docs: short `README.md` with project name and “local demo only”
- [x] **0.2** Minimal Flask app that binds to `127.0.0.1:5600` and serves a home page shell
  - Security: do not enable debug in committed defaults if avoidable; no secret keys in git
  - Docs: README “Run” section (venv → pip → `python app.py` → open `:5600`)
- [x] **0.3** Basic UI: layout (nav/header), overview placeholder, simple CSS
  - Security: no inline user-controlled HTML; static assets only from `/static`
  - Docs: note UI pages in README (Overview placeholder)

---

## Phase 1 — Sign-in + unit tests

- [x] **1.1** Add single-user sign-in form (username + password) and session cookie
  - Security: HttpOnly session cookie; `SECRET_KEY` from env or generated locally (not committed); redirect unauthenticated users to login
  - Docs: document demo user `admin` in README (password shown only as demo credential)
- [x] **1.2** Store password as hash only (Werkzeug); verify on login; reject non-admin
  - Security: never log or flash the raw password; constant-time hash check via Werkzeug
  - Docs: note in README that password is hashed at rest in app config/code
- [x] **1.3** Logout route + protect all app routes with login required
  - Security: clear session on logout; CSRF later for mutating forms (Phase 2+)
  - Docs: update README auth flow (sign in → overview → sign out)
- [x] **1.4** Unit tests for auth (valid login, bad password, logout, protected redirect)
  - Security: tests must not assert plaintext password storage
  - Docs: README “Tests” — `pytest` one-liner
- [x] **1.5** Wire `pytest` + Flask test client; keep tests fast and local-only
  - Security: use test `SECRET_KEY`; isolate test data from real `data/`
  - Docs: list test files under `tests/` in README

---

## Phase 2 — Server inventory (CRUD) + security/docs

- [x] **2.1** Persist servers in local JSON (or tiny DB file) under `data/` (gitignored)
  - Security: gitignore `data/`; never commit SSH passwords in sample data
  - Docs: describe data file location and that it is local-only
- [x] **2.2** Add-server form: name, IP/hostname, SSH user, SSH password, “local host” flag
  - Security: require login; do not echo password back in HTML value on edit (blank = keep); mask in UI
  - Docs: how to add **local** (checkbox, no SSH) vs **remote** (IP + SSH)
- [x] **2.3** Edit + delete server (admin session only); confirm delete
  - Security: POST for delete; validate server id exists; no IDOR without session (single user still enforce login)
  - Docs: edit/delete steps in README
- [x] **2.4** Unit tests for add/edit/delete and local vs remote field validation
  - Security: ensure SSH password not present in GET edit response HTML
  - Docs: mention CRUD tests in README Tests section

---

## Phase 3 — Local metrics (read-only UI)

- [x] **3.1** Collect local CPU + memory via `psutil`
  - Security: read-only metrics APIs; no shell=`True` for local collection
  - Docs: metrics meaning (CPU %, mem used/total)
- [x] **3.2** Collect local network counters + listening ports
  - Security: handle `AccessDenied` on ports gracefully; do not crash UI
  - Docs: note port list may be limited by OS permissions
- [x] **3.3** Overview cards: show high-level metrics for each server (local path first)
  - Security: metrics display is read-only (no edit of metric values)
  - Docs: screenshot or short description of overview
- [x] **3.4** Detail page for one server (CPU, memory, network, ports)
  - Security: only show servers from persisted list; 404/redirect if missing
  - Docs: detail page fields listed in README
- [x] **3.5** Auto-refresh overview + detail (meta refresh or light JS, ~8s)
  - Security: refresh must not leak credentials in URL query params
  - Docs: document refresh interval
- [x] **3.6** Unit tests for local metrics helpers (mock `psutil` where useful)
  - Security: tests must not require real SSH
  - Docs: how to run metrics unit tests

---

## Phase 4 — Remote Linux via SSH

- [x] **4.1** SSH collect helper (Paramiko): CPU, memory, network, ports
  - Security: disable agent/key auto-use unless needed; set connect timeouts; do not log SSH password
  - Docs: remote prerequisites (Linux, SSH password auth reachable from this host)
- [x] **4.2** Wire remote servers on overview/detail; show clear error if SSH fails
  - Security: sanitize/escape error strings in templates (Jinja auto-escape on)
  - Docs: troubleshooting SSH failures (timeout, auth, host unreachable)
- [x] **4.3** Unit tests with mocked SSH (success + auth failure)
  - Security: fixtures use fake credentials only
  - Docs: note remote tests are mocked (no live hosts in CI)

---

## Phase 5 — Hardening polish (demo-scale)

- [x] **5.1** CSRF protection on login + mutating forms (Flask-WTF or equivalent)
  - Security: CSRF tokens on POST; same-site session cookie if easy
  - Docs: note CSRF enabled for forms
- [x] **5.2** Flash messages without leaking secrets; consistent error handling
  - Security: generic login failure message (“Invalid username or password”)
  - Docs: update acceptance checklist in requirements if needed
- [x] **5.3** Final README pass: credentials, port 5600, local vs remote, tests
  - Security: remind not to commit real SSH passwords
  - Docs: keep instructions minimal (venv → install → run → browse)

---

## Phase 6 — CI/CD (GitHub Actions)

- [x] **6.1** Add `.github/workflows/ci.yml`: install deps, run `pytest` on push/PR
  - Security: no secrets in workflow; use dummy env `SECRET_KEY` for tests
  - Docs: badge or one-line “CI runs pytest on PR” in README
- [x] **6.2** Pin/cache pip in Actions; fail on test failure
  - Security: Actions runs on ubuntu-latest with checkout of this repo only
  - Docs: minimal “CI” subsection (what it runs; deploy stays local)
- [x] **6.3** Optional: lint job (`ruff` or `flake8`) — keep light for demo
  - Security: no publish/deploy credentials in CI (local run only)
  - Docs: state clearly — **no remote deploy**; CI = test/lint only

---

## Definition of done (demo)

- [x] Login as `admin` with hashed password
- [x] Add/edit/delete servers; local host without SSH
- [x] Overview + detail show CPU, memory, network, ports
- [x] Auto-refresh works
- [x] Unit tests + GitHub Actions CI green
- [x] README documents run on `http://127.0.0.1:5600`
