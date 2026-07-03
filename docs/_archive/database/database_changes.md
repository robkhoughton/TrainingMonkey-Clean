# Database Changes Log

## 📋 **Change Tracking**
All database schema changes should be documented here with:
- **Date**: When the change was made
- **Description**: What was changed and why
- **SQL Commands**: Exact commands executed
- **Impact**: What this affects
- **Rollback**: How to undo if needed

---

## 🚀 **Migration System Schema - 2025-01-27**

### **Purpose:**
Implement database schema for existing user migration system to support the OAuth transition from individual to centralized credentials.

### **Changes Made:**

#### **1. Migration Status Tracking Table**
```sql
CREATE TABLE IF NOT EXISTS migration_status (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    error_message TEXT NULL,
    rollback_available BOOLEAN DEFAULT TRUE,
    data_preserved BOOLEAN DEFAULT TRUE,
    strava_connected BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### **2. Migration Snapshots Table**
```sql
CREATE TABLE IF NOT EXISTS migration_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'created',
    snapshot_size BIGINT NULL,
    checksum VARCHAR(64) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### **3. Migration Snapshot Data Table**
```sql
CREATE TABLE IF NOT EXISTS migration_snapshot_data (
    id SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (snapshot_id) REFERENCES migration_snapshots(snapshot_id) ON DELETE CASCADE
);
```

