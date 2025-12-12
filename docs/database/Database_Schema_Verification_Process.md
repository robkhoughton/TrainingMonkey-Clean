# Database Schema Verification Process

## Overview
This document outlines the systematic approach to verify database schema and field names before making changes or debugging issues. Following the principle: **Collect Facts First, Then Analyze, Then Act**.

## Database Rules Compliance

**⚠️ CRITICAL: This process must follow the established database rules:**

### Core Database Rules:
1. **Use SQL Editor for one-time database operations** - Don't clutter the codebase
2. **Manual schema changes via SQL Editor** - No automated schema changes in code
3. **Document all changes** in `docs/database_changes.md`
4. **Use cloud database only** - No local database creation for testing
5. **Runtime validation only** - Code should only validate, not modify schema

### References:
- `docs/database_schema_rules.md` - Core database management rules
- `docs/database_testing_rules.md` - Database testing guidelines
- `docs/database_changes.md` - Change log for all schema modifications

## Step 1: Collect Facts - Database Schema Discovery

### 1.1 Current Database Schema Queries

Run these queries in your SQL Editor to collect the actual database schema:

#### A. Check All Tables
```sql
-- List all tables in the database
SELECT 
    table_name,
    table_type,
    CASE 
        WHEN table_name IN ('user_settings', 'activities', 'hr_streams', 'feature_flags') 
        THEN '✅ CORE TABLE'
        ELSE 'ℹ️ OTHER TABLE'
    END as table_category
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

#### B. Verify user_settings Table Structure
```sql
-- Check user_settings table columns and data types
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    character_maximum_length,
    CASE 
        WHEN column_name IN ('id', 'email', 'password_hash', 'resting_hr', 'max_hr', 'gender', 'is_admin') 
        THEN '✅ CORE COLUMN'
        WHEN column_name LIKE '%strava%' 
        THEN '🔗 STRAVA COLUMN'
        WHEN column_name LIKE '%migration%' 
        THEN '🔄 MIGRATION COLUMN'
        ELSE 'ℹ️ OTHER COLUMN'
    END as column_category
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
ORDER BY ordinal_position;
```

#### C. Verify activities Table Structure
```sql
-- Check activities table columns and data types
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    CASE 
        WHEN column_name IN ('activity_id', 'user_id', 'date', 'name', 'type', 'avg_heart_rate', 'duration_minutes', 'trimp') 
        THEN '✅ CORE COLUMN'
        WHEN column_name LIKE '%trimp%' 
        THEN '📊 TRIMP COLUMN'
        WHEN column_name LIKE '%hr%' 
        THEN '❤️ HR COLUMN'
        ELSE 'ℹ️ OTHER COLUMN'
    END as column_category
FROM information_schema.columns 
WHERE table_name = 'activities' 
ORDER BY ordinal_position;
```

#### D. Verify hr_streams Table Structure
```sql
-- Check if hr_streams table exists and its structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    CASE 
        WHEN column_name IN ('id', 'activity_id', 'user_id', 'hr_data', 'sample_rate') 
        THEN '✅ CORE COLUMN'
        ELSE 'ℹ️ OTHER COLUMN'
    END as column_category
FROM information_schema.columns 
WHERE table_name = 'hr_streams' 
ORDER BY ordinal_position;
```

#### E. Check Data Types for Critical Fields
```sql
-- Verify data types for critical fields
SELECT 
    table_name,
    column_name,
    data_type,
    CASE 
        WHEN column_name = 'activity_id' AND data_type = 'bigint' THEN '✅ CORRECT'
        WHEN column_name = 'activity_id' AND data_type != 'bigint' THEN '❌ WRONG TYPE'
        WHEN column_name = 'id' AND data_type IN ('integer', 'bigint', 'serial') THEN '✅ CORRECT'
        WHEN column_name = 'id' AND data_type NOT IN ('integer', 'bigint', 'serial') THEN '❌ WRONG TYPE'
        ELSE 'ℹ️ CHECK MANUALLY'
    END as type_status
FROM information_schema.columns 
WHERE table_name IN ('user_settings', 'activities', 'hr_streams')
AND column_name IN ('id', 'activity_id', 'user_id')
ORDER BY table_name, column_name;
```

### 1.2 Sample Data Verification

#### A. Check User Settings Data
```sql
-- Verify user settings data exists and is properly formatted
SELECT 
    id,
    email,
    resting_hr,
    max_hr,
    gender,
    is_admin,
    CASE 
        WHEN resting_hr IS NULL THEN '❌ MISSING RESTING_HR'
        WHEN max_hr IS NULL THEN '❌ MISSING MAX_HR'
        WHEN gender IS NULL THEN '❌ MISSING GENDER'
        ELSE '✅ COMPLETE'
    END as hr_config_status
