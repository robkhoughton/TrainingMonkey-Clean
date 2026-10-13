# 02 — Block database access from the test suite with a top-level conftest

Status: resolved
Source: `../prompt.md` item 2
Baseline: 0 failures. Hazard only.

## Problem

`app/tests/` has no `conftest.py`. No test body opens a connection, but connection attempts still happen outside test bodies:

- importing `strava_app` runs `initialize_database_pool_on_startup()` (strava_app.py ~195), which reaches `db_connection_manager.initialize_pool` → `psycopg2.pool.ThreadedConnectionPool`
- `log_api_request_async` (strava_app.py ~167), an after-request hook, writes `api_logs` from a background thread via `db_utils.execute_query` → `psycopg2.connect`

They fail today only because `DATABASE_URL` points nowhere. With the Cloud SQL proxy up and a real `DATABASE_URL` in the environment they reach production. There is no test database.

## What to do

Add `app/tests/conftest.py` that, **at module level** (not an autouse fixture), replaces `psycopg2.connect`, `psycopg2.pool.SimpleConnectionPool` and `psycopg2.pool.ThreadedConnectionPool` with stubs raising a clearly named error, and sets a dummy `DATABASE_URL` so the suite runs without the env prefix.

## Acceptance

- A probe at the driver level records zero connection attempts, including at import time and from background threads.
- Suite counts unchanged by this ticket.

## Answer

Added `app/tests/conftest.py`. At module level it replaces `psycopg2.connect`, `psycopg2.pool.SimpleConnectionPool` and `psycopg2.pool.ThreadedConnectionPool` with stubs that raise `DatabaseAccessBlockedInTests`, and it overwrites `DATABASE_URL` with a dummy `.invalid` URL, so a real URL in the environment never reaches app code.

Probe: a pytest plugin loaded with `-p` before conftest, which wraps `psycopg2._connect` (the C-driver entry point that `connect` and every pool reach).
- Before: 3 driver-level attempts, all at collection/import, none in a test body. 1× `ThreadedConnectionPool` from `strava_app` import (`initialize_database_pool_on_startup`, strava_app.py:224 → :194) and 2× `psycopg2.connect` from `log_request_end` → `log_api_request_async` (strava_app.py:141 → :166).
- After: **0 driver-level attempts**, both with `DATABASE_URL` unset and with the env prefix. A direct check confirms the guard is what fires at both sites ("Failed to initialize connection pool: psycopg2.pool.ThreadedConnectionPool() called during tests…", "Failed to log API request to database: psycopg2.connect() called during tests…").
- Counts unchanged: 1 failed / 250 passed. Runtime fell from ~14 s to ~1.7 s because nothing waits on connection timeouts now.

Correction to the premise: `log_api_request_async` is **not** threaded. Despite its name, the `log_request_end` after-request hook calls it synchronously on the request thread. The 2 attempts come from `tests/test_with_context.py`, a script with no test functions that drives `app.test_client()` at module level during collection. The guard covers it either way.
