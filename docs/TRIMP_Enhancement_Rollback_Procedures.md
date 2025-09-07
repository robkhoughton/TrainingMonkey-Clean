# TRIMP Enhancement Rollback Procedures

## Overview

This document provides detailed rollback procedures for the TRIMP Enhancement system. Rollback procedures are designed to be executed quickly and safely to minimize impact on users and system stability.

## Rollback Scenarios

### Scenario 1: Feature Flag Rollback (Recommended)
**Use Case**: Issues with enhanced TRIMP calculation but system is stable
**Impact**: Users revert to original TRIMP calculation method
**Time to Execute**: < 5 minutes

### Scenario 2: Application Rollback
**Use Case**: Critical system issues or application instability
**Impact**: Complete system revert to previous version
**Time to Execute**: 10-15 minutes

### Scenario 3: Database Rollback
**Use Case**: Data corruption or schema issues
**Impact**: Data revert to previous state
**Time to Execute**: 30-60 minutes

## Quick Reference

### Emergency Rollback Commands

```bash
# Immediate feature flag disable (all users)
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# Check rollback status
curl http://localhost:8080/api/admin/feature-flags

# Verify system health
curl http://localhost:8080/health
```

## Detailed Rollback Procedures

### 1. Feature Flag Rollback (Immediate)

#### Step 1: Assess Situation
```bash
# Check current system status
curl http://localhost:8080/api/admin/trimp-performance-metrics

# Check error logs
tail -f app/logs/trimp_calculation.log

# Check user feedback
curl http://localhost:8080/api/admin/feedback/summary
```

#### Step 2: Disable Feature Flags
```bash
# Disable for all user types
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "admin", "enabled": false}'

curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "beta", "enabled": false}'

curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "regular", "enabled": false}'
```

#### Step 3: Verify Rollback
```bash
# Test admin user access
python -c "from utils.feature_flags import is_feature_enabled; print('Admin access:', is_feature_enabled('enhanced_trimp_calculation', 1))"

# Test beta user access
python -c "from utils.feature_flags import is_feature_enabled; print('Beta access:', is_feature_enabled('enhanced_trimp_calculation', 2))"

# Test regular user access
python -c "from utils.feature_flags import is_feature_enabled; print('Regular access:', is_feature_enabled('enhanced_trimp_calculation', 4))"
```

#### Step 4: Monitor System
```bash
# Check system health
curl http://localhost:8080/api/admin/monitoring/dashboard

# Monitor error rates
tail -f app/logs/error.log

# Check user activity
curl http://localhost:8080/api/admin/trimp-calculation-stats
```

### 2. Gradual Rollback (Controlled)

#### Step 1: Disable for Regular Users Only
```bash
# Keep admin and beta users on enhanced system
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "regular", "enabled": false}'
```

#### Step 2: Monitor Impact
```bash
# Monitor for 15 minutes
watch -n 30 'curl -s http://localhost:8080/api/admin/trimp-performance-metrics | jq .performance_metrics.system_metrics'
```

#### Step 3: Disable for Beta Users (if needed)
```bash
# Keep only admin users on enhanced system
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "beta", "enabled": false}'
```

#### Step 4: Complete Rollback (if needed)
```bash
# Disable for admin users
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "admin", "enabled": false}'
```

### 3. Application Rollback

#### Step 1: Stop Current Application
```bash
# Find and stop application process
ps aux | grep strava_app.py
kill -TERM <process_id>

# Wait for graceful shutdown
sleep 10

# Force kill if needed
kill -KILL <process_id>
```

#### Step 2: Backup Current State
```bash
# Create backup of current deployment
cp -r app app_backup_$(date +%Y%m%d_%H%M%S)

# Backup database
cp training_data.db training_data_backup_$(date +%Y%m%d_%H%M%S).db
```

#### Step 3: Deploy Previous Version
```bash
# Use existing deployment script
./deploy_strava_simple.bat

# Or manually deploy previous version
git checkout <previous_commit_hash>
python strava_app.py &
```

#### Step 4: Verify Rollback
```bash
# Check application health
curl http://localhost:8080/health

# Test basic functionality
curl http://localhost:8080/api/admin/trimp-settings

# Check logs
tail -f app/logs/application.log
```

### 4. Database Rollback

#### Step 1: Stop Application
```bash
# Stop application to prevent data corruption
pkill -f strava_app.py
```

#### Step 2: Backup Current Database
```bash
# Create backup of current database
cp training_data.db training_data_corrupted_$(date +%Y%m%d_%H%M%S).db
```

#### Step 3: Restore Previous Database
```bash
# Restore from backup
cp training_data_backup_$(date +%Y%m%d_%H%M%S).db training_data.db

# Or restore from specific backup
cp /path/to/backup/training_data_backup.db training_data.db
```