FROM user_settings 
WHERE id = 1;
```

#### B. Check Activities Data
```sql
-- Verify activities data structure
SELECT 
    activity_id,
    user_id,
    date,
    avg_heart_rate,
    duration_minutes,
    trimp,
    CASE 
        WHEN activity_id > 2147483647 THEN '⚠️ LARGE ID'
        WHEN avg_heart_rate IS NULL THEN '❌ MISSING HR'
        WHEN duration_minutes IS NULL THEN '❌ MISSING DURATION'
        ELSE '✅ COMPLETE'
    END as data_status
FROM activities 
WHERE user_id = 1 
ORDER BY date DESC 
LIMIT 5;
```

#### C. Check HR Streams Data
```sql
-- Verify HR streams data
SELECT 
    id,
    activity_id,
    user_id,
    sample_rate,
    created_at,
    CASE 
        WHEN hr_data IS NULL THEN '❌ MISSING HR_DATA'
        WHEN sample_rate IS NULL THEN '❌ MISSING SAMPLE_RATE'
        ELSE '✅ COMPLETE'
    END as stream_status
FROM hr_streams 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 5;
```

## Step 2: Analyze - Schema Comparison and Issue Identification

### 2.1 Expected vs Actual Schema Analysis

#### A. Core Tables Checklist
- [ ] `user_settings` table exists with required columns
- [ ] `activities` table exists with required columns  
- [ ] `hr_streams` table exists with required columns
- [ ] `feature_flags` table exists (if used)

#### B. Critical Field Analysis
- [ ] `activity_id` is `BIGINT` (not `INTEGER`)
- [ ] `user_id` references exist and are consistent
- [ ] HR configuration fields exist in `user_settings`
- [ ] TRIMP calculation fields exist in `activities`

#### C. Data Type Analysis
- [ ] Large IDs use `BIGINT` (Strava activity IDs can exceed 2^31)
- [ ] JSON data uses `JSONB` (PostgreSQL) or `TEXT` (SQLite)
- [ ] Timestamps use `TIMESTAMP` with proper defaults
- [ ] Numeric fields use appropriate precision

### 2.2 Common Schema Issues

#### Issue 1: Missing Columns
**Symptoms**: SQL errors about missing columns
**Example**: `no such column: resting_hr`
**Solution**: Add missing columns via SQL Editor

#### Issue 2: Wrong Data Types
**Symptoms**: Data overflow or truncation
**Example**: Large activity IDs causing errors
**Solution**: Change `INTEGER` to `BIGINT`

#### Issue 3: Inconsistent References
**Symptoms**: Foreign key constraint errors
**Example**: `user_id` references don't match
**Solution**: Verify and fix reference consistency

#### Issue 4: Missing Indexes
**Symptoms**: Slow query performance
**Example**: Queries on `user_id` or `activity_id` are slow
**Solution**: Add appropriate indexes

## Step 3: Act - Schema Corrections and Validation

### 3.1 Schema Correction Process

**⚠️ IMPORTANT: All schema changes must be done via SQL Editor, not in code!**

#### A. Schema Changes via SQL Editor
**Use Google Cloud SQL Console or your preferred SQL Editor to execute these commands:**

```sql
-- Add missing HR configuration columns to user_settings
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS resting_hr INTEGER DEFAULT 60;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS max_hr INTEGER DEFAULT 180;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT 'male';

-- Add missing TRIMP calculation columns to activities
ALTER TABLE activities ADD COLUMN IF NOT EXISTS trimp_calculation_method VARCHAR(20) DEFAULT 'average';
ALTER TABLE activities ADD COLUMN IF NOT EXISTS hr_stream_sample_count INTEGER DEFAULT 0;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS trimp_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

#### B. Data Type Corrections via SQL Editor
```sql
-- Change activity_id to BIGINT if it's currently INTEGER
ALTER TABLE activities ALTER COLUMN activity_id TYPE BIGINT;

-- Change user_id to BIGINT if it's currently INTEGER
ALTER TABLE user_settings ALTER COLUMN id TYPE BIGINT;
ALTER TABLE activities ALTER COLUMN user_id TYPE BIGINT;
```

