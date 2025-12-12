# Updated Database Rules - Direct Connection Approach

## 🎯 **Updated Core Principle**
**Direct PostgreSQL connection for local development. Use SQL Editor for schema changes.**

## 🗄️ **Database Platform**
**PostgreSQL Only**: This project uses PostgreSQL exclusively on Google Cloud SQL.

## 📋 **Updated Rules**

### ✅ **Direct Database Connection For:**
- **Local Development**: Connect directly to Google Cloud PostgreSQL
- **Schema Exploration**: Query database structure and data
- **Testing**: Test features against live database data
- **Development**: All development work uses live database

### ✅ **Use SQL Editor For:**
- **Schema Changes**: Adding/removing tables, columns, indexes
  - Example: Adding sport-specific columns (cycling_equivalent_miles, swimming_equivalent_miles, rowing_equivalent_miles)
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

## 🛠️ **Streamlined Connection Setup**

### **Quick Connection Commands:**
```bash
# PowerShell (Windows) - Set environment variable
$env:DATABASE_URL="postgresql://appuser:LwTIf_Yr1AZUGtfalrcQtxyC@35.223.144.85:5432/train-d"

# Then run any Python script or Flask app
python run_flask.py
```

### **Database Instance Details:**
- **Instance**: `train-monk-db-v3`
- **Public IP**: `35.223.144.85`
- **Database**: `train-d`
- **User**: `appuser`
- **Password**: `LwTIf_Yr1AZUGtfalrcQtxyC`
- **Status**: RUNNABLE (verified working)

### **Connection Requirements:**
1. **Environment Variable**: `DATABASE_URL` must be set
2. **Dependencies**: `psycopg2` installed (`pip install psycopg2-binary`)
3. **Network Access**: Public IP enabled (no VPN required)

## 🔧 **Streamlined Development Workflow**

### **1. Quick Database Connection Test:**
```bash
# Set environment and test connection
$env:DATABASE_URL="postgresql://appuser:LwTIf_Yr1AZUGtfalrcQtxyC@35.223.144.85:5432/train-d"
python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('✅ Database connection successful')
conn.close()
"
```

### **2. Direct Database Queries (Recommended):**
```python
# Use direct psycopg2 connection (most reliable)
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()

# Your queries here
cursor.execute("SELECT * FROM user_settings LIMIT 5")
results = cursor.fetchall()

cursor.close()
conn.close()
```

### **3. Schema Exploration Commands:**
```sql
-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
ORDER BY ordinal_position;

-- Check if specific column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_settings' AND column_name = 'age';

-- Sample data check
SELECT id, email, age, gender FROM user_settings LIMIT 5;
```

## 📊 **Database Schema Information**

### **Current Tables:**
- `users` - User accounts and profiles
- `activities` - Strava activity data (includes sport-specific equivalent miles columns)
- `user_settings` - User preferences and OAuth tokens
- `journal_entries` - User notes and reflections
- `ai_autopsies` - AI analysis results
- `legal_compliance` - User agreement tracking
- `migration_status` - OAuth migration tracking
- `acwr_configurations` - ACWR calculation settings

### **Activities Table Sport-Specific Columns:**
- `cycling_equivalent_miles` (REAL) - Running equivalent for cycling activities (2.4-4.0:1 ratio)
- `swimming_equivalent_miles` (REAL) - Running equivalent for swimming activities (4.0-4.2:1 ratio)
- `rowing_equivalent_miles` (REAL) - Running equivalent for rowing activities (1.5-1.7:1 ratio)
- All columns are nullable (NULL for non-applicable activities)

### **Schema Queries:**
```sql
-- Get all tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' ORDER BY table_name;

-- Get table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' ORDER BY ordinal_position;

-- Get indexes
SELECT indexname, indexdef FROM pg_indexes 
WHERE tablename = 'users';
```

## 🚀 **Testing Approach**

### **Local Testing:**
- **Unit Tests**: Mock database interactions
- **Integration Tests**: Use live database connection
- **Schema Tests**: Query database directly
- **Feature Tests**: Test against real data

### **Database-Dependent Testing:**
- **Defer to Post-Deployment**: Tests requiring database access
- **Use Live Database**: For development and testing
- **No Local Database**: Do not create local database replicas

## 🔧 **Troubleshooting & Best Practices**

### **Common Connection Issues:**

#### **1. Connection Pool Not Initialized:**
```bash
# Error: "Connection pool not initialized"
# Solution: Use direct psycopg2 connection instead of db_utils
import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
```

#### **2. Environment Variable Not Set:**
```bash
# Error: "DATABASE_URL environment variable is required"
# Solution: Set environment variable first
$env:DATABASE_URL="postgresql://appuser:LwTIf_Yr1AZUGtfalrcQtxyC@35.223.144.85:5432/train-d"
```

#### **3. SQL Syntax Errors:**
```sql
-- ❌ Wrong (SQLite syntax)
UPDATE user_settings SET field = ? WHERE id = ?

-- ✅ Correct (PostgreSQL syntax)
UPDATE user_settings SET field = %s WHERE id = %s
```

### **Best Practices:**

