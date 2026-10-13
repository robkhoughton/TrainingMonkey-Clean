# activate_user_account / deactivate_user_account send broken SQL

Status: resolved
Type: bug
Origin: follow-up to a9a3ce1, 2026-10-12

`app/user_account_manager.py` `activate_user_account` and `deactivate_user_account` both run:

```sql
UPDATE user_settings SET %s = %s WHERE id = %s
```

That binds a value where a column name belongs, so Postgres gets `SET 'active' = ...` and rejects it with a syntax error. `deactivate_user_account` also passes 4 params for 3 placeholders. Both catch `Exception` and return False, so the failure is silent. `test_user_account_manager.py` passes only because it mocks `execute_query` and never inspects the SQL.

Callers: `/api/user/activate-account` (strava_app.py ~9221) for activate. Deactivate has no caller in app code. No frontend, template, script, or Cloud Scheduler job calls `/api/user/activate-account`.

**Decision needed:** this belongs to the dead registration subsystem (see 03). If 03 resolves to delete, these go with it. If any of it is kept, fix the SQL to name the columns (`account_status`, `updated_at`, plus a reason column if one exists) and add a test that asserts on the SQL text.

## Comments

**2026-10-12 — resolved: deleted with the subsystem (see 03).**
