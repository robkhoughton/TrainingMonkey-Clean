# TRIMP Enhancement Deployment Documentation

## Table of Contents
1. [Overview](#overview)
2. [Deployment Architecture](#deployment-architecture)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Deployment Process](#deployment-process)
5. [Post-Deployment Validation](#post-deployment-validation)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Emergency Procedures](#emergency-procedures)

## Overview

This document provides comprehensive guidance for deploying the enhanced TRIMP calculation system. The deployment follows a phased approach with feature flags to ensure safe rollout and easy rollback if issues arise.

### Key Features Deployed
- Enhanced TRIMP calculation using heart rate stream data
- Fallback to average HR calculation when stream data unavailable
- Feature flag system for gradual rollout
- Admin controls and monitoring dashboard
- Historical data recalculation system
- Comprehensive feedback collection system
- System performance monitoring

## Deployment Architecture

### Components
1. **Core TRIMP Calculation Engine** (`strava_training_load.py`)
2. **Feature Flag System** (`utils/feature_flags.py`)
3. **Database Schema** (New fields and tables)
4. **Admin Dashboard** (`templates/admin_trimp_settings.html`)
5. **Historical Recalculation System** (`historical_trimp_recalculation.py`)
6. **Feedback Collection System** (`feedback_collection_system.py`)
7. **Monitoring Dashboard** (`system_monitoring_dashboard.py`)
8. **Deployment Monitor** (`trimp_deployment_monitor.py`)

### Deployment Phases
1. **Pre-Deployment**: Validation and preparation
2. **Deployed Disabled**: System deployed with feature flags disabled
3. **Admin Testing**: Feature enabled for admin users only
4. **Beta Rollout**: Feature enabled for beta users
5. **General Release**: Feature enabled for all users
6. **Monitoring**: Continuous monitoring and validation

## Pre-Deployment Checklist

### Database Schema Requirements
- [ ] `activities` table has `trimp_calculation_method` field
- [ ] `activities` table has `hr_stream_sample_count` field
- [ ] `activities` table has `trimp_processed_at` field
- [ ] `hr_streams` table exists with proper structure
- [ ] Database indexes are created for performance
- [ ] Schema validation passes (`get_trimp_schema_status()`)

### Code Requirements
- [ ] All Python modules are present and importable
- [ ] Feature flag system is configured
- [ ] Admin dashboard templates are deployed
- [ ] API endpoints are accessible
- [ ] Test suite passes

### Infrastructure Requirements
- [ ] Sufficient database storage for HR stream data
- [ ] Adequate server resources for enhanced calculations
- [ ] Monitoring and logging systems are operational
- [ ] Backup systems are in place

### Validation Requirements
- [ ] Pre-deployment validation passes
- [ ] Database connectivity is verified
- [ ] API endpoints respond correctly
- [ ] Admin interface is accessible

## Deployment Process

### Step 1: Pre-Deployment Validation

```bash
# Run pre-deployment validation
python deploy_trimp_enhancement.py --phase pre_deployment
```

**Expected Output:**
- All validation checks pass
- Database schema is ready
- Feature flags are configured
- Dependencies are available

### Step 2: Deploy with Feature Flags Disabled

```bash
# Deploy application
python deploy_trimp_enhancement.py --phase deploy
```

**What Happens:**
- Application is deployed to production
- Feature flags are disabled for all users
- System operates with existing TRIMP calculation
- New infrastructure is in place but not active

### Step 3: Enable Admin Testing

```bash
# Enable for admin users
python deploy_trimp_enhancement.py --phase admin_testing
```

**What Happens:**
- Feature flag enabled for admin user (user_id=1)
- Admin can test enhanced TRIMP calculation
- Validation checks are performed
- Logging and monitoring are active

### Step 4: Enable Beta Rollout

```bash
# Enable for beta users
python enable_beta_rollout.py
```

**What Happens:**
- Feature flag enabled for beta users (user_id=2, 3)
- Beta users receive enhanced TRIMP calculation
- Feedback collection is active
- Performance monitoring is enhanced

### Step 5: Enable General Release

```bash
# Enable for all users
python enable_general_release.py
```

**What Happens:**
- Feature flag enabled for all users
- Enhanced TRIMP calculation is available to everyone
- Full monitoring and feedback collection active
- System is in production mode

## Post-Deployment Validation

### Automated Validation

```bash
# Run post-deployment validation
curl -X POST http://localhost:8080/api/admin/deployment/validate \
  -H "Content-Type: application/json" \
  -d '{"validation_type": "post_deployment"}'
```

### Manual Validation Checklist

#### System Health
- [ ] All API endpoints respond correctly
- [ ] Database queries execute successfully
- [ ] Admin dashboard loads and functions
- [ ] Feature flags work as expected
- [ ] Logging is working properly

#### TRIMP Calculation
- [ ] Enhanced TRIMP calculation works with HR stream data
- [ ] Fallback to average HR works when stream data unavailable
- [ ] Calculation results are reasonable and consistent
- [ ] Performance is acceptable

#### User Experience
- [ ] Admin users can access enhanced features
- [ ] Beta users receive enhanced TRIMP calculations
- [ ] Regular users have appropriate access levels
- [ ] No user-facing errors or issues

#### Data Integrity
- [ ] Historical data recalculation works correctly
- [ ] New data is stored with proper metadata
- [ ] Database schema is consistent
- [ ] No data corruption or loss

## Rollback Procedures

### Emergency Rollback (Immediate)

If critical issues are discovered:

```bash
# Disable feature flags immediately
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

**Result:** All users revert to original TRIMP calculation method.

### Gradual Rollback

If issues are minor:

#### Step 1: Disable for Regular Users
```bash
# Keep admin and beta users on enhanced system
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "regular", "enabled": false}'
```

#### Step 2: Disable for Beta Users
```bash
# Keep only admin users on enhanced system
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "beta", "enabled": false}'
```

#### Step 3: Disable for Admin Users
```bash
# Complete rollback
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "admin", "enabled": false}'
```

### Complete System Rollback

If major issues require complete rollback:

```bash
# Revert to previous application version
deploy_strava_simple.bat

