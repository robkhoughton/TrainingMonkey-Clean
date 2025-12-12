# Cursor ↔ Google Cloud PostgreSQL Bridge Setup Guide

## 🎯 Overview

This guide helps you set up a direct connection between Cursor (your local development environment) and your PostgreSQL database hosted on Google Cloud SQL. This allows you to develop locally while using the production database schema and data.

## 📋 Prerequisites

- ✅ Google Cloud SQL PostgreSQL instance running
- ✅ Cursor IDE installed
- ✅ Python 3.8+ installed
- ✅ Access to your Google Cloud project (`dev-ruler-460822-e8`)

## 🚀 Quick Setup (5 minutes)

### Step 1: Run the Setup Script

```bash
cd scripts
python setup_local_database_connection.py
```

This script will:
- Create a `.env` file with your database connection details
- Use the known connection details from your deployment scripts
- Generate a secure secret key
- Test the database connection

### Step 2: Install Dependencies

```bash
cd app
pip install -r strava_requirements.txt
```

### Step 3: Test the Connection

```bash
cd scripts
python test_database_connection.py
```

### Step 4: Start Development Server

```bash
cd app
python start_dev_server.ps1
```

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Create Environment File

Create `app/.env` with these contents:

```bash
# Database Configuration
DATABASE_URL=postgresql://appuser:YOUR_PASSWORD@HOST:5432/train-d

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=dev-ruler-460822-e8

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5001

# Strava API (optional for basic testing)
STRAVA_CLIENT_ID=your-strava-client-id
STRAVA_CLIENT_SECRET=your-strava-client-secret
```

### 2. Install Dependencies

```bash
pip install psycopg2-binary python-dotenv flask
```

### 3. Test Connection

```bash
python scripts/test_database_connection.py
```

## 🗄️ Database Connection Details

Based on your deployment scripts, your database connection details are:

| Parameter | Value |
|-----------|-------|
| **Host** | `10.109.208.9` (Private IP) |
| **Port** | `5432` |
| **Database** | `train-d` |
| **Username** | `appuser` |
| **Password** | `[Load from .env file - never hardcode]` |
| **Project** | `dev-ruler-460822-e8` |
| **Region** | `us-central1` |

## 🔍 Connection Testing

The test script will verify:

- ✅ Environment variables are set correctly
- ✅ Database connection is established
- ✅ PostgreSQL version and server info
- ✅ Table count and sample tables
- ✅ User count (if users table exists)

## 🛠️ Development Workflow

### With Live Database Connection

1. **Start Development Server**:
   ```bash
   cd app
   python start_dev_server.ps1
   ```

2. **Access Application**:
   - Open: http://localhost:5001
   - All database operations use the live Google Cloud database

3. **Database Operations**:
   - **Read Operations**: Safe to perform (SELECT queries)
   - **Write Operations**: Use with caution (INSERT, UPDATE, DELETE)
   - **Schema Changes**: Use SQL Editor only (per project rules)

### Database Rules Compliance

Remember these key rules:

- ✅ **PostgreSQL Only**: No SQLite compatibility
- ✅ **SQL Editor for Schema**: One-time operations via SQL Editor
- ✅ **Cloud Database**: All operations use the cloud database
- ✅ **Manual Schema Changes**: Don't put schema changes in code

## 🔧 Troubleshooting

### Connection Issues

**Error: "DATABASE_URL environment variable is required"**
- Solution: Make sure `.env` file exists in `app/` directory
- Check that `DATABASE_URL` is set correctly

**Error: "Connection refused"**
- Solution: Verify Google Cloud SQL instance is running
- Check that your IP is whitelisted in Cloud SQL

**Error: "Authentication failed"**
- Solution: Verify username and password are correct
- Check that the user has proper permissions

**Error: "Database does not exist"**
- Solution: Verify database name is correct (`train-d`)
- Check that the database exists in Cloud SQL

### Dependency Issues

**Error: "No module named 'psycopg2'"**
```bash
pip install psycopg2-binary
```

**Error: "No module named 'python-dotenv'"**
```bash
pip install python-dotenv
```

### Environment Issues

**Error: "Could not find .env file"**
- Solution: Run the setup script or create `.env` manually
- Make sure the file is in the `app/` directory

## 📊 Database Schema Information

Your database includes these main tables:

- `users` - User accounts and profiles
- `activities` - Strava activity data
- `user_settings` - User preferences and OAuth tokens
- `journal_entries` - User notes and reflections
- `ai_autopsies` - AI analysis results
- `legal_compliance` - User agreement tracking
- `migration_status` - OAuth migration tracking
- `acwr_configurations` - ACWR calculation settings

## 🔒 Security Considerations

- **Local Development**: The `.env` file contains sensitive credentials
- **Never Commit**: Add `.env` to `.gitignore` (already configured)
- **Production**: Uses Google Secret Manager for credentials
- **Network**: Connection uses private IP (10.109.208.9)

## 🚀 Next Steps

After successful setup:

1. **Start Developing**: Use Cursor with live database connection
2. **Test Features**: Verify all functionality works with real data
3. **Schema Changes**: Use SQL Editor for any database modifications
4. **Deploy**: Use existing deployment scripts when ready

## 📞 Support

If you encounter issues:

1. **Check Logs**: Look at the console output for error messages
2. **Verify Setup**: Run the test script to diagnose issues
3. **Review Rules**: Ensure you're following the database rules
4. **Check Documentation**: Refer to other docs in the `docs/` folder

---

**Last Updated**: 2025-01-27  
**Project**: TrainingMonkey-Clean  
**Database**: Google Cloud SQL PostgreSQL
