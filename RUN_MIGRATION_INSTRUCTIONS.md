# Database Migration Instructions

## Overview
This migration adds two new columns to the `activities` table:
- `start_time` - Stores activity start time in 'HH:MM:SS' format
- `device_name` - Stores device name for Garmin branding compliance

## Steps to Run Migration

### Option 1: PowerShell (Recommended)
```powershell
# Set the DATABASE_URL with your correct password
$env:DATABASE_URL="postgresql://appuser:YOUR_PASSWORD@35.223.144.85:5432/train-d"

# Run the migration
cd app
python run_migration.py
```

### Option 2: Command Prompt
```cmd
# Set the DATABASE_URL with your correct password
set DATABASE_URL=postgresql://appuser:YOUR_PASSWORD@35.223.144.85:5432/train-d

# Run the migration
cd app
python run_migration.py
```

### Option 3: One-Line PowerShell Command
```powershell
$env:DATABASE_URL="postgresql://appuser:YOUR_PASSWORD@35.223.144.85:5432/train-d"; cd app; python run_migration.py; cd ..
```

## What the Migration Does

The migration script (`app/run_migration.py`) will:
1. Connect to the database using the existing `db_utils` module
2. Execute `ALTER TABLE activities ADD COLUMN IF NOT EXISTS start_time TEXT`
3. Execute `ALTER TABLE activities ADD COLUMN IF NOT EXISTS device_name TEXT`
4. Verify both columns were created successfully
5. Display confirmation

## Expected Output

```
============================================================
SCHEMA MIGRATION: Adding start_time and device_name columns
============================================================

[1/2] Adding start_time column...
[OK] Successfully added start_time column

[2/2] Adding device_name column...
[OK] Successfully added device_name column

[Verification] Checking columns...

[OK] Verified 2 new columns exist:
  - device_name (text)
  - start_time (text)

============================================================
[SUCCESS] MIGRATION COMPLETED SUCCESSFULLY!
============================================================

Next steps:
1. Deploy updated backend code
2. Deploy updated frontend  
3. Trigger Strava sync to populate new fields
```

## If Migration Fails

Common issues:
1. **Authentication Error**: Wrong password in DATABASE_URL
2. **Connection Error**: Database not accessible
3. **Columns Already Exist**: Migration was already run (this is okay!)

## After Migration

Once the migration succeeds:
1. The database schema is ready
2. Deploy the updated code (backend + frontend)
3. Users should sync their Strava data to populate the new fields
4. Existing activities will remain without start_time/device_name until re-synced

## Files Involved

- `app/run_migration.py` - Migration script
- `ADD_START_TIME_FIELD.sql` - SQL documentation
- `app/strava_training_load.py` - Captures start_time and device_name from Strava
- `frontend/src/ActivitiesPage.tsx` - Displays start_time below date