# Verify rollback
curl http://localhost:8080/health
```

## Monitoring and Maintenance

### Continuous Monitoring

The system includes comprehensive monitoring:

#### Performance Metrics
- TRIMP calculation success rate
- Processing time per calculation
- Error rates and types
- System resource usage

#### User Experience Metrics
- User satisfaction ratings
- Feature adoption rates
- User feedback and issues
- Accuracy validation results

#### System Health Metrics
- Database performance
- API response times
- Error logs and alerts
- Deployment status

### Monitoring Dashboard

Access the monitoring dashboard at:
```
http://localhost:8080/admin/trimp-settings
```

**Key Sections:**
- Feature Flag Status
- Calculation Method Statistics
- Performance Monitoring
- User Access Control
- System Health Alerts

### Automated Alerts

The system generates alerts for:
- High error rates (>5%)
- Low success rates (<90%)
- Poor accuracy (<80% within 5% of external sources)
- System performance issues
- Database connectivity problems

### Maintenance Tasks

#### Daily
- [ ] Check system health dashboard
- [ ] Review error logs
- [ ] Monitor user feedback
- [ ] Verify feature flag status

#### Weekly
- [ ] Review performance metrics
- [ ] Analyze user satisfaction data
- [ ] Check accuracy validation results
- [ ] Update monitoring thresholds if needed

#### Monthly
- [ ] Comprehensive system review
- [ ] Performance optimization
- [ ] User feedback analysis
- [ ] Documentation updates

## Troubleshooting Guide

### Common Issues

#### TRIMP Calculation Errors

**Symptoms:**
- TRIMP values are null or zero
- Calculation errors in logs
- Inconsistent results

**Diagnosis:**
```bash
# Check calculation logs
tail -f app/logs/trimp_calculation.log

# Verify HR data
curl http://localhost:8080/api/admin/trimp-calculation-stats
```

**Solutions:**
1. Check HR data quality
2. Verify HR configuration
3. Review calculation parameters
4. Check for data corruption

#### Feature Flag Issues

**Symptoms:**
- Users not receiving enhanced TRIMP
- Inconsistent access levels
- Feature flag errors

**Diagnosis:**
```bash
# Check feature flag status
curl http://localhost:8080/api/admin/feature-flags

# Test user access
python -c "from utils.feature_flags import is_feature_enabled; print(is_feature_enabled('enhanced_trimp_calculation', 1))"
```

**Solutions:**
1. Verify feature flag configuration
2. Check user ID mapping
3. Review access control logic
4. Restart application if needed

#### Performance Issues

**Symptoms:**
- Slow TRIMP calculations
- High server load
- Timeout errors

**Diagnosis:**
```bash
# Check performance metrics
curl http://localhost:8080/api/admin/trimp-performance-metrics

# Monitor system resources
top
htop
```

**Solutions:**
1. Optimize database queries
2. Increase server resources
3. Implement caching
4. Review calculation algorithms

#### Database Issues

**Symptoms:**
- Database connection errors
- Schema validation failures
- Data corruption

**Diagnosis:**
```bash
# Check database status
curl http://localhost:8080/api/admin/trimp-schema-status

