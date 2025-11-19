# Database Access Guide for AI Assistant

## 🎯 Overview

The AI assistant can now work directly with the TrainingMonkey database using secure credential loading. This guide documents the approved methods and best practices.

## 🔐 Security Model

### Credentials Storage
- **Location**: `.env` file in project root (gitignored, never in version control)
- **Format**: `DATABASE_URL=postgresql://appuser:PASSWORD@35.223.144.85:5432/train-d`
- **Loading**: Always use `app/db_credentials_loader.py` module

### Access Principles
1. ✅ Credentials loaded from `.env` file at runtime
2. ✅ No credentials in code files or version control
3. ✅ AI can execute database operations using approved methods
4. ✅ All operations logged and auditable
5. ✅ Production credentials remain in Google Cloud Secret Manager

## 📋 Approved Database Operations

### 1. Schema Migrations

**When to Use**: Adding/modifying database schema

```python
# File: app/add_new_column_migration.py
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
import db_utils

def run_migration():
    if not set_database_url():
        print("ERROR: Could not load DATABASE_URL")
        return False
    
    try:
        db_utils.execute_query(
            "ALTER TABLE activities ADD COLUMN IF NOT EXISTS new_field TEXT"
        )
        print("✓ Migration successful")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
```

**Run**: `python app/add_new_column_migration.py`

### 2. Data Queries

**When to Use**: Reading data, verifying state, debugging

```python
# Quick script or interactive use
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Count users
result = db_utils.execute_query(
    "SELECT COUNT(*) as count FROM user_settings",
    fetch=True
)
print(f"Total users: {result[0]['count']}")

# Get specific user
user = db_utils.execute_query(
    "SELECT email, account_status FROM user_settings WHERE id = %s",
    (user_id,),
    fetch=True
)
```

### 3. Data Updates

**When to Use**: Fixing data issues, bulk updates

```python
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Example: Fix invalid dates
db_utils.execute_query(
    "UPDATE activities SET date = %s WHERE date = %s",
    ('2025-11-19', '2025-11-32')
)
```

### 4. Data Inspection

**When to Use**: Debugging, understanding schema

```python
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Check table structure
columns = db_utils.execute_query("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'activities'
    ORDER BY ordinal_position
""", fetch=True)

for col in columns:
    print(f"{col['column_name']}: {col['data_type']}")
```

## 🚫 Prohibited Operations

### Never Do These:

❌ **Hardcode Credentials**
```python
# WRONG
os.environ['DATABASE_URL'] = 'postgresql://user:pass@...'
```

❌ **Modify Production Schema in Application Code**
```python
# WRONG - Don't put schema changes in strava_app.py or similar
def setup_database():
    execute_query("ALTER TABLE activities ADD COLUMN ...")
```

❌ **Commit Credentials**
```python
# WRONG - Never commit .env or config with credentials
# These should be in .gitignore
```

❌ **Run Destructive Operations Without Confirmation**
```python
# WRONG - Always confirm before:
# - DROP TABLE
# - DELETE FROM without WHERE
# - TRUNCATE
# - UPDATE without WHERE
```

## 📊 Common Use Cases

### Use Case 1: Add New Column

```python
# File: app/add_feature_column.py
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Add column
db_utils.execute_query(
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS feature_flag BOOLEAN DEFAULT FALSE"
)

# Verify
result = db_utils.execute_query("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'activities' AND column_name = 'feature_flag'
""", fetch=True)

print(f"✓ Column exists: {len(result) > 0}")
```

### Use Case 2: Verify Data After Code Change

```python
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Check if new field is being populated
count = db_utils.execute_query("""
    SELECT COUNT(*) as count 
    FROM activities 
    WHERE start_time IS NOT NULL
""", fetch=True)

print(f"Activities with start_time: {count[0]['count']}")
```

### Use Case 3: Debug User Issue

