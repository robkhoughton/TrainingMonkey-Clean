Fix the broken test setup in `app/tests` so the auth/registration tests actually exercise the code. Use the mattpocock skills as follows:

1. `/mattpocock-skills:to-tickets` — break the work below into tickets in `.scratch/test-setup-repair/`. One ticket per root cause, not per file.
2. `/mattpocock-skills:implement` — work the tickets one at a time. After each one, re-run the full suite and report the count change.
3. `/mattpocock-skills:code-review` — review since the starting commit before committing. The diff should touch only `app/tests/`.

TDD's red→green loop doesn't fit here, because the tests are already red. Hold each fix to this instead: a test goes green because the test is now correct, never by weakening the assertion or by changing app code. If a corrected test exposes a real app bug, stop and report it. Do not fix app code in this session.

Baseline on 2026-10-12 (commit 287fa0b): 58 failed, 357 passed. Run from `app/`: `python -m pytest tests -q -p no:cacheprovider`.

Root causes, verified last session:

A. Flask proxies patched outside a request (~33 failures): all of `test_csrf_protection.py` (22), most of `test_registration_session_manager.py` and `test_registration_status_tracker.py`.
- `@patch('csrf_protection.session')` / `patch('...request')` makes mock inspect the werkzeug LocalProxy (`_is_async_obj`), which raises "Working outside of request context" before the test body runs.
- Fix: stop mocking `session`/`request`. Use a real `Flask(__name__)` app with a `secret_key` and `app.test_request_context(...)` (headers, remote_addr, etc. passed in). Then assert on the real session contents. Put a shared fixture in `app/tests/conftest.py` (none exists yet).

B. Stale mock targets that let real DB queries through (8 tests). A probe on psycopg2.connect showed these are the only tests in the suite that open a connection.
- `test_registration_validation.py`: test_validate_email_valid / _already_exists / _unique / _database_error and test_create_user_account_success / _failure. These patch `registration_validation.execute_query`, but the uniqueness check moved to `email_validation.py` (`check_email_uniqueness`). Patch where the lookup actually happens.
- `test_registration_status_tracker.py`: test_start_registration_tracking_failure and test_track_onboarding_complete_failure. They mock `user_account_manager` but not `registration_status_tracker.execute_query` (lines ~466/489).
- WARNING: the proxy points at PRODUCTION, and there is no test DB. Never run these with the proxy up until they're fixed. `test_create_user_account_success` would INSERT test@example.com into live `user_settings`.
- Acceptance: re-run the connect probe (wrap psycopg2.connect and the pool constructors, record the nodeid). Zero tests may open a connection. Consider making this permanent: an autouse conftest fixture that makes psycopg2.connect raise during tests, so a stale mock fails loudly instead of quietly hitting the DB.

C. Patches on names that strava_app no longer imports (11): `test_oauth_callback_enhanced.py` (8) and `test_oauth_callback_existing_enhanced.py` (3) patch `strava_app.UserAccountManager` / `strava_app.RegistrationStatusTracker`. Find where the OAuth callback now gets these (grep the callback route) and patch there. If the callback no longer uses them at all, the tests are describing removed behavior. Report that rather than inventing a target.

Out of scope (leave failing; note them in the final report):
- `test_user_account_manager.py` failures: the real bug, `execute_query_for_onboarding` not imported plus a `VALUES (%s)` with 12 params, has its own session/prompt.
- Password-rule expectation drift (`test_password_generator`, two `test_validate_password_*`): needs a product decision on the current rules.
- Any app-code change, and pytest integration markers (deferred until a separate test database exists).

Finish with: before/after failure counts per root cause, the list of remaining failures with their causes, and a commit (tests only, so no deploy).
