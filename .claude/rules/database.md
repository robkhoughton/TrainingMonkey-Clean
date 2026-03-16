---
paths: ["app/**/*.py", "scripts/**/*.py"]
---

# Database Standards (PostgreSQL)

## Syntax Requirements

**PostgreSQL ONLY** - This project uses PostgreSQL, not SQLite.

| Correct (PostgreSQL) | Wrong (SQLite) |
|---------------------|----------------|
| `%s` placeholder | `?` placeholder |
| `SERIAL PRIMARY KEY` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| `NOW()` | `CURRENT_TIMESTAMP` |
| `BOOLEAN` | `INTEGER` for booleans |
| `TEXT` | `VARCHAR` without limit |

## Database Connection — Cloud SQL Only

**There is no local database.** All environments (local dev, production) connect to Cloud SQL PostgreSQL (`train-monk-db-v3`, project `dev-ruler-460822-e8`, region `us-central1`).

### Production (Cloud Run)
Connects via Unix socket — no public IP, no authorized networks. Managed automatically by Cloud Run + Cloud SQL connector. DATABASE_URL is stored in Secret Manager (`database-url` secret, version 52+).

### Local Development
Requires the **Cloud SQL Auth Proxy** running before any DB work (migrations, scripts, local Flask):

```bash
scripts\start_sql_proxy.bat
```

Keep that window open. It tunnels `localhost:5432 → Cloud SQL via IAM`. `.env` points to `127.0.0.1:5432`.

The proxy binary is at `%USERPROFILE%\bin\cloud-sql-proxy.exe` (v2.15.2).

**0.0.0.0/0 has been removed from Cloud SQL authorized networks.** Direct public IP connections are blocked. The proxy is the only local access path.

## Credential Security

**Never hardcode DATABASE_URL or credentials in code.**

```python
# CORRECT - Always use this pattern
from db_credentials_loader import set_database_url
import db_utils

set_database_url()  # Loads from .env file
results = db_utils.execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch=True)
```

```python
# WRONG - Never do this
os.environ['DATABASE_URL'] = 'postgresql://user:pass@host/db'
```

For UI-only development with no DB needed, set `USE_MOCK_DB=true` in `.env`. See `CLAUDE.md` § Local Development for mock server setup.

## Query Execution

Four functions exist in `db_utils.py`. Use the right one:

| Function | When to use |
|---|---|
| `execute_query()` | Default for all application code — tries pool first, falls back to direct |
| `execute_query_direct()` | Sync operations where pool latency matters; explicit direct connection |
| `execute_query_for_onboarding()` | New user creation flows — isolated connection to avoid pool contention |
| `execute_query_for_sync()` | Strava sync operations — same as direct, labelled for clarity |

`execute_query()` is correct for the vast majority of cases. The pool auto-initializes on startup (`initialize_database_pool_on_startup()` in `strava_app.py`) and silently falls back to a direct connection if the pool is unavailable — so it is always safe.

```python
# Standard read
results = db_utils.execute_query(
    "SELECT * FROM activities WHERE user_id = %s AND date >= %s",
    (user_id, start_date),
    fetch=True
)

# Standard write
db_utils.execute_query(
    "INSERT INTO activities (user_id, name, date) VALUES (%s, %s, %s)",
    (user_id, name, activity_date)
)
```

### Connection Manager (advanced)

For code that needs explicit connection control, use the context manager from `db_connection_manager`:

```python
from db_connection_manager import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM activities WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
    conn.commit()
```

This pattern is used in auth, analytics, migrations, and chat modules. Prefer `execute_query()` unless you need transaction control across multiple statements.

## JSONB Storage

The `llm_recommendations.structured_output` column is JSONB. Python dicts must be serialized before insert:

```python
import json

# Writing a dict to a JSONB column
structured = {"assessment": {...}, "decision": {...}}
db_utils.execute_query(
    "UPDATE llm_recommendations SET structured_output = %s WHERE id = %s",
    (json.dumps(structured), rec_id)
)

# Reading back — psycopg2 returns JSONB as a Python dict automatically
result = db_utils.execute_query(
    "SELECT structured_output FROM llm_recommendations WHERE id = %s",
    (rec_id,), fetch=True
)
structured = result[0]['structured_output']  # already a dict, no json.loads() needed
```

