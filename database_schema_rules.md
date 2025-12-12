# Database Schema Management Rules

## 🎯 **Core Principle**
**Direct PostgreSQL connection for local development. Use SQL Editor for one-time database operations.**

## 🗄️ **Database Platform**
**PostgreSQL Only**: This project uses PostgreSQL exclusively. Do not maintain SQLite compatibility.

## 📋 **Rules**

### ✅ **Use SQL Editor For:**
- **Schema Changes**: Adding/removing tables, columns, indexes
- **Data Migrations**: One-time data updates, transformations
- **Initial Setup**: Database initialization, seed data
- **Schema Validation**: Checking table structures, constraints
- **Performance Tuning**: Adding indexes, optimizing queries

### ❌ **Don't Use Code For:**
- **One-time schema operations** (unless dynamic/runtime)
- **Static database setup** that runs once
- **Schema validation** that could be done via SQL
- **Migration scripts** that should be in SQL files

### 🔄 **Exceptions (Use Code For):**
- **Runtime schema validation** (checking if columns exist during app startup)
- **Dynamic schema creation** (user-specific tables, etc.)
- **Multi-environment migrations** (dev/staging/prod differences)
- **Complex data transformations** that require business logic

## 🛠️ **Implementation Guidelines**

### **SQL Editor Usage:**
1. **Google Cloud SQL Console** for production database (PostgreSQL)
2. **pgAdmin** or **DBeaver** for PostgreSQL management
3. **Document all changes** in `docs/database_changes.md`

### **Direct Database Connection:**
1. **Local Development**: Connect directly to Google Cloud PostgreSQL
2. **Environment**: Use `DATABASE_URL` in `.env` file
3. **Instance**: `train-monk-db-v3` (35.223.144.85)
4. **Database**: `train-d` with user `appuser`

### **Connection Best Practices:**
1. **Use RealDictCursor**: Always use `RealDictCursor` for dictionary-like row access
2. **Context Manager**: Use `with get_db_connection() as conn:` for proper connection management
3. **Schema Verification**: Use `information_schema.columns` for PostgreSQL schema queries
4. **Error Handling**: Wrap database operations in try-catch blocks
5. **Connection Testing**: Create simple verification scripts for schema validation

### **PostgreSQL Syntax Requirements:**
- **Primary Keys**: Use `SERIAL PRIMARY KEY` (not `INTEGER PRIMARY KEY AUTOINCREMENT`)
- **Timestamps**: Use `DEFAULT NOW()` (not `DEFAULT CURRENT_TIMESTAMP`)
- **Data Types**: Use PostgreSQL-specific types (`SERIAL`, `JSONB`, etc.)
- **Indexes**: Use PostgreSQL index syntax and system tables for verification

### **PostgreSQL Schema Examples:**
```sql
-- ✅ Correct PostgreSQL syntax
CREATE TABLE IF NOT EXISTS example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ✅ Correct index creation
CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);

-- ✅ Correct verification queries
SELECT table_name FROM information_schema.tables WHERE table_name = 'example_table';
SELECT indexname FROM pg_indexes WHERE indexname LIKE 'idx_%';
```

### **Code Integration:**
```python
# ✅ Good: Runtime validation only (PostgreSQL with RealDictCursor)
def check_required_columns():
    """Check if required columns exist at runtime"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'user_settings'
                """)
                existing_columns = [row['column_name'] for row in cursor.fetchall()]
                missing_columns = set(REQUIRED_COLUMNS) - set(existing_columns)
                if missing_columns:
                    logger.error(f"Missing columns: {missing_columns}")
                    return False
                return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

# ✅ Good: Schema verification script pattern
def verify_database_schema():
    """Verify database schema for development"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'user_settings' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                print(f"user_settings table has {len(columns)} columns")
                for col in columns:
                    print(f"{col['column_name']:<30} {col['data_type']:<15}")
                return True
    except Exception as e:
        print(f"Schema verification failed: {e}")
        return False

# ❌ Bad: One-time schema changes in code
def ensure_goals_columns_exist():
    """Don't do this - use SQL Editor instead"""
    execute_query("ALTER TABLE user_settings ADD COLUMN goals_configured BOOLEAN")
```

## 📁 **File Organization**

### **SQL Files:**
- `app/*_schema.sql` - PostgreSQL table definitions, indexes
- `app/*_migration.sql` - One-time data migrations (PostgreSQL syntax)
- `docs/database_changes.md` - Change log with PostgreSQL examples

### **Code Files:**
- `db_utils.py` - Database utilities, connection management
- `models/` - Data models, ORM definitions
- `migrations/` - Runtime schema validation only

## 🔍 **PostgreSQL Schema Standards**

### **Required Syntax Standards:**
```sql
-- ✅ Correct PostgreSQL table creation
CREATE TABLE IF NOT EXISTS example_table (
    id SERIAL PRIMARY KEY,                    -- Not AUTOINCREMENT
    name VARCHAR(100) NOT NULL UNIQUE,
    data JSONB,                               -- PostgreSQL-specific type
    created_at TIMESTAMP DEFAULT NOW(),       -- Not CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ✅ Correct PostgreSQL indexes
CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);
CREATE INDEX IF NOT EXISTS idx_example_user_timestamp ON example_table(user_id, created_at);
```

### **Verification Queries (PostgreSQL):**
```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'example_table';

-- Check if columns exist (use with RealDictCursor)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'example_table'
ORDER BY ordinal_position;

-- Check if indexes exist
SELECT indexname FROM pg_indexes 
WHERE tablename = 'example_table';

-- Verify specific fields exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_settings' 
AND column_name IN ('age', 'training_experience', 'primary_sport');
```

### **Connection Testing Script Pattern:**
```python
#!/usr/bin/env python3
"""Database Schema Verification Script"""
import os
from dotenv import load_dotenv
load_dotenv()
from db_utils import get_db_connection

def verify_schema():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'user_settings' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                print(f"✅ user_settings table has {len(columns)} columns")
                for col in columns:
                    print(f"  {col['column_name']:<30} {col['data_type']:<15}")
                return True
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_schema()
```

## 📊 **Benefits**

### **Codebase Cleanliness:**
- ✅ No one-time operations cluttering code
- ✅ Clear separation of concerns
- ✅ Easier code reviews and maintenance
- ✅ Reduced deployment complexity

### **Database Management:**
- ✅ Direct SQL control and visibility
- ✅ Better performance monitoring
- ✅ Easier rollback and recovery
- ✅ Clear audit trail of changes

### **Team Collaboration:**
- ✅ SQL changes are visible to all team members
- ✅ Database changes are documented and tracked
- ✅ Reduced risk of schema conflicts
- ✅ Better understanding of data structure

## 🚨 **Enforcement**

### **Code Review Checklist:**
- [ ] No one-time schema operations in code
- [ ] Database changes documented in `docs/database_changes.md`
- [ ] SQL files properly organized and versioned
- [ ] Runtime validation only where necessary

### **Deployment Process:**
1. **PostgreSQL SQL changes** applied via SQL Editor first
2. **Code changes** deployed after schema is ready
3. **Runtime validation** confirms PostgreSQL schema compatibility
4. **Rollback plan** includes both SQL and code changes

### **Platform-Specific Notes:**
- **No SQLite Support**: Do not create SQLite-compatible schemas
- **PostgreSQL Only**: All database operations must use PostgreSQL syntax
- **Cloud SQL**: Production database is Google Cloud SQL (PostgreSQL)
- **Local Development**: Use PostgreSQL locally, not SQLite

---

**Last Updated**: 2025-01-04
**Next Review**: 2025-01-11