# Verify database connectivity
python -c "from db_utils import execute_query; print(execute_query('SELECT 1', fetch=True))"
```

**Solutions:**
1. Check database connectivity
2. Verify schema integrity
3. Run database maintenance
4. Restore from backup if needed

### Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| TRIMP_001 | Invalid HR data | Check HR data quality and format |
| TRIMP_002 | Missing HR configuration | Verify HR config parameters |
| TRIMP_003 | Calculation timeout | Optimize calculation or increase timeout |
| TRIMP_004 | Database error | Check database connectivity and schema |
| TRIMP_005 | Feature flag error | Verify feature flag configuration |

## Emergency Procedures

### Critical System Failure

If the system becomes completely unresponsive:

1. **Immediate Response:**
   ```bash
   # Stop application
   pkill -f strava_app.py
   
   # Check system resources
   df -h
   free -m
   ```

2. **Assessment:**
   - Check server resources
   - Review error logs
   - Identify root cause

3. **Recovery:**
   ```bash
   # Restart application
   python strava_app.py
   
   # Verify health
   curl http://localhost:8080/health
   ```

4. **Rollback if needed:**
   ```bash
   # Deploy previous version
   deploy_strava_simple.bat
   ```

### Data Corruption

If data corruption is detected:

1. **Immediate Response:**
   ```bash
   # Stop all write operations
   # Disable feature flags
   # Isolate affected data
   ```

2. **Assessment:**
   - Identify scope of corruption
   - Check backup integrity
   - Plan recovery strategy

3. **Recovery:**
   ```bash
   # Restore from backup
   # Verify data integrity
   # Re-enable operations
   ```

### Security Incident

If security issues are detected:

1. **Immediate Response:**
   ```bash
   # Disable all feature flags
   # Review access logs
   # Isolate affected systems
   ```

2. **Assessment:**
   - Identify security breach
   - Assess data exposure
   - Plan remediation

3. **Recovery:**
   ```bash
   # Patch security issues
   # Reset compromised credentials
   # Re-enable systems gradually
   ```

## Contact Information

### Development Team
- **Lead Developer**: [Name]
- **Email**: [email@domain.com]
- **Phone**: [phone number]

### Operations Team
- **On-Call Engineer**: [Name]
- **Email**: [ops@domain.com]
- **Phone**: [phone number]

### Escalation Procedures
1. **Level 1**: Development Team
2. **Level 2**: Operations Team
3. **Level 3**: Management Team

## Appendices

### Appendix A: Database Schema

```sql
-- Activities table additions
ALTER TABLE activities ADD COLUMN trimp_calculation_method TEXT;
ALTER TABLE activities ADD COLUMN hr_stream_sample_count INTEGER;
ALTER TABLE activities ADD COLUMN trimp_processed_at TIMESTAMP;

-- HR streams table
CREATE TABLE hr_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    hr_data TEXT NOT NULL,
    sample_rate REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_activities_trimp_method ON activities(trimp_calculation_method);
CREATE INDEX idx_activities_trimp_processed ON activities(trimp_processed_at);
CREATE INDEX idx_hr_streams_activity ON hr_streams(activity_id);
CREATE INDEX idx_hr_streams_user ON hr_streams(user_id);
```

### Appendix B: API Endpoints

| Endpoint | Method | Description | Access |
|----------|--------|-------------|---------|
| `/api/admin/trimp-settings` | GET | Get TRIMP settings | Admin |
| `/api/admin/trimp-recalculate` | POST | Trigger recalculation | Admin |
| `/api/admin/feature-flags` | GET | Get feature flags | Admin |
| `/api/admin/feature-flags/<name>/toggle` | POST | Toggle feature flag | Admin |
| `/api/admin/trimp-calculation-stats` | GET | Get calculation statistics | Admin |
| `/api/admin/trimp-performance-metrics` | GET | Get performance metrics | Admin |
| `/api/admin/trimp-comparison` | POST | Compare calculation methods | Admin |
| `/api/feedback/submit` | POST | Submit user feedback | All users |
| `/api/feedback/accuracy-validation` | POST | Submit accuracy validation | All users |

### Appendix C: Configuration Files

#### Feature Flags Configuration
```python
# utils/feature_flags.py
feature_flags = {
    'enhanced_trimp_calculation': False,  # Global flag
    'settings_page_enabled': True,
    'admin_dashboard_enabled': True
}
```

#### Deployment Configuration
```python
# trimp_deployment_monitor.py
DEPLOYMENT_PHASES = [
    'pre_deployment',
    'deployed_disabled',
    'admin_testing',
    'beta_rollout',
    'general_release',
    'monitoring'
]
```

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Date + 3 months]
