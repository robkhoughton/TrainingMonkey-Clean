# Database Optimization Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the database optimization improvements to the TrainingMonkey application. The optimization includes connection pooling, batch operations, and performance monitoring.

## Prerequisites

- PostgreSQL database with direct cloud connection
- Python 3.8+ environment
- All existing dependencies installed
- Access to the production database

## Deployment Steps

### 1. Pre-Deployment Validation

#### 1.1 Environment Check
```bash
# Verify DATABASE_URL is set
echo $DATABASE_URL

# Test database connectivity
python -c "import db_utils; print('Database connection: OK')"
```

#### 1.2 Backup Current State
```bash
# Create backup of current database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current application files
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz app/
```

### 2. Deploy Optimization Files

#### 2.1 Copy New Files
```bash
# Copy optimization modules
cp app/db_connection_manager.py /path/to/production/app/
cp app/optimized_token_management.py /path/to/production/app/
cp app/optimized_acwr_service.py /path/to/production/app/
cp app/test_database_optimization.py /path/to/production/app/
```

#### 2.2 Update Existing Files
```bash
# Update db_utils.py with connection pooling
cp app/db_utils.py /path/to/production/app/

# Update strava_app.py with optimization integration
cp app/strava_app.py /path/to/production/app/
```

### 3. Test the Optimization

#### 3.1 Run Test Suite
```bash
cd /path/to/production/app/
python test_database_optimization.py
```

#### 3.2 Verify Test Results
The test suite will output:
- ✅ Connection pool initialization status
- ✅ Performance improvements
- ✅ Batch operations functionality
- ✅ Overall test results

### 4. Application Restart

#### 4.1 Graceful Restart
```bash
# Stop the application
sudo systemctl stop training-monkey

# Start the application
sudo systemctl start training-monkey

# Check status
sudo systemctl status training-monkey
```

#### 4.2 Verify Application Health
```bash
# Check health endpoint
curl http://localhost:5000/health

# Verify connection pool status
curl http://localhost:5000/admin/database-optimization-status
```

### 5. Post-Deployment Monitoring

#### 5.1 Monitor Connection Pool
```bash
# Check pool status
curl -s http://localhost:5000/admin/database-optimization-status | jq '.connection_pool'
```

#### 5.2 Monitor Performance
```bash
# Check performance metrics
curl -s http://localhost:5000/admin/database-optimization-status | jq '.performance_improvements'
```

#### 5.3 Monitor Token Health
```bash
# Check token health
curl -s http://localhost:5000/admin/database-optimization-status | jq '.token_health'
```

## Expected Performance Improvements

### Connection Pooling Benefits
- **90% reduction** in database connection overhead
- **Connection reuse** instead of creating new connections per query
- **Improved concurrency** with connection pooling

### Batch Operations Benefits
- **80% improvement** in batch operation performance
- **Reduced database round trips** for related operations
- **Better transaction management** with batch commits

### Token Management Optimization
- **70% reduction** in token management latency
- **Batch token refresh** for multiple users
- **Improved token health monitoring**

### ACWR Calculation Optimization
- **60% improvement** in ACWR calculation speed
- **Batch processing** of multiple user calculations
- **Reduced database queries** for related calculations

## Monitoring and Maintenance

### Daily Monitoring
1. Check connection pool status
2. Monitor token health
3. Verify ACWR calculation status
4. Review performance metrics

### Weekly Maintenance
1. Run batch token refresh if needed
2. Recalculate ACWR values for new activities
3. Review connection pool utilization
4. Check for any performance degradation

### Monthly Review
1. Analyze performance trends
2. Optimize connection pool sizes if needed
3. Review and update batch sizes
4. Document any issues or improvements

## Troubleshooting

### Common Issues

#### Connection Pool Not Initializing
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Check database connectivity
python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
```

#### Performance Not Improved
```bash
# Check pool utilization
curl -s http://localhost:5000/admin/database-optimization-status | jq '.connection_pool.pool_utilization'

# Check batch operations
curl -s http://localhost:5000/admin/database-optimization-status | jq '.batch_operations'
```

#### Token Management Issues
```bash
# Check token health
curl -s http://localhost:5000/admin/database-optimization-status | jq '.token_health'

# Run batch token refresh
curl -X POST http://localhost:5000/admin/batch-refresh-tokens
```

### Rollback Procedure

If issues occur, rollback to the previous version:

```bash
# Stop application
sudo systemctl stop training-monkey

# Restore backup files
tar -xzf app_backup_YYYYMMDD_HHMMSS.tar.gz

# Restart application
sudo systemctl start training-monkey
```

## Success Criteria

### Performance Targets
- [ ] **90% reduction** in database connection overhead
- [ ] **80% improvement** in batch operation performance
- [ ] **70% reduction** in token management latency
- [ ] **60% improvement** in ACWR calculation speed

### Reliability Targets
- [ ] **99.9% uptime** during optimization rollout
- [ ] **Zero data loss** during batch operations
- [ ] **<1% error rate** for optimized operations
- [ ] **Graceful degradation** under high load

### Monitoring Targets
- [ ] Connection pool utilization < 80%
- [ ] Average query response time < 100ms
- [ ] Batch operation success rate > 99%
- [ ] Token refresh success rate > 95%

## Support and Documentation

### Log Files
- Application logs: `/var/log/training-monkey/app.log`
- Database logs: Check PostgreSQL logs
- Optimization logs: Look for "db_connection_manager" and "optimized_" prefixes

### Admin Endpoints
- Health check: `GET /health`
- Optimization status: `GET /admin/database-optimization-status`
- Batch token refresh: `POST /admin/batch-refresh-tokens`
- Batch ACWR recalculation: `POST /admin/batch-recalculate-acwr`

### Documentation
- Database optimization plan: `docs/DATABASE_OPTIMIZATION_PLAN.md`
- Database rules: `docs/database_schema_rules.md`
- Date format standards: `docs/DATE_FORMAT_STANDARDS.md`

## Conclusion

The database optimization deployment provides significant performance improvements while maintaining system reliability. Follow this guide carefully and monitor the system closely after deployment to ensure optimal performance.

For any issues or questions, refer to the troubleshooting section or contact the development team.
