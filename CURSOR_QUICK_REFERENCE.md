# 🚀 Cursor Quick Reference - TrainingMonkey

## Before Starting Any Work
```bash
# Run validation
python scripts/pre_work_validation.py

# Check SQL syntax
python scripts/validate_sql_syntax.py
```

## 🗄️ Database Quick Rules
```sql
-- ✅ CORRECT PostgreSQL Syntax
INSERT INTO table (col) VALUES (%s)
CREATE TABLE table (id SERIAL PRIMARY KEY)
UPDATE table SET updated_at = NOW()

-- ❌ WRONG SQLite Syntax  
INSERT INTO table (col) VALUES (?)
CREATE TABLE table (id INTEGER PRIMARY KEY AUTOINCREMENT)
UPDATE table SET updated_at = CURRENT_TIMESTAMP
```

## 📅 Date Operations
```python
# ✅ CORRECT - Date only operations
from datetime import datetime
current_date = datetime.now().date()
date_str = current_date.strftime('%Y-%m-%d')

# ❌ WRONG - Using datetime for date operations
current_date = datetime.now()  # Includes time component
```

## 🔧 Code Patterns
```python
# ✅ CORRECT - Public API usage
from user_account_manager import user_account_manager
user_account_manager.complete_onboarding(user_id)

# ❌ WRONG - Private method call
from onboarding_manager import onboarding_manager
onboarding_manager._complete_onboarding(user_id)

# ✅ CORRECT - Database connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM table WHERE id = %s", (user_id,))
    conn.commit()
```

## 🎯 Remember
1. **Schema changes**: SQL Editor ONLY
2. **Date APIs**: Always return `'YYYY-MM-DD'`
3. **Error handling**: Meaningful messages
4. **Testing**: End-to-end user flows
5. **Validation**: Check database state first
