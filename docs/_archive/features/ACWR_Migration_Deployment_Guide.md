# ACWR Configuration System - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ACWR Configuration System to production PostgreSQL database.

## Prerequisites

- Access to production PostgreSQL database (Google Cloud SQL)
- SQL Editor access (Google Cloud Console or pgAdmin)
- Database admin privileges
- Backup of current database (recommended)

## Deployment Steps

### 1. Pre-Deployment Checklist

- [ ] Database backup completed
- [ ] Migration script reviewed and approved
- [ ] Rollback plan prepared
- [ ] Deployment window scheduled
- [ ] Team notified of deployment

### 2. Execute Production Verification Script

**File**: `app/acwr_migration_script.sql`

**Note**: This script assumes the ACWR tables, indexes, and default configuration have already been created via the initial schema execution.

1. **Open SQL Editor** in Google Cloud Console
2. **Copy the verification script** from `app/acwr_migration_script.sql`
3. **Execute the script** in your production database
4. **Verify all checks pass** - the script will report SUCCESS or ERROR for each verification step

### 3. Expected Results

After successful execution, you should see:

```
verification_type        | count
-------------------------|-------
Tables Ready            | 3
Indexes Ready           | 8+
Default Configuration   | 1
Constraints Active      | 10+
```

**Console Output**: The script will also display SUCCESS messages for each verification step:
- ✅ All required ACWR tables exist
- ✅ Default configuration verified
- ✅ All required performance indexes exist
- ✅ All configurations pass constraint validation

### 4. Post-Deployment Verification

#### 4.1 Database Structure Verification

Execute these queries to verify the schema:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations');

-- Check default configuration
SELECT * FROM acwr_configurations WHERE name = 'default_enhanced';

-- Check indexes
SELECT indexname, tablename FROM pg_indexes 
WHERE tablename IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
ORDER BY tablename, indexname;
```

#### 4.2 Application Integration Test

1. **Deploy updated application code** with ACWR configuration service
2. **Test database connectivity** using the test script:
   ```bash
   python app/test_acwr_database_connectivity.py
   ```
3. **Verify service functionality** through admin interface

### 5. Rollback Procedure

If issues are encountered and you need to remove the ACWR system:

```sql
-- Rollback ACWR Configuration System
BEGIN;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS enhanced_acwr_calculations CASCADE;
DROP TABLE IF EXISTS user_acwr_configurations CASCADE;
DROP TABLE IF EXISTS acwr_configurations CASCADE;

COMMIT;
```

**Note**: This rollback procedure should only be used if the initial schema creation needs to be undone. The verification script itself does not modify data.

### 6. Monitoring and Maintenance

#### 6.1 Performance Monitoring

Monitor these metrics after deployment:

- Query performance on ACWR tables
- Index usage statistics
- Table growth rates
- Connection pool utilization

#### 6.2 Data Integrity Checks

Run periodic checks:

```sql
-- Check for orphaned records
SELECT COUNT(*) FROM user_acwr_configurations uac
LEFT JOIN acwr_configurations ac ON uac.configuration_id = ac.id
WHERE ac.id IS NULL;

-- Check for invalid configurations
SELECT * FROM acwr_configurations 
WHERE chronic_period_days < 28 OR decay_rate <= 0 OR decay_rate > 1.0;
```

### 7. Feature Flag Rollout

After successful deployment:

1. **Enable feature flag** for admin user (user_id=1)
2. **Test enhanced calculations** with admin account
3. **Gradually enable** for beta users (user_ids 2, 3)
4. **Monitor performance** and calculation accuracy
5. **Full rollout** to all users

### 8. Troubleshooting

#### Common Issues

**Issue**: Migration script fails with constraint errors
- **Solution**: Check for existing data conflicts, use `ON CONFLICT` clauses

**Issue**: Index creation fails
- **Solution**: Verify table creation succeeded, check for naming conflicts

**Issue**: Default configuration not inserted
- **Solution**: Check for existing 'default_enhanced' record, use `ON CONFLICT DO NOTHING`

#### Support Contacts

- **Database Issues**: Database Administrator
- **Application Issues**: Development Team
- **Performance Issues**: DevOps Team

### 9. Documentation Updates

After successful deployment, update:

- [ ] `docs/database_changes.md` with deployment results
- [ ] Application documentation with new features
- [ ] Admin user guide with ACWR configuration instructions
- [ ] API documentation with new endpoints

### 10. Success Criteria

Deployment is considered successful when:

- [ ] All tables and indexes created without errors
- [ ] Default configuration accessible via application
- [ ] Database connectivity test passes
- [ ] ACWR configuration service functions correctly
- [ ] No performance degradation observed
- [ ] Feature flags can be toggled successfully

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Verification Completed By**: _______________
**Status**: _______________

## Related Files

- `app/acwr_migration_script.sql` - Main migration script
- `app/test_acwr_database_connectivity.py` - Connectivity test
- `docs/acwr_schema_verification.sql` - Schema verification queries
- `app/acwr_configuration_service.py` - Core service implementation
