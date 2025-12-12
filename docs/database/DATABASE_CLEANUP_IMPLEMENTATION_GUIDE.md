# Database Cleanup Implementation Guide

**Date**: 2025-01-10  
**Purpose**: Clean up redundant ACWR calculation tables  
**Status**: Implementation Ready

## 🎯 **Overview**

This guide implements the cleanup of redundant database tables:
- **Keep**: `acwr_enhanced_calculations` (migration system table)
- **Remove**: `enhanced_acwr_calculations` (redundant configuration table)

## 📋 **Implementation Steps**

### **Step 1: Analysis (REQUIRED FIRST)**

Run the analysis script to understand current data:

```sql
-- Execute this script first
\i sql/database_cleanup_analysis.sql
```

**What to look for:**
- Which table has data
- Data distribution by user
- Date ranges
- Data quality issues

### **Step 2: Data Migration (IF NEEDED)**

**Only run if `enhanced_acwr_calculations` has data:**

```sql
-- Execute only if enhanced_acwr_calculations has data
\i sql/migrate_enhanced_calculations_data.sql
```

**Verification:**
- Check migration results
- Verify no data loss
- Test application functionality

### **Step 3: Code Updates (COMPLETED)**

**Files Updated:**
- ✅ `app/acwr_configuration_service.py` - Updated to use `acwr_enhanced_calculations`
- ✅ `app/verify_acwr_system_health.py` - Updated table reference

**Changes Made:**
- Updated table name from `enhanced_acwr_calculations` to `acwr_enhanced_calculations`
- Updated column mapping to match migration system schema
- Added activity_id lookup functionality

### **Step 4: Final Cleanup**

**After verifying everything works:**

```sql
-- Execute final cleanup
\i sql/database_cleanup_final.sql
```

**This will:**
- Drop `enhanced_acwr_calculations` table
- Drop backup tables
- Update table statistics
- Verify cleanup

## 🔍 **Verification Checklist**

### **Before Cleanup:**
- [ ] Analysis script shows current state
- [ ] Data migration completed (if needed)
- [ ] Application tested with new code
- [ ] All functionality working

### **After Cleanup:**
- [ ] Only `acwr_enhanced_calculations` table exists
- [ ] Application still works correctly
- [ ] Configuration comparison chart works
- [ ] No database errors in logs

## 🚨 **Rollback Plan**

**If something goes wrong:**

### **Option 1: Restore from Backup**
```sql
-- If backup table exists
CREATE TABLE enhanced_acwr_calculations AS 
SELECT * FROM enhanced_acwr_calculations_backup;
```

### **Option 2: Recreate Table**
```sql
-- Recreate the original table structure
CREATE TABLE enhanced_acwr_calculations (
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
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id)
);
```

### **Option 3: Revert Code Changes**
- Revert changes to `acwr_configuration_service.py`
- Revert changes to `verify_acwr_system_health.py`

## 📊 **Expected Benefits**

### **Immediate Benefits:**
- ✅ **Eliminates confusion** between similar table names
- ✅ **Reduces maintenance burden** (one table instead of two)
- ✅ **Improves code clarity** (no table selection logic)
- ✅ **Prevents future errors** (no schema mismatches)

### **Long-term Benefits:**
- ✅ **Easier database maintenance**
- ✅ **Simpler backup/restore procedures**
- ✅ **Clearer data model**
- ✅ **Reduced development complexity**

## 🔧 **Technical Details**

### **Table Schema (Final)**
```sql
CREATE TABLE acwr_enhanced_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,
    acwr_ratio DECIMAL(10,4),
    acute_load DECIMAL(10,2),
    chronic_load DECIMAL(10,2),
    calculation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculation_method VARCHAR(50) DEFAULT 'enhanced',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### **Code Changes Summary**
1. **Table Reference**: `enhanced_acwr_calculations` → `acwr_enhanced_calculations`
2. **Column Mapping**: Updated to match migration system schema
3. **Activity Lookup**: Added `_get_activity_id_by_date()` method
4. **Parameter Mapping**: Updated to use correct column names

## 📝 **Post-Implementation**

### **Documentation Updates:**
- [ ] Update database schema documentation
- [ ] Update API documentation
- [ ] Update development guidelines

### **Monitoring:**
- [ ] Monitor application logs for database errors
- [ ] Verify configuration comparison chart works
- [ ] Check ACWR calculation performance

### **Future Maintenance:**
- [ ] Regular table statistics updates
- [ ] Monitor table growth
- [ ] Consider partitioning for large datasets

## 🎯 **Success Criteria**

**The cleanup is successful when:**
1. ✅ Only `acwr_enhanced_calculations` table exists
2. ✅ Application works without errors
3. ✅ Configuration comparison chart displays data
4. ✅ All ACWR calculations work correctly
5. ✅ No database schema errors in logs

---

**Implementation Status**: Ready for execution  
**Risk Level**: Low (with proper backup and testing)  
**Estimated Time**: 30-60 minutes (including testing)
