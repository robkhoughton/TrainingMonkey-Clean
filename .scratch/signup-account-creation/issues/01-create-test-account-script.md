# create_test_account.py calls a deleted method

Status: resolved
Type: task
Origin: follow-up to a9a3ce1 (email signup path removed), 2026-10-12

`scripts/admin/create_test_account.py` calls `UserAccountManager.create_new_user_account` (line 78, deleted in a9a3ce1) and `activate_user_account` (line 103, deleted with the registration subsystem, see 03).

The script never worked before the deletion either:
- `sys.path.append(os.path.dirname(__file__))` adds `scripts/admin/`, not `app/`, so `from db_utils import ...` fails at import.
- `create_new_user_account` always returned failure (the NameError and the 12-column `VALUES (%s)` INSERT).

It creates email/password accounts, which no longer exist as a concept: all accounts come from Strava OAuth.

**Decision needed:** delete the script, or rewrite it to seed a Strava-shaped test user. Its docstring says it was built for beta-testing "the OAuth transition", which is long finished, so deleting it is the likely answer.

## Comments

**2026-10-12 — resolved: deleted.**