#### Step 4: Verify Database Integrity
```bash
# Check database schema
python -c "from db_utils import execute_query; print(execute_query('SELECT name FROM sqlite_master WHERE type=\"table\"', fetch=True))"

# Check data integrity
python -c "from db_utils import execute_query; print(execute_query('SELECT COUNT(*) FROM activities', fetch=True))"
```

#### Step 5: Restart Application
```bash
# Start application
python strava_app.py &

# Verify functionality
curl http://localhost:8080/health
```

## Rollback Validation

### Post-Rollback Checklist

#### System Health
- [ ] Application is running and responsive
- [ ] All API endpoints are accessible
- [ ] Database is accessible and consistent
- [ ] No critical errors in logs
- [ ] System resources are normal

#### User Experience
- [ ] Users can access the application
- [ ] TRIMP calculations are working
- [ ] No user-facing errors
- [ ] Performance is acceptable

#### Data Integrity
- [ ] No data corruption
- [ ] Database schema is consistent
- [ ] Historical data is intact
- [ ] New data can be created

### Validation Commands

```bash
# System health check
curl http://localhost:8080/health

# Feature flag status
curl http://localhost:8080/api/admin/feature-flags

# Database connectivity
python -c "from db_utils import execute_query; print('DB OK' if execute_query('SELECT 1', fetch=True) else 'DB ERROR')"

# TRIMP calculation test
python -c "from strava_training_load import calculate_banister_trimp; print('TRIMP OK' if calculate_banister_trimp(60, 150, {'resting_hr': 50, 'max_hr': 180, 'gender': 'male'}) > 0 else 'TRIMP ERROR')"
```

## Communication Procedures

### Internal Communication

#### Immediate Notification
- **To**: Development Team, Operations Team
- **Method**: Slack/Teams, Email
- **Content**: Rollback initiated, reason, expected impact

#### Status Updates
- **Frequency**: Every 15 minutes during rollback
- **Content**: Progress, issues, expected completion time

#### Completion Notification
- **To**: All stakeholders
- **Content**: Rollback completed, system status, next steps

### User Communication

#### If Rollback is Transparent
- No user communication needed
- Users continue with original functionality

#### If Rollback Affects Users
- **Method**: In-app notification, email
- **Content**: Brief explanation, expected resolution time
- **Tone**: Professional, reassuring

## Recovery Procedures

### After Successful Rollback

#### Step 1: Root Cause Analysis
```bash
# Collect logs
tar -czf rollback_logs_$(date +%Y%m%d_%H%M%S).tar.gz app/logs/

# Analyze error patterns
grep -i error app/logs/*.log | tail -50

# Check system metrics
curl http://localhost:8080/api/admin/trimp-performance-metrics
```

#### Step 2: Fix Issues
- Identify root cause
- Develop fix
- Test fix in development environment
- Plan re-deployment

#### Step 3: Re-deployment Planning
- Schedule re-deployment
- Prepare rollback plan
- Notify stakeholders
- Execute re-deployment

### Prevention Measures

#### Monitoring Improvements
- Enhanced alerting thresholds
- Additional health checks
- Performance monitoring
- User feedback collection

#### Testing Improvements
- More comprehensive test coverage
- Load testing
- Integration testing
- User acceptance testing

## Emergency Contacts

### Primary Contacts
- **Development Lead**: [Name] - [Phone] - [Email]
- **Operations Lead**: [Name] - [Phone] - [Email]
- **On-Call Engineer**: [Name] - [Phone] - [Email]

### Escalation Path
1. **Level 1**: Development Team (0-15 minutes)
2. **Level 2**: Operations Team (15-30 minutes)
3. **Level 3**: Management Team (30+ minutes)

## Rollback Decision Matrix

| Issue Type | Severity | Recommended Action | Time to Execute |
|------------|----------|-------------------|-----------------|
| TRIMP calculation errors | Low | Gradual rollback | 15-30 minutes |
| Performance degradation | Medium | Feature flag rollback | 5-10 minutes |
| System instability | High | Application rollback | 10-15 minutes |
| Data corruption | Critical | Database rollback | 30-60 minutes |
| Security breach | Critical | Complete system rollback | 15-30 minutes |

## Post-Rollback Analysis

### Metrics to Collect
- Rollback execution time
- User impact assessment
- System performance during rollback
- Error rates before/after rollback
- User feedback and complaints

### Analysis Questions
1. What was the root cause of the issue?
2. Could the issue have been prevented?
3. Was the rollback procedure effective?
4. What improvements can be made?
5. How can we prevent similar issues?

### Documentation Updates
- Update rollback procedures based on lessons learned
- Improve monitoring and alerting
- Enhance testing procedures
- Update deployment documentation

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Date + 6 months]
