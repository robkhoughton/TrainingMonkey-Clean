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

## Query Execution

Always use parameterized queries via `db_utils`:

```python
# Read operation
results = db_utils.execute_query(
    "SELECT * FROM activities WHERE user_id = %s AND date >= %s",
    (user_id, start_date),
    fetch=True
)

# Write operation
db_utils.execute_query(
    "INSERT INTO activities (user_id, name, date) VALUES (%s, %s, %s)",
    (user_id, name, activity_date)
)
```

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

## Common Mistakes to Avoid

- Using `?` instead of `%s` for placeholders
- Using `AUTOINCREMENT` instead of `SERIAL`
- Using `CURRENT_TIMESTAMP` instead of `NOW()`
- Hardcoding connection strings anywhere
- Running schema changes in application startup code
- Using `datetime.now()` when you need `datetime.now().date()`
