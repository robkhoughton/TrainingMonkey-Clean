Clean up the remaining broken tests in `app/tests` and make it impossible for the suite to reach the database. Use the mattpocock skills as follows:

1. `/mattpocock-skills:to-tickets`: break the work below into tickets in `.scratch/test-setup-repair/issues/`, one ticket per numbered item.
2. `/mattpocock-skills:implement`: work the tickets one at a time. After each one, re-run the full suite and report the count change.
3. `/mattpocock-skills:code-review`: review since the starting commit before committing. The diff should touch only `app/tests/` (plus `.scratch/`).

The tests are already red, so TDD's red→green loop doesn't apply. Hold each change to this rule instead: a test goes green only because the test is now correct. Never weaken an assertion, and never change app code. If a corrected test exposes a real app bug, stop and report it.

Baseline on 2026-10-12 (commit e3a486e): 12 failed, 255 passed. Run from `app/` with an unreachable database: `DATABASE_URL=postgresql://x:y@localhost:1/z python -m pytest tests -q -p no:cacheprovider`. The tests don't load `.env`, but `db_utils` raises at import if `DATABASE_URL` is unset.

## 1. Stale OAuth callback tests (11 failures)

`test_oauth_callback_enhanced.py` has 8 failures and `test_oauth_callback_existing_enhanced.py` has 3. They describe behavior the callback no longer has:
- They patch `strava_app.UserAccountManager` and `strava_app.RegistrationStatusTracker`. Neither name exists in `strava_app`, and `/oauth-callback` (strava_app.py ~463) never used them in its current form.
- They import `oauth_callback_signup` and `complete_strava_welcome`, both removed (see the comment at strava_app.py ~2903).
- They expect a flash of "Token exchange failed" (the callback now only logs that string; the user sees "Unable to connect to Strava. Please try again."), a `render_template('oauth_success.html', ...)` the callback no longer makes, and a `logger.info` call that doesn't happen.

Delete these 11 tests. Don't re-target them: no current code path matches what they assert.

The same two files have 24 passing tests. Audit them in the same ticket. Several module-level functions `return True/False` instead of asserting (pytest's `PytestReturnNotNoneWarning`), so they pass whatever happens. Delete or convert those. Report which of the remaining tests exercise the real `/oauth-callback` and which only mock it.

Out of scope: writing new tests for the current callback, which needs its own decision. Note the coverage gap in the final report.

## 2. DB guard in a top-level conftest (0 failures; prevents a hazard)

`app/tests/` has no `conftest.py`. A probe that wraps `psycopg2.connect` and the pool constructors shows no test body opens a connection today. Three connection attempts still happen outside test bodies:
- `strava_app` import: `initialize_database_pool_on_startup()` (strava_app.py ~195) → `db_connection_manager.initialize_pool`
- `log_api_request_async` (strava_app.py ~167): an after-request hook that writes from a background thread

They only fail today because `DATABASE_URL` points nowhere. If the Cloud SQL proxy is up and a real `DATABASE_URL` is in the environment, they reach PRODUCTION. There is no test database.

Add `app/tests/conftest.py` that blocks `psycopg2.connect`, `psycopg2.pool.SimpleConnectionPool` and `ThreadedConnectionPool` **at module level** (not in a per-test autouse fixture), so the block is in place before any test module imports `strava_app`. Make a blocked call raise a clearly named error. Also set a dummy `DATABASE_URL` there, so the suite runs without the env prefix.

Acceptance: re-run the probe and get zero connection attempts anywhere, including at import time and from background threads. The suite count must not change.

## 3. `test_oauth_centralized::test_config_file_malformed` (1 failure): report it, don't fix it

This exposes real app behavior. `enhanced_token_management.get_centralized_credentials()` (~770) wraps everything in one `try`. A malformed `strava_config.json` raises in `json.load`, the `except` returns `(None, None)`, and the env-var fallback never runs. The test expects the fallback.

`get_centralized_credentials` has no callers outside tests. Write this up as a ticket with a recommendation (delete the function and its tests, or fix the fallback). Leave the test failing.

## Finish with

Before/after failure counts per item, the remaining failures and their causes, the coverage gap from item 1, and a commit (tests only, so no deploy).