Always use `ADD COLUMN IF NOT EXISTS ... JSONB` for new JSONB columns in migrations.

## Error Handling

```python
# Application code — let execute_query() handle logging; catch at the call site
try:
    results = db_utils.execute_query(query, params, fetch=True)
except Exception as e:
    logger.error(f"DB error for user {user_id}: {str(e)}", exc_info=True)
    return None  # or raise, depending on context

# Migrations — always rollback on failure
try:
    conn.commit()
    print("Migration complete")
except Exception as e:
    conn.rollback()
    raise  # let it surface — never silently swallow migration errors
```

`safe_execute_query()` in `db_utils.py` catches missing-table errors and triggers auto-initialization. Use it only for startup-time table checks, not general application queries.

## Schema Migrations

**Never modify schema in application code.** Create migration scripts in `scripts/migrations/`.

### Migration Script Template

```python
# scripts/migrations/add_new_column.py
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Check if column exists first
check_query = """
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'activities' AND column_name = 'new_field'
"""
result = db_utils.execute_query(check_query, fetch=True)

if not result:
    db_utils.execute_query("ALTER TABLE activities ADD COLUMN new_field TEXT")
    print("Column 'new_field' added successfully")
else:
    print("Column 'new_field' already exists")
```

### Direct psycopg2 for Complex Migrations

```python
from db_credentials_loader import set_database_url
import psycopg2
import os

set_database_url()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cursor = conn.cursor()

try:
    cursor.execute("BEGIN")
    cursor.execute("ALTER TABLE activities ADD COLUMN new_field TEXT")
    cursor.execute("UPDATE activities SET new_field = 'default' WHERE new_field IS NULL")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e
finally:
    cursor.close()
    conn.close()
```

## Date Handling

```python
# Date-only operations
from datetime import datetime
today = datetime.now().date()  # Returns date object, not datetime

# API format
date_string = today.strftime('%Y-%m-%d')  # '2025-01-15'

# Database storage - UTC timestamps
# PostgreSQL handles timezone conversion with TIMESTAMP WITH TIME ZONE
```

## Schema Discovery

Before writing queries, verify column names exist. The schema has evolved and some expected columns may not exist or may be in a different table.

```python
# Check a table's columns before querying
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'my_table'
    ORDER BY ordinal_position;
""")

# Check which tables have data (useful for debugging empty results)
cur.execute("""
    SELECT relname, n_live_tup
    FROM pg_stat_user_tables
    WHERE n_live_tup > 0
    ORDER BY n_live_tup DESC;
""")
```

## Key Schema Facts

**`user_settings` is the real user table — NOT `users`.**

The `users` table exists but is empty. All user data lives in `user_settings`:
- `id` — primary key (used as `user_id` in `activities`)
- `email` — user email (may be `strava_XXXXXXX@training-monkey.com` for OAuth-only users)
- `strava_athlete_id` — Strava athlete ID
- `primary_sport` — user's selected primary sport (e.g. `trail_running`, `cycling`, `running`)
- `created_at` — account creation timestamp
- `onboarding_completed_at` — when onboarding finished

**`activities` primary key is `activity_id`** (not `id`).

**Joining users to activities:**
```sql
SELECT us.email, a.type, a.date
FROM user_settings us
LEFT JOIN activities a ON a.user_id = us.id
WHERE us.created_at >= '2026-01-01'
```

## Common Mistakes to Avoid

- Using `?` instead of `%s` for placeholders
- Using `AUTOINCREMENT` instead of `SERIAL`
- Using `CURRENT_TIMESTAMP` instead of `NOW()`
- Hardcoding connection strings anywhere
- Running schema changes in application startup code
- Using `datetime.now()` when you need `datetime.now().date()`
- Querying the `users` table — it is empty; use `user_settings` instead
- Using `a.id` to count activities — the PK is `a.activity_id`
- Calling `json.loads()` on a JSONB column — psycopg2 deserializes it automatically
- Forgetting to start the SQL proxy before running local migrations or scripts
- Using `safe_execute_query()` for general application queries — it is for startup table checks only