#### C. Create Missing Tables via SQL Editor
```sql
-- Create hr_streams table if it doesn't exist
CREATE TABLE IF NOT EXISTS hr_streams (
    id SERIAL PRIMARY KEY,
    activity_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    hr_data JSONB,
    sample_rate REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(activity_id),
    FOREIGN KEY (user_id) REFERENCES user_settings(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_hr_streams_activity_id ON hr_streams(activity_id);
CREATE INDEX IF NOT EXISTS idx_hr_streams_user_id ON hr_streams(user_id);
```

#### D. Document All Changes
**After executing schema changes, document them in `docs/database_changes.md`:**
- Date of change
- SQL commands executed
- Reason for change
- Verification results

### 3.2 Validation Queries

#### A. Post-Correction Verification
```sql
-- Verify all required columns exist
SELECT 
    table_name,
    column_name,
    data_type,
    CASE 
        WHEN column_name IN ('resting_hr', 'max_hr', 'gender') AND table_name = 'user_settings' THEN '✅ HR CONFIG'
        WHEN column_name IN ('trimp_calculation_method', 'hr_stream_sample_count') AND table_name = 'activities' THEN '✅ TRIMP FIELDS'
        WHEN column_name = 'activity_id' AND data_type = 'bigint' THEN '✅ BIGINT ID'
        ELSE 'ℹ️ OTHER'
    END as verification_status
FROM information_schema.columns 
WHERE table_name IN ('user_settings', 'activities', 'hr_streams')
AND column_name IN ('resting_hr', 'max_hr', 'gender', 'trimp_calculation_method', 'hr_stream_sample_count', 'activity_id', 'id', 'user_id')
ORDER BY table_name, column_name;
```

#### B. Data Integrity Check
```sql
-- Check for data integrity issues
SELECT 
    'user_settings' as table_name,
    COUNT(*) as total_rows,
    COUNT(resting_hr) as resting_hr_count,
    COUNT(max_hr) as max_hr_count,
    COUNT(gender) as gender_count
FROM user_settings
UNION ALL
SELECT 
    'activities' as table_name,
    COUNT(*) as total_rows,
    COUNT(trimp_calculation_method) as trimp_method_count,
    COUNT(hr_stream_sample_count) as hr_stream_count,
    COUNT(trimp_processed_at) as trimp_processed_count
FROM activities;
```

## Step 4: Documentation and Prevention

### 4.1 Schema Documentation Template

```sql
-- Database Schema Documentation
-- Last Updated: [DATE]
-- Version: [VERSION]

-- Core Tables:
-- 1. user_settings: User configuration and authentication
-- 2. activities: Activity data and TRIMP calculations  
-- 3. hr_streams: Heart rate stream data storage
-- 4. feature_flags: Feature toggle management

-- Critical Data Types:
-- - activity_id: BIGINT (Strava IDs can exceed 2^31)
-- - user_id: BIGINT (consistent across all tables)
-- - hr_data: JSONB (PostgreSQL) or TEXT (SQLite)
-- - timestamps: TIMESTAMP with DEFAULT CURRENT_TIMESTAMP
```

### 4.2 Prevention Checklist

Before making any database changes:

- [ ] **Collect Facts**: Run schema verification queries
- [ ] **Analyze**: Compare expected vs actual schema
- [ ] **Document**: Record current state before changes
- [ ] **Use SQL Editor**: Execute schema changes via SQL Editor (NOT in code)
- [ ] **Document Changes**: Update `docs/database_changes.md` with all modifications
- [ ] **Validate**: Run post-change verification queries
- [ ] **Monitor**: Check for errors after deployment

### 4.3 Common Mistakes to Avoid

1. **Don't assume schema**: Always verify actual database structure
2. **Don't use local database**: Use cloud database for all operations
3. **Don't skip validation**: Always run verification queries
4. **Don't ignore data types**: Use `BIGINT` for external API IDs
5. **Don't forget indexes**: Add indexes for performance-critical queries
6. **Don't put schema changes in code**: Use SQL Editor for all schema modifications
7. **Don't forget to document**: Always update `docs/database_changes.md`
8. **Don't automate schema changes**: Manual execution via SQL Editor only

## Conclusion

Following this systematic approach ensures that database schema issues are identified and resolved before they cause problems in production. The key is to **collect facts first** through comprehensive schema queries, **analyze** the differences between expected and actual state, and then **act** with targeted corrections and validation.

This process should be followed whenever:
- Debugging database-related errors
- Adding new features that require schema changes
- Migrating between database systems
- Troubleshooting performance issues
- Validating deployment readiness
