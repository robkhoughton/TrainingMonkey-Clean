Fix the signup path in `app/user_account_manager.py` `_create_user_record`, test-first. Commit and deploy when green.

Evidence from the 2026-10-12 test run:
- `user_account_manager.py:116` calls `execute_query_for_onboarding`, which is never imported. It is defined at `db_utils.py:240`, but the module imports only `execute_query, get_db_connection` (line 23). The result is a NameError, which the broad `except` at line 134 catches and turns into `return None`.
- This code is reachable in production: `/signup` (strava_app.py ~9088) → `registration_validator.create_user_account` → `user_account_manager.create_new_user_account` → `_create_user_record`.
- A second defect hides behind the first. The INSERT names 12 columns but has `VALUES (%s)`, a single placeholder, against 12 params. Fixing the import alone just moves the failure to the SQL.

Do this:
1. Confirm the actual production behavior first. Is /signup live and linked from the site, or has it been superseded by Strava OAuth signup? Check the Cloud Run logs for "Database error creating user record". If the path is dead, propose deleting it instead of fixing it, and wait for my decision.
2. If it is live, write a failing test at the `create_new_user_account` seam with `execute_query_for_onboarding` mocked. It should assert that a user id is returned and that the SQL has 12 placeholders.
3. Fix the import and the VALUES clause. Then check whether the columns exist in `user_settings` (information_schema, via the proxy).
4. Look at whether the `except Exception: return None` at line 134 should hide programming errors like NameError. The root-cause rule in CLAUDE.md applies.
5. Also check `_log_legal_acceptances` and `_initialize_onboarding_progress` in the same file for the same class of bug.
