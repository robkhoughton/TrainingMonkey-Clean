# SQL Syntax Guide - PostgreSQL Only

## 🎯 Overview

This guide ensures all SQL queries use PostgreSQL syntax and prevents SQLite syntax regressions.

## 🚨 Critical Rules

### 1. Placeholder Syntax
**❌ WRONG (SQLite):**
```python
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**✅ CORRECT (PostgreSQL):**
```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### 2. Data Types
**❌ WRONG (SQLite):**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    score REAL
);
```

**✅ CORRECT (PostgreSQL):**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    age INTEGER,
    score DECIMAL(10,2)
);
```

### 3. Common Patterns

#### Dynamic IN Clauses
**❌ WRONG:**
```python
placeholders = ','.join(['?' for _ in items])
query = f"SELECT * FROM table WHERE id IN ({placeholders})"
```

**✅ CORRECT:**
```python
placeholders = ','.join(['%s' for _ in items])
query = f"SELECT * FROM table WHERE id IN ({placeholders})"
```

#### JSONB Operations
**❌ WRONG:**
```sql
SELECT LENGTH(json_column) FROM table;
```

**✅ CORRECT:**
```sql
SELECT jsonb_array_length(json_column) FROM table;
```

## 🔍 Validation Checklist

Before committing any SQL code:

- [ ] All placeholders use `%s` (not `?`)
- [ ] No `AUTOINCREMENT` keywords
- [ ] No `INTEGER PRIMARY KEY` without SERIAL
- [ ] No `REAL` data type
- [ ] No `TEXT` without length specification
- [ ] JSONB operations use PostgreSQL functions
- [ ] No `sqlite3` imports

## 🛠️ Tools

### Validation Script
```bash
python scripts/validate_sql_syntax.py
```

### Pre-commit Hook
```bash
python scripts/pre-commit-hooks.py
```

## 📚 Reference

### PostgreSQL Data Types
| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `TEXT` | `VARCHAR(n)` or `TEXT` |
| `REAL` | `DECIMAL(p,s)` or `NUMERIC(p,s)` |
| `BLOB` | `BYTEA` |

### PostgreSQL Functions
| SQLite | PostgreSQL |
|--------|------------|
| `LENGTH(json)` | `jsonb_array_length(json)` |
| `json_extract()` | `jsonb_extract_path_text()` |
| `json_set()` | `jsonb_set()` |

## 🚨 Common Mistakes

1. **Copy-pasting from tutorials** - Many tutorials use SQLite syntax
2. **AI-generated code** - AI tools often default to SQLite
3. **Legacy code** - Old code may have SQLite remnants
4. **Documentation examples** - Check that examples use PostgreSQL

## 🔧 Quick Fixes

### Fix Placeholder Issues
```bash
# Find all SQLite placeholders
grep -r "?" app/ --include="*.py" | grep -v "#"

# Replace with PostgreSQL placeholders
sed -i 's/?/%s/g' file.py
```

### Fix Data Type Issues
```bash
# Find SQLite data types
grep -r "AUTOINCREMENT\|INTEGER PRIMARY KEY\|REAL" app/ --include="*.py"
```

## 📞 Support

If you encounter SQL syntax issues:
1. Run the validation script
2. Check this guide
3. Review existing compliant code
4. Ask for help if needed

Remember: **PostgreSQL syntax is mandatory for this project!**