#### **4. Migration Notifications Table**
```sql
CREATE TABLE IF NOT EXISTS migration_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### **5. User Settings Migration Columns**
```sql
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_status VARCHAR(50) DEFAULT 'not_started';
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_completed_at TIMESTAMP NULL;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS oauth_type VARCHAR(50) DEFAULT 'individual';
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_priority INTEGER DEFAULT 0;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS last_migration_attempt TIMESTAMP NULL;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_attempts INTEGER DEFAULT 0;
```

#### **6. Performance Indexes**
```sql
CREATE INDEX IF NOT EXISTS idx_migration_status_user_id ON migration_status(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_status_status ON migration_status(status);
CREATE INDEX IF NOT EXISTS idx_migration_snapshots_user_id ON migration_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_notifications_user_id ON migration_notifications(user_id);
```

### **Impact:**
- ✅ **Migration System**: Full database support for user migration
- ✅ **Data Preservation**: Snapshot system for rollback capability
- ✅ **Status Tracking**: Complete migration progress monitoring
- ✅ **Notifications**: User communication during migration
- ✅ **Performance**: Optimized queries with proper indexing

### **Verification:**
```sql
-- Check if migration tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('migration_status', 'migration_snapshots', 'migration_snapshot_data', 'migration_notifications');

-- Check if user_settings has migration columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_settings' 
AND column_name LIKE '%migration%';
```

### **Rollback (If Needed):**
```sql
-- Drop migration tables
DROP TABLE IF EXISTS migration_notifications CASCADE;
DROP TABLE IF EXISTS migration_snapshot_data CASCADE;
DROP TABLE IF EXISTS migration_snapshots CASCADE;
DROP TABLE IF EXISTS migration_status CASCADE;

-- Remove migration columns from user_settings
ALTER TABLE user_settings DROP COLUMN IF EXISTS migration_status;
ALTER TABLE user_settings DROP COLUMN IF EXISTS migration_completed_at;
ALTER TABLE user_settings DROP COLUMN IF EXISTS oauth_type;
ALTER TABLE user_settings DROP COLUMN IF EXISTS migration_priority;
ALTER TABLE user_settings DROP COLUMN IF EXISTS last_migration_attempt;
ALTER TABLE user_settings DROP COLUMN IF EXISTS migration_attempts;
```

---

## 🎯 **Goals Setup Implementation - 2025-08-29**

### **Purpose:**
Implement missing goals setup functionality to fix broken onboarding flow.

### **Changes Made:**

#### **1. Add Goals Columns to user_settings Table**
```sql
-- Add goals-related columns
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goals_configured BOOLEAN DEFAULT FALSE;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goal_type VARCHAR(50);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goal_target VARCHAR(100);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goal_timeframe VARCHAR(50);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS goals_setup_date TIMESTAMP;
```

#### **2. Create Onboarding Analytics Table**
```sql
-- Create table for real analytics tracking
CREATE TABLE IF NOT EXISTS onboarding_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_onboarding_analytics_user_timestamp 
ON onboarding_analytics(user_id, timestamp);
```

### **Impact:**
- ✅ **Goals Setup**: Users can now set training goals
- ✅ **Analytics**: Real user behavior tracking (not hallucinated)
- ✅ **Onboarding**: Complete flow from signup to goals
- ✅ **Data Integrity**: Proper foreign key constraints

### **Verification:**
```sql
-- Check goals columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
AND column_name IN ('goals_configured', 'goal_type', 'goal_target', 'goal_timeframe', 'goals_setup_date')
ORDER BY column_name;

-- Check analytics table exists
SELECT table_name, column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'onboarding_analytics'
ORDER BY ordinal_position;
```

### **Rollback (If Needed):**
```sql
-- Remove goals columns
ALTER TABLE user_settings DROP COLUMN IF EXISTS goals_configured;
ALTER TABLE user_settings DROP COLUMN IF EXISTS goal_type;
ALTER TABLE user_settings DROP COLUMN IF EXISTS goal_target;
ALTER TABLE user_settings DROP COLUMN IF EXISTS goal_timeframe;
ALTER TABLE user_settings DROP COLUMN IF EXISTS goals_setup_date;

-- Drop analytics table
DROP TABLE IF EXISTS onboarding_analytics CASCADE;
```

---

## 📊 **Previous Changes**

### **Phase 1 Database Schema - 2025-08-27**
- Added `user_settings` table with OAuth token storage
- Added `legal_compliance` table for user agreements
- Added `oauth_security_log` table for security monitoring
- Added `token_audit_log` table for token management
- Added `llm_recommendations` table for AI recommendations

### **Initial Schema - 2025-08-26**
- Created `users` table for user accounts
- Created `activities` table for Strava activities
- Created `journal_entries` table for user notes
- Created `ai_autopsies` table for activity analysis

---

## 🔄 **Future Changes**

### **Planned Schema Updates:**
- **Goal Progress Tracking**: Add progress columns to track goal completion
- **Advanced Analytics**: Add more granular analytics tables
- **User Preferences**: Add personalization settings
- **Notification System**: Add notification preferences and history

### **Change Process:**
1. **Plan**: Document the change and its impact
2. **Review**: Get approval for schema changes
3. **Execute**: Apply via SQL Editor
4. **Verify**: Confirm changes work as expected
5. **Document**: Update this log with results

---

## 🎯 **ACWR Configuration Schema - 2025-01-27**

### **Purpose:**
Implement database schema for configurable ACWR calculations with exponential decay functionality to support enhanced training load monitoring.

### **Changes Made:**

#### **1. ACWR Configurations Table**
```sql
CREATE TABLE IF NOT EXISTS acwr_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    chronic_period_days INTEGER NOT NULL DEFAULT 28 CHECK (chronic_period_days >= 28),
    decay_rate REAL NOT NULL DEFAULT 0.05 CHECK (decay_rate > 0 AND decay_rate <= 1.0),
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER,
    notes TEXT
);
```

#### **2. User ACWR Configuration Assignments Table**
```sql
CREATE TABLE IF NOT EXISTS user_acwr_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE,
    UNIQUE(user_id, configuration_id)
);
```

#### **3. Enhanced ACWR Calculations Table**
```sql
CREATE TABLE IF NOT EXISTS enhanced_acwr_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_date DATE NOT NULL,
    configuration_id INTEGER NOT NULL,
    chronic_period_days INTEGER NOT NULL,
    decay_rate REAL NOT NULL,
    enhanced_chronic_load REAL,
    enhanced_chronic_trimp REAL,
    enhanced_acute_chronic_ratio REAL,
    enhanced_trimp_acute_chronic_ratio REAL,
    enhanced_normalized_divergence REAL,
    calculation_timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id),
    UNIQUE(user_id, activity_date, configuration_id)
);
```

#### **4. Default Configuration Insert**
```sql
INSERT INTO acwr_configurations (
    name, 
    description, 
    chronic_period_days, 
    decay_rate, 
    is_active,
    created_by,
    notes
) VALUES (
    'default_enhanced',
    'Default enhanced ACWR with 42-day chronic period and moderate decay',
    42,
    0.05,
    TRUE,
    1,
    'Default configuration for enhanced ACWR calculation'
);
```

#### **5. Performance Indexes**
```sql
CREATE INDEX IF NOT EXISTS idx_user_acwr_config_user_id ON user_acwr_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_acwr_config_config_id ON user_acwr_configurations(configuration_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_acwr_user_date ON enhanced_acwr_calculations(user_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_enhanced_acwr_config_id ON enhanced_acwr_calculations(configuration_id);
CREATE INDEX IF NOT EXISTS idx_acwr_config_active ON acwr_configurations(is_active);
```

### **Impact:**
- ✅ **Configurable ACWR**: Support for multiple ACWR calculation methods
- ✅ **Exponential Decay**: Enhanced chronic load calculation with decay weighting
- ✅ **User Assignments**: Per-user configuration management
- ✅ **Historical Tracking**: Store enhanced calculation results
- ✅ **Performance**: Optimized queries with proper indexing

### **Verification:**
```sql
-- Check if ACWR tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations');

-- Check default configuration was inserted
SELECT * FROM acwr_configurations WHERE name = 'default_enhanced';

-- Check indexes were created
SELECT indexname FROM pg_indexes WHERE indexname LIKE 'idx_%acwr%';
```

### **Rollback (If Needed):**
```sql
-- Drop ACWR tables
DROP TABLE IF EXISTS enhanced_acwr_calculations CASCADE;
DROP TABLE IF EXISTS user_acwr_configurations CASCADE;
DROP TABLE IF EXISTS acwr_configurations CASCADE;
```

---

## 🔧 **Profile Settings Fix - 2025-01-27**

### **Purpose:**
Fix missing `age` column in `user_settings` table to resolve profile settings page issues where age and gender values were not being loaded properly.

### **Changes Made:**

#### **1. Database Schema Verification**
- ✅ **Age Column Found**: The `age` column already exists in the database (INTEGER, nullable)
- ✅ **Data Confirmed**: Users have age and gender data (User 1: age=68, gender=male; User 2: age=63, gender=female)

#### **2. Code Fixes Applied**
- **Fixed Settings Profile Route**: Updated `/settings/profile` to load complete user data from database instead of just `current_user`
- **Fixed HR Zones Route**: Applied same fix to `/settings/hrzones` for consistency
- **Fixed SQL Syntax**: Corrected PostgreSQL placeholder syntax (`%s` instead of `?`)
- **Added Age Field**: Included `age` in list of updatable fields in settings API

#### **3. Streamlined Connection Tools**
- **Created Helper Script**: `scripts/quick_db_connect.py` for easy database operations
- **Updated Documentation**: Streamlined database connection instructions

### **Impact:**
- ✅ **Profile Settings**: Age and gender values now properly loaded and displayed
- ✅ **Data Integrity**: Complete user profile information available
- ✅ **User Experience**: Profile settings page works correctly
- ✅ **Developer Experience**: Streamlined database connection and troubleshooting

### **Verification Commands:**
```bash
# Quick verification using helper script
python scripts/quick_db_connect.py test
python scripts/quick_db_connect.py column user_settings age
python scripts/quick_db_connect.py sample user_settings 3
```

### **Database Connection String:**
```
postgresql://appuser:YOUR_PASSWORD@HOST:5432/train-d
```

---

**Last Updated**: 2025-01-27
**Next Review**: 2025-02-03

