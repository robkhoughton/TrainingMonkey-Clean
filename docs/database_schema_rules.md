# Database Schema Management Rules

## 🎯 **Core Principle**
**Use SQL Editor for one-time database operations. Don't clutter the codebase.**

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
1. **Google Cloud SQL Console** for production database
2. **Local SQLite Browser** for development database
3. **pgAdmin** or **DBeaver** for PostgreSQL management
4. **Document all changes** in `docs/database_changes.md`

### **Code Integration:**
```python
# ✅ Good: Runtime validation only
def check_required_columns():
    """Check if required columns exist at runtime"""
    try:
        result = execute_query("SELECT column_name FROM information_schema.columns WHERE table_name = 'user_settings'")
        existing_columns = [row[0] for row in result]
        missing_columns = set(REQUIRED_COLUMNS) - set(existing_columns)
        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}")
            return False
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

# ❌ Bad: One-time schema changes in code
def ensure_goals_columns_exist():
    """Don't do this - use SQL Editor instead"""
    execute_query("ALTER TABLE user_settings ADD COLUMN goals_configured BOOLEAN")
```

## 📁 **File Organization**

### **SQL Files:**
- `sql/schema/` - Table definitions, indexes
- `sql/migrations/` - One-time data migrations
- `sql/seeds/` - Initial data setup
- `docs/database_changes.md` - Change log

### **Code Files:**
- `db_utils.py` - Database utilities, connection management
- `models/` - Data models, ORM definitions
- `migrations/` - Runtime schema validation only

## 🔍 **Current Goals Setup Implementation**

### **Required SQL Commands:**
```sql
-- Add goals columns to user_settings table
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goals_configured BOOLEAN DEFAULT FALSE;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goal_type VARCHAR(50);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goal_target VARCHAR(100);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goal_timeframe VARCHAR(50);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goals_setup_date TIMESTAMP;

-- Create onboarding_analytics table for real analytics
CREATE TABLE IF NOT EXISTS onboarding_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Add index for analytics queries
CREATE INDEX IF NOT EXISTS idx_onboarding_analytics_user_timestamp 
ON onboarding_analytics(user_id, timestamp);
```

### **Verification Query:**
```sql
-- Check if goals columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
AND column_name IN ('goals_configured', 'goal_type', 'goal_target', 'goal_timeframe', 'goals_setup_date')
ORDER BY column_name;
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
1. **SQL changes** applied via SQL Editor first
2. **Code changes** deployed after schema is ready
3. **Runtime validation** confirms schema compatibility
4. **Rollback plan** includes both SQL and code changes

---

**Last Updated**: 2025-08-29
**Next Review**: 2025-09-05

