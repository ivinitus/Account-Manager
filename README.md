# Account Manager API

A lightweight Flask-based micro-service for importing, distributing and maintaining customer account credentials. The service uses an on-disk SQLite database with a small connection-pool, background maintenance workers and an optional system-tray icon when run on a desktop OS.

---

## Features

* REST API built with **Flask**  
* Connection pooling with concurrent friendly SQLite **WAL** mode  
* Batch inserts / updates for high-volume imports  
* Small in-memory cache for the *last served* account  
* Background workers that
  * demote `member` accounts to `3 days old` after 3 days
  * promote `3 days old` accounts to `former` after 30 days
  * permanently delete `former` accounts after 120 days  
* Optional system-tray icon (requires Pillow + pystray)  
* Packagable with **PyInstaller** – the database will be placed next to the generated executable.

---

## Project layout

```
.
├── run.py                    # Application entry-point
└── account_manager/
    ├── __init__.py           # App factory (create_app)
    ├── database.py           # Connection pool + schema helpers
    ├── routes.py             # All Flask endpoints (registered as blueprint)
    ├── tasks.py              # Background maintenance threads
    ├── tray.py               # Optional tray-icon utilities
    └── utils.py              # Cache + small helpers
```

---

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # create this to pin flask, flask-cors, pillow, pystray
```

On a server you may omit optional desktop dependencies:

```bash
pip install flask flask-cors
```

---

## Running locally

```bash
python run.py
```

The service starts on `http://127.0.0.1:5000` by default and prints optimisation info. Two daemon threads are spawned for background maintenance; another optional thread starts the tray icon if supported.

---

## REST API

### `POST /import_accounts`
Bulk-import an array of account objects. Duplicate `customerId`s are skipped.

Body JSON example:
```json
[
  {
    "customerId": "123",
    "email": "foo@example.com",
    "password": "bar",
    "marketplace": "us",
    "type": "member",
    "date": "2024-07-26 12:00:00"
  }
]
```
Returns number of accounts `inserted` / `skipped`.

---

### `GET /accounts?marketplace=<code>&type=<kind>`
Returns **one random** account matching `marketplace` and `type`.  
When an `rnb` account is served it is automatically upgraded to `member`.

---

### `GET /last_used_account`
Retrieve the account most recently returned by `/accounts` (fast – served from memory cache for 30 seconds, afterwards from DB).

---

### `POST /update_account_type`
Update an individual account status.

Body JSON:
```json
{
  "customer_id": "123",
  "new_type": "former"
}
```

---

### `GET /health`
Simple health-check returning `{ "status": "ok" }`.

---

## Background tasks
Task | Interval | Description
-----|----------|------------
`auto_demote_members` | hourly | Set `member` → `3 days old` after 3 days.
`cleanup_old_accounts` | every 6 h | Promote / delete historical accounts as described above.

Both tasks live in `account_manager.tasks` and are started from `run.py`.

---

## Packaging (PyInstaller)

```
pyinstaller --onefile run.py
```

At runtime the database `accounts.db` is created alongside the executable thanks to the path logic in `database.py`.

---

## Configuration notes

* **Threaded server** – `app.run(threaded=True)` enables concurrent requests with the built-in server. For production use a proper WSGI server (uWSGI, gunicorn, etc.).
* **Cache timeout** – adjustable in `account_manager.utils.CACHE_TIMEOUT`.
* **Pool size** – change default `max_connections` in `ConnectionPool` constructor if required.

---

## License
MIT Licence – do whatever you wish, no warranties.