# 03 — `get_centralized_credentials()` skips the env-var fallback on a malformed config

Status: resolved
Source: `../prompt.md` item 3
Failing test: `app/tests/test_oauth_centralized.py::TestCentralizedOAuth::test_config_file_malformed`

## Behaviour (verified 2026-10-12)

`enhanced_token_management.get_centralized_credentials()` (line 770) wraps the config read *and* the env-var fallback in one `try`. A malformed `strava_config.json` makes `json.load` raise `JSONDecodeError`; the `except` at line 803 returns `(None, None)` and the env-var fallback at lines 793–798 never runs. The test expects the fallback, so the test describes the intended contract and the code breaks it.

## Callers

- Module-level `get_centralized_credentials()`: **no callers outside tests** (only `tests/test_oauth_centralized.py`, 5 call sites). The other grep hits are the differently named `get_centralized_credentials_status`.
- **The same flaw is in live code.** `SimpleTokenManager.get_centralized_strava_credentials()` (line 25) has the identical single-`try` shape (except at line 57). It is called by `get_centralized_credentials_status()` (line 83) and by the token-refresh path (line 317).

## Exposure today

Latent. `app/Dockerfile.strava` ships `COPY *.json .`, and there is no `app/strava_config.json` in the working tree (only `app/tests/strava_config.json`), so production has no config file. `os.path.exists` is false and the env vars are read directly. The bug only bites if someone drops a malformed `strava_config.json` into `app/`: every token refresh would then return "no credentials" even with valid env vars set.

## Recommendation

Do both, as one change:

1. **Delete** the module-level `get_centralized_credentials()` and its tests in `test_oauth_centralized.py`. It is a dead duplicate of the method; fixing it only keeps two copies of the logic alive.
2. **Fix the root cause in the live method** `SimpleTokenManager.get_centralized_strava_credentials()`: narrow the `try` to the config-file read (`OSError`, `json.JSONDecodeError`), log the malformed file as an error, and fall through to the env-var lookup. Move the malformed-config test onto the method, unchanged in what it asserts.

## Answer

Approved by Rob on 2026-10-12 as a follow-up to the test-only pass, and implemented as recommended:

- Moved 4 tests from the dead function onto `SimpleTokenManager(user_id=1).get_centralized_strava_credentials()`, with the same assertions: file_not_found, no_credentials, malformed, missing_credentials. Dropped the success-path test, which duplicated `test_simple_token_manager_centralized_credentials`. Once moved, the malformed test failed against the live method, confirming the bug was in production code.
- Fixed the root cause in the method. Only the file read is guarded now (`OSError`, `ValueError`, which covers `JSONDecodeError`), and a config that parses to something other than a JSON object is logged and skipped. In every case the method falls through to the env-var lookup. Checked by hand: `[1,2]`, `{"invalid": json}` and an empty file all return the env credentials.
- Deleted the module-level `get_centralized_credentials()`. No callers remain.

Suite: 1 failed / 250 passed → 0 failed / 250 passed.
