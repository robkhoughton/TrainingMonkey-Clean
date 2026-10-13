# Registration session/status subsystem has no clients

Status: resolved
Type: task
Origin: follow-up to a9a3ce1; verified 2026-10-12

With `/signup` gone, nothing calls the following routes. Checked: `frontend/src`, `app/templates`, `scripts/`, and Cloud Scheduler (which has only the 4 cron jobs).

- `/api/user/account-status`, `/api/user/activate-account`, `/api/user/update-onboarding`, `/api/user/complete-onboarding`
- `/api/registration/*` (status, track-*, create/validate/resume/complete/extend-session, user-sessions)
- `/api/admin/pending-registrations`, `/api/admin/cleanup-expired-registrations`, `/api/admin/registration-summary`, `/api/admin/registration-status/<id>`, `/api/admin/cleanup-registrations-with-tracking`, `/api/admin/session-analytics`, `/api/admin/cleanup-expired-sessions`, `/api/admin/invalidate-session`

Modules reachable only through those routes:
- `registration_session_manager.py`: `_get_resume_url` still builds `/signup/resume/...`, `/email-verification/...` and `/strava-connect/...` links. None of those routes exist.
- `registration_status_tracker.py`
- `csrf_protection.py`: its only use left is `@csrf_protected` on `/api/registration/create-session`.
- `legal_validation.py`: its only importer was the deleted `registration_validation.py`.

Still live in `user_account_manager.py`: `complete_onboarding()`, called from `/welcome-stage1` (strava_app.py ~11850) in the Strava onboarding flow. Keep it.

**Decision needed:** delete the subsystem (routes, modules, tests), or keep it for a planned feature.

This decides whether test-setup-repair root cause A is worth doing. 33 of the 45 current test failures are in `test_csrf_protection.py`, `test_registration_session_manager.py` and `test_registration_status_tracker.py`, all of which test this dead code.

Side note: this means no live state-changing route has app-level CSRF protection. That's a separate question; don't solve it by reviving this module.

## Comments

**2026-10-12 — resolved: deleted.** Removed the 25 routes listed above, `registration_session_manager.py`, `registration_status_tracker.py`, `csrf_protection.py` and `legal_validation.py`, plus their 4 test files. `user_account_manager.py` is down to `complete_onboarding()`. Suite went from 45 failed / 327 passed to 12 failed / 255 passed, with no new failures. The connection probe shows 0 tests opening a DB connection; the 3 that remain happen outside any test body (`strava_app` import-time pool init and `log_api_request_async`).
