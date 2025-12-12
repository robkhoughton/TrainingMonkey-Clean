# Database Connection Quick Start Guide

## 🚀 **One-Command Connection**

```bash
# Set environment variable and test connection
$env:DATABASE_URL="postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d"
python scripts/quick_db_connect.py test
```

## 🔧 **Helper Script Commands**

```bash
# Test database connection
python scripts/quick_db_connect.py test

# Check if specific column exists
python scripts/quick_db_connect.py column user_settings age

# View table structure
python scripts/quick_db_connect.py structure user_settings

# Get sample data
python scripts/quick_db_connect.py sample user_settings 5

# Set environment variable
python scripts/quick_db_connect.py env
```

## 📊 **Common Database Operations**

### **Direct Python Connection:**
```python
import psycopg2
import os

# Set environment variable
os.environ['DATABASE_URL'] = "postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d"

# Connect and query
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()
cursor.execute("SELECT * FROM user_settings LIMIT 5")
results = cursor.fetchall()
cursor.close()
conn.close()
```

### **Common SQL Queries:**
```sql
-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
ORDER BY ordinal_position;

-- Check if column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_settings' AND column_name = 'age';

-- Get sample data
SELECT id, email, age, gender FROM user_settings LIMIT 5;
```

## 🛠️ **Troubleshooting**

### **Connection Issues:**
- **Error**: "Connection pool not initialized" → Use direct `psycopg2` connection
- **Error**: "DATABASE_URL environment variable is required" → Set environment variable first
- **Error**: SQL syntax errors → Use PostgreSQL syntax (`%s` placeholders, `NOW()` timestamps)

### **Quick Fixes:**
```bash
# Always set environment variable first
$env:DATABASE_URL="postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d"

# Test connection
python -c "import psycopg2, os; conn = psycopg2.connect(os.environ['DATABASE_URL']); print('✅ Connected'); conn.close()"
```

## 📋 **Database Details**

- **Instance**: `train-monk-db-v3`
- **Host**: `35.223.144.85`
- **Database**: `train-d`
- **User**: `appuser`
- **Password**: `trainmonk25`
- **Connection String**: `postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d`

## ✅ **Verification Checklist**

- [ ] Environment variable set: `$env:DATABASE_URL="postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d"`
- [ ] Connection test passes: `python scripts/quick_db_connect.py test`
- [ ] Can query data: `python scripts/quick_db_connect.py sample user_settings 3`
- [ ] PostgreSQL syntax used: `%s` placeholders, `NOW()` timestamps

---

**Last Updated**: 2025-01-27  
**Status**: Streamlined and Tested