#### **1. Always Use Direct Connection for Queries:**
```python
# ✅ Recommended approach
import psycopg2
import os

def query_database(query, params=None):
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
```

#### **2. Check Column Existence Before Operations:**
```python
# Check if column exists before using it
cursor.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'user_settings' AND column_name = 'age'
""")
age_column = cursor.fetchone()
if age_column:
    print("Age column exists")
```

#### **3. Use Proper PostgreSQL Data Types:**
```sql
-- ✅ Correct PostgreSQL syntax
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    age INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ❌ Wrong (SQLite syntax)
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔒 **Security Considerations**

### **Development:**
- **Public IP**: Required for local development access
- **Authorized Networks**: Use 0.0.0.0/0 for development (less secure)
- **Credentials**: Store in .env file (never commit)

### **Production:**
- **Private IP**: Use private IP for production
- **VPN Access**: Require VPN for private IP access
- **Secret Manager**: Use Google Secret Manager for credentials

## 📁 **File Organization**

### **Configuration Files:**
- `app/.env` - Local development environment variables
- `app/db_utils.py` - Database connection utilities
- `docs/database_changes.md` - Schema change log

### **SQL Files:**
- `sql/*.sql` - Schema definitions and migrations
- `docs/database_changes.md` - Change documentation

### **Code Files:**
- `app/db_utils.py` - Database utilities, connection management
- `app/models/` - Data models, ORM definitions
- `app/migrations/` - Runtime schema validation only

## 🎯 **Benefits of Direct Connection**

### **Development Efficiency:**
- ✅ **Real-time Data**: Always work with current database state
- ✅ **Schema Visibility**: Complete visibility into database structure
- ✅ **No Sync Issues**: No need to sync local and remote databases
- ✅ **Consistent Environment**: Same database for all developers

### **Database Management:**
- ✅ **Direct SQL Control**: Full SQL capabilities
- ✅ **Performance Monitoring**: Real-time performance data
- ✅ **Easy Rollback**: Direct database access for recovery
- ✅ **Clear Audit Trail**: All changes visible in database

### **Team Collaboration:**
- ✅ **Shared Database**: All developers use same database
- ✅ **Real-time Changes**: Changes visible to all team members
- ✅ **Reduced Conflicts**: No local database conflicts
- ✅ **Better Understanding**: Direct database interaction

## 🚨 **Enforcement**

### **Code Review Checklist:**
- [ ] No one-time schema operations in code
- [ ] Database changes documented in `docs/database_changes.md`
- [ ] SQL files properly organized and versioned
- [ ] Runtime validation only where necessary
- [ ] Direct database connection configured correctly

### **Deployment Process:**
1. **PostgreSQL SQL changes** applied via SQL Editor first
2. **Code changes** deployed after schema is ready
3. **Runtime validation** confirms PostgreSQL schema compatibility
4. **Rollback plan** includes both SQL and code changes

### **Platform-Specific Notes:**
- **No SQLite Support**: Do not create SQLite-compatible schemas
- **PostgreSQL Only**: All database operations must use PostgreSQL syntax
- **Cloud SQL**: Production database is Google Cloud SQL (PostgreSQL)
- **Direct Connection**: Local development uses direct database connection

## 🔄 **Migration from Previous Approach**

### **What Changed:**
- **Removed**: Local SQLite database support
- **Added**: Direct PostgreSQL connection for development
- **Updated**: Environment configuration for cloud database
- **Simplified**: No local database setup required

### **What Stayed the Same:**
- **SQL Editor**: Still required for schema changes
- **PostgreSQL Only**: Still PostgreSQL-exclusive
- **Schema Rules**: Same rules for schema management
- **Testing Approach**: Same testing deferral rules

## 📋 **Quick Reference**

### **Essential Commands:**
```bash
# Set environment variable (PowerShell)
$env:DATABASE_URL="postgresql://appuser:LwTIf_Yr1AZUGtfalrcQtxyC@35.223.144.85:5432/train-d"

# Test connection
python -c "import psycopg2, os; conn = psycopg2.connect(os.environ['DATABASE_URL']); print('✅ Connected'); conn.close()"

# Check table structure
python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()
cursor.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', ('user_settings',))
for row in cursor.fetchall(): print(f'{row[0]}: {row[1]}')
conn.close()
"
```

### **Common Queries:**
```sql
-- Check if column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_settings' AND column_name = 'age';

-- Get sample data
SELECT id, email, age, gender FROM user_settings LIMIT 5;

-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
ORDER BY ordinal_position;
```

### **Connection String:**
```
postgresql://appuser:LwTIf_Yr1AZUGtfalrcQtxyC@35.223.144.85:5432/train-d
```

---

## 📝 **Recent Schema Changes**

### **2025-12-09: Rowing Support Added**
- Added `rowing_equivalent_miles` column to `activities` table
- Conversion factors: 1.5:1 (indoor/erg), 1.7:1 (on-water)
- Migration file: `sql/add_rowing_support.sql`
- Backend support: Full rowing activity classification and load calculation
- Frontend support: Rowing toggle and visualization in dashboard

---

**Last Updated**: 2025-12-09
**Next Review**: 2025-12-16
**Status**: Active - Streamlined Direct Connection Approach
