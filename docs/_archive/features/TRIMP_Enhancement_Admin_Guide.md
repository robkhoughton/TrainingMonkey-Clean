# TRIMP Enhancement Admin Guide

## Overview

This guide provides administrators with comprehensive information about the new TRIMP enhancement features, how to use them, and how to manage the system effectively.

## Table of Contents
1. [New Features Summary](#new-features-summary)
2. [Admin Dashboard Access](#admin-dashboard-access)
3. [Feature Flag Management](#feature-flag-management)
4. [TRIMP Calculation Management](#trimp-calculation-management)
5. [Historical Data Recalculation](#historical-data-recalculation)
6. [Performance Monitoring](#performance-monitoring)
7. [User Feedback Management](#user-feedback-management)
8. [System Health Monitoring](#system-health-monitoring)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Best Practices](#best-practices)

## New Features Summary

### Enhanced TRIMP Calculation
- **Heart Rate Stream Processing**: Uses second-by-second heart rate data for more accurate TRIMP calculations
- **Automatic Fallback**: Falls back to average HR calculation when stream data is unavailable
- **Backward Compatibility**: Existing TRIMP calculations continue to work unchanged
- **Improved Accuracy**: More precise training load assessment, especially for interval training

### Feature Flag System
- **Gradual Rollout**: Control which users have access to enhanced features
- **User Type Management**: Separate controls for admin, beta, and regular users
- **Dynamic Toggle**: Enable/disable features without code deployment
- **Safe Rollback**: Quick reversion to original functionality if issues arise

### Admin Dashboard
- **Real-time Statistics**: Live view of calculation methods and performance
- **User Access Control**: Manage feature access for different user types
- **Performance Monitoring**: System health and calculation performance metrics
- **Method Comparison**: Compare enhanced vs. average HR calculation results

### Historical Data Processing
- **Batch Recalculation**: Update existing TRIMP values with enhanced method
- **Progress Tracking**: Monitor recalculation progress and status
- **User-specific Processing**: Recalculate for specific users or all users
- **Data Validation**: Ensure data integrity during recalculation

### Feedback Collection System
- **User Feedback**: Collect user opinions and ratings
- **Accuracy Validation**: Compare TRIMP values against external sources
- **Performance Feedback**: Monitor user experience and system performance
- **Analytics Dashboard**: View feedback trends and insights

## Admin Dashboard Access

### Accessing the Admin Dashboard

1. **Navigate to Admin Interface**:
   ```
   http://localhost:8080/admin/trimp-settings
   ```

2. **Login Requirements**:
   - Must be logged in as admin user (user_id=1)
   - Admin privileges required for all features

3. **Dashboard Sections**:
   - Feature Flag Status
   - User Access Control
   - Database Schema Status
   - Calculation Method Statistics
   - Performance Monitoring
   - Historical Recalculation Controls
   - Method Comparison Tools

### Dashboard Overview

The admin dashboard provides a comprehensive view of the TRIMP enhancement system:

- **Status Cards**: Quick overview of system health and feature status
- **Real-time Metrics**: Live performance and usage statistics
- **Interactive Controls**: Direct management of feature flags and settings
- **Alert System**: Notifications for system issues or performance concerns

## Feature Flag Management

### Understanding Feature Flags

Feature flags control which users have access to the enhanced TRIMP calculation:

- **Global Flag**: Master switch for the entire feature
- **User Type Flags**: Separate controls for admin, beta, and regular users
- **Dynamic Control**: Changes take effect immediately without restart

### Managing Feature Flags

#### Enable Enhanced TRIMP for Admin Users
```bash
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "admin", "enabled": true}'
```

#### Enable Enhanced TRIMP for Beta Users
```bash
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "beta", "enabled": true}'
```

#### Enable Enhanced TRIMP for All Users
```bash
curl -X POST http://localhost:8080/api/admin/feature-flags/enhanced_trimp_calculation/toggle \
  -H "Content-Type: application/json" \
  -d '{"user_type": "regular", "enabled": true}'
```

#### Check Current Feature Flag Status
```bash
curl http://localhost:8080/api/admin/feature-flags
```

### Rollout Strategy

**Recommended Rollout Sequence**:
1. **Admin Testing**: Enable for admin users first
2. **Beta Rollout**: Enable for beta users after admin validation
3. **General Release**: Enable for all users after beta feedback
4. **Monitoring**: Continuous monitoring and validation

## TRIMP Calculation Management

### Understanding Enhanced TRIMP Calculation

The enhanced TRIMP calculation provides more accurate training load assessment by:

- **Processing Heart Rate Streams**: Uses second-by-second HR data when available
- **Improved Accuracy**: Better reflects actual training intensity
- **Interval Training Support**: More accurate for variable intensity workouts
- **Automatic Fallback**: Uses average HR when stream data unavailable

### Calculation Method Statistics

View detailed statistics about TRIMP calculation methods:

- **Method Distribution**: Percentage of activities using each method
- **Performance Metrics**: Success rates and error counts
- **User Statistics**: Method usage by user
- **Trend Analysis**: Changes over time

### Method Comparison Tools

Compare TRIMP calculation methods for specific activities:

1. **Select User**: Choose user to analyze
2. **Set Time Range**: Specify days back to analyze
3. **Choose Activity Count**: Number of activities to compare
4. **Run Comparison**: Generate side-by-side comparison

**Comparison Results Include**:
- Enhanced TRIMP vs. Average HR TRIMP
- Difference in values
- Percentage difference
- Activities with HR stream data

## Historical Data Recalculation

### When to Use Historical Recalculation

Recalculate historical TRIMP values when:
- Enhanced TRIMP calculation is first enabled
- HR stream data becomes available for existing activities
- Calculation algorithm improvements are made
- Data quality issues are identified

### Starting Historical Recalculation

#### Using the Admin Dashboard
1. Navigate to the "Actions" section
2. Configure recalculation parameters:
   - **User ID**: Specific user or leave empty for all users
   - **Days Back**: Time range to process
   - **Force Recalculation**: Override recently processed activities
3. Click "Start Recalculation"
4. Monitor progress in the "Recalculation Status" section

#### Using API Endpoints
```bash
curl -X POST http://localhost:8080/api/admin/trimp-recalculate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "days_back": 30,
    "force_recalculation": false
  }'
```

### Monitoring Recalculation Progress

- **Real-time Status**: View current progress and statistics
- **Error Tracking**: Monitor failed calculations and errors
- **Completion Notifications**: Alerts when recalculation completes
- **Performance Metrics**: Processing speed and resource usage

### Recalculation Best Practices

- **Start Small**: Begin with recent activities or specific users
- **Monitor Performance**: Watch system resources during processing
- **Validate Results**: Check calculation accuracy after completion
- **Backup Data**: Ensure data backup before large recalculations

## Performance Monitoring

### System Performance Metrics

Monitor key performance indicators:

- **Calculation Success Rate**: Percentage of successful TRIMP calculations
- **Processing Time**: Average time per calculation
- **Error Rates**: Frequency and types of calculation errors
- **Resource Usage**: CPU, memory, and database performance

### Performance Alerts

The system automatically generates alerts for:

- **High Error Rates**: >5% calculation failures
- **Performance Degradation**: Slow response times
- **Resource Issues**: High CPU or memory usage
- **Data Quality Problems**: Invalid or missing data

### Performance Optimization

- **Database Indexing**: Ensure proper indexes for HR stream queries
- **Caching**: Implement caching for frequently accessed data
- **Batch Processing**: Process activities in batches for efficiency
- **Resource Monitoring**: Monitor system resources and scale as needed

## User Feedback Management

### Feedback Collection

The system collects feedback through:

- **User Feedback Forms**: Direct user input and ratings
- **Accuracy Validation**: Comparison with external sources
- **Performance Feedback**: User experience and system performance
- **Bug Reports**: Issue reporting and resolution tracking

### Viewing Feedback

#### Feedback Summary
```bash
curl http://localhost:8080/api/admin/feedback/summary
```

#### Recent Feedback
```bash
curl http://localhost:8080/api/admin/feedback/recent
```

#### Accuracy Validations
```bash
curl http://localhost:8080/api/admin/feedback/accuracy-validations
```

### Feedback Analysis

- **Satisfaction Scores**: User ratings and feedback trends
- **Accuracy Metrics**: Comparison with external TRIMP sources
- **Issue Tracking**: Common problems and resolution status
- **Feature Requests**: User suggestions and enhancement ideas

## System Health Monitoring

### Health Dashboard

Monitor overall system health:

- **Overall Health Score**: Composite system health metric
- **Active Alerts**: Current system issues and warnings
- **Deployment Status**: Current deployment phase and status
- **User Satisfaction**: Current user satisfaction levels

### Health Metrics

- **System Uptime**: Application availability and stability
- **Database Health**: Database performance and connectivity
- **API Performance**: Response times and error rates
- **User Activity**: Active users and system usage

### Health Alerts

- **Critical Alerts**: System-threatening issues requiring immediate attention
- **Warning Alerts**: Performance issues that should be monitored
- **Info Alerts**: Informational messages about system status

## Troubleshooting Guide

### Common Issues and Solutions

#### TRIMP Calculation Errors

**Problem**: TRIMP values are null or zero
**Solutions**:
1. Check HR data quality and format
2. Verify HR configuration parameters
3. Review calculation logs for errors
4. Validate input data integrity

#### Feature Flag Issues

**Problem**: Users not receiving enhanced TRIMP
**Solutions**:
1. Verify feature flag configuration
2. Check user ID mapping and access levels
3. Review feature flag logic
4. Restart application if needed

#### Performance Issues

**Problem**: Slow TRIMP calculations
**Solutions**:
1. Optimize database queries and indexes
2. Increase server resources
3. Implement caching strategies
4. Review calculation algorithms

#### Database Issues

**Problem**: Database connection or schema errors
**Solutions**:
1. Check database connectivity
2. Verify schema integrity
3. Run database maintenance
4. Restore from backup if needed

### Diagnostic Commands

#### Check System Health
```bash
curl http://localhost:8080/health
```

#### Verify Feature Flags
```bash
curl http://localhost:8080/api/admin/feature-flags
```

#### Check Database Schema
```bash
curl http://localhost:8080/api/admin/trimp-schema-status
```

#### View Performance Metrics
```bash
curl http://localhost:8080/api/admin/trimp-performance-metrics
```

### Log Analysis

#### TRIMP Calculation Logs
```bash
tail -f app/logs/trimp_calculation.log
```

#### Application Logs
```bash
tail -f app/logs/application.log
```

#### Error Logs
```bash
tail -f app/logs/error.log
```

## Best Practices

### Deployment Management

1. **Gradual Rollout**: Always use feature flags for gradual deployment
2. **Monitor Closely**: Watch system performance during rollout
3. **Validate Results**: Verify calculation accuracy after deployment
4. **Have Rollback Plan**: Be prepared to rollback if issues arise

### User Management

1. **Admin Testing**: Test with admin users before broader rollout
2. **Beta Validation**: Use beta users for validation and feedback
3. **User Communication**: Inform users about new features
4. **Feedback Collection**: Actively collect and respond to user feedback

### System Maintenance

1. **Regular Monitoring**: Check system health daily
2. **Performance Optimization**: Continuously optimize system performance
3. **Data Validation**: Regularly validate data integrity
4. **Backup Strategy**: Maintain regular data backups

### Security Considerations

1. **Access Control**: Ensure proper admin access controls
2. **Data Privacy**: Protect user data and privacy
3. **Audit Logging**: Maintain audit logs for admin actions
4. **Secure Communication**: Use secure communication channels

## API Reference

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/trimp-settings` | GET | Admin dashboard interface |
| `/api/admin/feature-flags` | GET | Get feature flag status |
| `/api/admin/feature-flags/<name>/toggle` | POST | Toggle feature flag |
| `/api/admin/trimp-calculation-stats` | GET | Get calculation statistics |
| `/api/admin/trimp-performance-metrics` | GET | Get performance metrics |
| `/api/admin/trimp-comparison` | POST | Compare calculation methods |
| `/api/admin/trimp-recalculate` | POST | Start historical recalculation |
| `/api/admin/trimp-operations` | GET | Get recalculation operations |
| `/api/admin/feedback/summary` | GET | Get feedback summary |
| `/api/admin/monitoring/dashboard` | GET | Get monitoring dashboard |

### User Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/feedback/submit` | POST | Submit user feedback |
| `/api/feedback/accuracy-validation` | POST | Submit accuracy validation |

## Support and Resources

### Documentation
- **Deployment Guide**: `docs/TRIMP_Enhancement_Deployment_Documentation.md`
- **Rollback Procedures**: `docs/TRIMP_Enhancement_Rollback_Procedures.md`
- **API Documentation**: Available in admin dashboard

### Scripts and Tools
- **Beta Rollout**: `app/enable_beta_rollout.py`
- **General Release**: `app/enable_general_release.py`
- **Deployment Monitor**: `app/trimp_deployment_monitor.py`

### Contact Information
- **Development Team**: [Contact Information]
- **Operations Team**: [Contact Information]
- **Emergency Support**: [Contact Information]

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Date + 3 months]