```python
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

# Get user's recent activities
activities = db_utils.execute_query("""
    SELECT date, name, type, total_load_miles 
    FROM activities 
    WHERE user_id = %s 
    ORDER BY date DESC 
    LIMIT 10
""", (user_id,), fetch=True)

for act in activities:
    print(f"{act['date']}: {act['name']} - {act['total_load_miles']} miles")
```

## 🔄 Workflow Examples

### Adding a Feature with Database Changes

1. **Plan Schema Change**
   - Document what columns/tables needed
   - Create SQL in markdown doc first

2. **Create Migration Script**
   - Use `db_credentials_loader` template
   - Add verification queries
   - Test locally

3. **Update Backend Code**
   - Modify data models
   - Update queries to use new fields
   - Add to API responses if needed

4. **Update Frontend**
   - Add to TypeScript interfaces
   - Display new data

5. **Deploy**
   - Migration runs automatically
   - Backend deployed
   - Frontend deployed

### Debugging Production Issue

1. **Query Database State**
   ```python
   from db_credentials_loader import set_database_url
   import db_utils
   set_database_url()
   
   # Check the issue
   result = db_utils.execute_query("SELECT ...", fetch=True)
   ```

2. **Identify Root Cause**
   - Analyze query results
   - Check related records
   - Verify assumptions

3. **Fix if Needed**
   - Create migration script if schema issue
   - Update code if logic issue
   - Document findings

## 📚 Best Practices

### ✅ Do These:

1. **Always Load Credentials Securely**
   ```python
   from db_credentials_loader import set_database_url
   set_database_url()
   ```

2. **Use Parameterized Queries**
   ```python
   db_utils.execute_query(
       "SELECT * FROM activities WHERE user_id = %s",
       (user_id,)
   )
   ```

3. **Verify Before Destructive Operations**
   ```python
   # Check count first
   count = db_utils.execute_query("SELECT COUNT(*) FROM ...", fetch=True)
   print(f"Will affect {count[0]['count']} rows")
   # Then update
   ```

4. **Log Operations**
   ```python
   print(f"Running migration: ALTER TABLE ...")
   result = db_utils.execute_query("ALTER TABLE ...")
   print("✓ Migration complete")
   ```

5. **Create Reusable Migration Scripts**
   - Save as `app/migration_name.py`
   - Include verification
   - Document in markdown

### 🎯 Performance Tips

1. **Use LIMIT for exploration**
   ```python
   db_utils.execute_query("SELECT * FROM activities LIMIT 10", fetch=True)
   ```

2. **Index consideration**
   ```python
   # Add indexes for frequently queried columns
   db_utils.execute_query(
       "CREATE INDEX IF NOT EXISTS idx_activities_user_date ON activities(user_id, date)"
   )
   ```

3. **Batch operations**
   ```python
   # Better than row-by-row
   db_utils.execute_query("UPDATE activities SET ... WHERE id IN (%s)", (ids,))
   ```

## 🛠️ Troubleshooting

### Issue: "DATABASE_URL not found"
**Solution**: Ensure `.env` file exists in project root with valid DATABASE_URL

### Issue: "Permission denied"
**Solution**: Check database user has required permissions

### Issue: "Connection timeout"
**Solution**: Check network connection, database server status

### Issue: "Column does not exist"
**Solution**: Run migration first, then update code

## 🔗 Related Files

- `app/db_credentials_loader.py` - Credential loading module
- `app/db_utils.py` - Database utility functions
- `app/run_migration.py` - Example migration script
- `.cursorrules` - Project database rules
- `.env` - Credentials (not in version control)

## 📞 Summary

**AI Assistant can now:**
- ✅ Run database migrations
- ✅ Query data for debugging
- ✅ Verify schema changes
- ✅ Inspect database state
- ✅ Execute read/write operations

**Always remember:**
- 🔐 Use `db_credentials_loader` for secure access
- 📝 Create migration scripts for schema changes
- ✅ Use parameterized queries
- 🚫 Never hardcode credentials
- 📊 Log and verify operations

This enables faster development while maintaining security and auditability!


