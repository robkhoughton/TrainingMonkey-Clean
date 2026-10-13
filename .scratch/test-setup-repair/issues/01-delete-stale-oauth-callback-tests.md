# 01 — Delete stale OAuth callback tests and audit the survivors

Status: resolved
Source: `../prompt.md` item 1
Baseline: 11 failures (8 in `test_oauth_callback_enhanced.py`, 3 in `test_oauth_callback_existing_enhanced.py`)

## What to do

1. Delete the 11 failing tests. They assert behaviour `/oauth-callback` (strava_app.py ~463) does not have: they patch `strava_app.UserAccountManager` / `strava_app.RegistrationStatusTracker` (neither exists), import `oauth_callback_signup` / `complete_strava_welcome` (removed), and expect a "Token exchange failed" flash, an `oauth_success.html` render and a `logger.info` call that the callback no longer produces. Don't re-target them.
2. Audit the 24 passing tests in the same files. Delete or convert the module-level functions that `return True/False` instead of asserting.
3. Report which survivors exercise the real `/oauth-callback` and which only mock it.

## Rule

A test goes green only because it is correct. Never weaken an assertion; never touch app code.

## Out of scope

New tests for the current callback. Record the coverage gap in the final report.

## Answer

Suite: 12 failed / 255 passed → 1 failed / 250 passed (−11 failures, −5 passing).

Deleted:
- 11 failing tests: `test_oauth_callback_enhanced.py` (error_handling, new_user_creation, fallback_creation, analytics_tracking, complete_strava_welcome_api, legal_compliance, error_recovery, enhanced_logging) and `test_oauth_callback_existing_enhanced.py` (analytics_tracking_existing_user, success_template_rendering, fallback_error_handling).
- 5 module-level `return True/False` functions, all passing whatever happened: `test_enhanced_oauth_callback_import`, `test_oauth_callback_components` (actually returned False: `oauth_callback_signup` is gone), `test_enhanced_existing_oauth_callback_import`, `test_oauth_callback_existing_components` (returned False: `track_page_view` does not exist in `strava_app`), `test_oauth_success_template` (returned False: wrong relative path). None was worth converting: the import checks are covered by every other test that imports `strava_app`, and the other two would assert names or templates the callback no longer uses.
- The two `__main__` runner blocks, which called the deleted functions.

Audit of the 19 survivors: **none exercises the real `/oauth-callback`.** None uses the Flask test client or calls `oauth_callback()`.
- 10 have empty bodies (`pass` under patches) and assert nothing: enhanced `missing_auth_code`, `configuration_error`, `token_exchange_success`, `existing_user_handling`, `strava_welcome_onboarding_route`; existing `error_handling_existing_user`, `missing_auth_code_existing_user`, `configuration_error_existing_user`, `token_exchange_success_existing_user`, `token_saving_existing_user`.
- 9 assert only on mocks or literals the test builds itself: enhanced `session_management`; existing `session_management_existing_user`, `enhanced_error_context`, `enhanced_logging`, `athlete_id_extraction`, `enhanced_token_structure`, `existing_activities_check`, `centralized_credentials_usage`, `template_data_preparation`.

Recommendation (not done, needs a decision): delete both files outright. They give zero coverage of the callback and report 19 green tests that test nothing.
