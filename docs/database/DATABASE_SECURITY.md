# Database Security Guidelines

## ⚠️ CRITICAL: Never Commit Database Credentials

The PostgreSQL database connection string should **NEVER** be hardcoded in source files or committed to version control.

## Secure Configuration Methods

### Method 1: Environment Variables (Recommended for Production)

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
```

For Google Cloud Run, use Secret Manager:
```bash
gcloud secrets create database-url --data-file=-
# Then update Cloud Run service to use the secret
```

### Method 2: .env File (Local Development Only)

Create a `.env` file in the project root (this file is gitignored):

```bash
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

**Never commit the `.env` file to version control.**

## Database Credentials Format

```
postgresql://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
```

**Example (replace with your actual credentials):**
```
postgresql://appuser:YOUR_PASSWORD_HERE@35.223.144.85:5432/train-d
```

## For Utility Scripts

All utility scripts (`generate_user_report.py`, `check_users.py`, etc.) should use:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Use DATABASE_URL for connection
conn = psycopg2.connect(DATABASE_URL)
```

## Security Checklist

- [ ] Database password changed after exposure
- [ ] All utility scripts use environment variables
- [ ] `.env` file added to `.gitignore`
- [ ] No hardcoded credentials in source code
- [ ] Production uses Google Cloud Secret Manager
- [ ] IP whitelisting enabled on database (if applicable)

## If Credentials Are Exposed

1. **Immediately change the database password**
2. Remove files from git tracking: `git rm --cached [file]`
3. Update `.gitignore` to prevent future commits
4. Consider cleaning git history with BFG Repo-Cleaner
5. Rotate all related secrets
6. Review database access logs for unauthorized activity

## Current Security Status

✅ Utility scripts removed from version control
✅ `.gitignore` updated to exclude credential-containing files
⚠️ **ACTION REQUIRED:** Rotate all exposed database passwords immediately
⚠️ **ACTION REQUIRED:** Update local `.env` file with new credentials

