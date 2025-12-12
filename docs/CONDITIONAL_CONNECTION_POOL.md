# Conditional Connection Pool System

## Overview

This document describes the conditional connection pool system implemented to address the dual requirements of:
1. **Onboarding operations** - Need connection pool for concurrent user registrations
2. **Sync operations** - Need reliable direct connections due to network connectivity issues

## System Architecture

### Connection Pool Usage

**Enabled for:**
- User registration and account creation
- Onboarding progress tracking
- User settings management
- Authentication operations
- Any operation that benefits from connection pooling

**Disabled for:**
- Strava sync operations
- Activity data processing
- Training load calculations
- Any operation that requires maximum reliability

### Implementation Details

#### Core Functions

```python
# Main function with conditional logic
execute_query(query, params=(), fetch=False, use_pool=False)

# Convenience functions for specific use cases
execute_query_for_onboarding(query, params=(), fetch=False)  # Uses pool
execute_query_for_sync(query, params=(), fetch=False)        # Uses direct connection
```

#### Fallback Mechanism

When `use_pool=True`:
1. **Primary**: Attempt to use connection pool
2. **Fallback**: If pool fails, automatically fall back to direct connection
3. **Logging**: Warning logged when fallback occurs

When `use_pool=False`:
1. **Direct**: Always use direct connection
2. **Reliable**: No pool dependency for sync operations

## Usage Guidelines

### For Onboarding Operations

```python
# User registration
result = execute_query_for_onboarding(
    "INSERT INTO user_settings (...) VALUES (...)",
    params, fetch=True
)

# Onboarding progress check
data = execute_query_for_onboarding(
    "SELECT * FROM user_settings WHERE id = %s",
    (user_id,), fetch=True
)
```

### For Sync Operations

```python
# Activity processing (automatic - no changes needed)
# The sync_fix.py and strava_training_load.py already use direct connections

# Manual sync operations
result = execute_query_for_sync(
    "SELECT * FROM activities WHERE user_id = %s",
    (user_id,), fetch=True
)
```

## Benefits

### For Onboarding
- **Concurrent handling**: Multiple users can register simultaneously
- **Performance**: Connection reuse reduces overhead
- **Scalability**: Pool manages connection limits efficiently

### For Sync Operations
- **Reliability**: Direct connections avoid pool initialization issues
- **Consistency**: No dependency on pool state
- **Debugging**: Easier to troubleshoot connection issues

## Monitoring

### Log Messages

**Connection Pool Usage:**
```
DEBUG: Using connection pool for operation
```

**Direct Connection Usage:**
```
DEBUG: Using direct connection (pool disabled for sync operations)
```

**Fallback Events:**
```
WARNING: Connection pool failed, falling back to direct connection: [error details]
```

### Performance Metrics

The connection pool manager tracks:
- Total connections
- Active connections
- Pool hits/misses
- Connection errors
- Slow query detection

## Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d
```

### Pool Settings

```python
# In db_connection_manager.py
minconn=2    # Minimum connections in pool
maxconn=10   # Maximum connections in pool
```

## Future Considerations

### When to Re-enable Full Pool Usage

Consider enabling the pool for all operations when:
1. Network connectivity to database is stable
2. Pool initialization issues are resolved
3. Performance monitoring shows pool benefits

### Migration Path

To migrate back to full pool usage:
1. Change `use_pool=False` to `use_pool=True` in sync operations
2. Monitor for any connection issues
3. Remove the conditional logic if stable

## Troubleshooting

### Common Issues

**Pool Initialization Fails:**
- Check network connectivity to database
- Verify DATABASE_URL is correct
- Check database server status

**Fallback to Direct Connections:**
- Normal behavior when pool is unavailable
- Monitor logs for frequency of fallbacks
- Consider investigating pool issues if frequent

**Performance Issues:**
- Monitor slow query logs
- Check connection pool statistics
- Consider adjusting pool size

## Files Modified

- `app/db_utils.py` - Core conditional logic
- `app/user_account_manager.py` - Onboarding operations
- `app/strava_app.py` - Onboarding checks
- `app/sync_fix.py` - Fixed PostgreSQL syntax (separate issue)

## Testing

### Onboarding Flow
1. Register new user
2. Complete onboarding steps
3. Verify pool usage in logs
4. Test fallback if pool fails

### Sync Flow
1. Trigger Strava sync
2. Verify direct connection usage
3. Confirm activity data is saved
4. Check HR stream data storage

This system provides the best of both worlds: reliable sync operations and efficient onboarding operations.
