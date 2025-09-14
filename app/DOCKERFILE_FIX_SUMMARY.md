# Dockerfile Fix Summary - Missing exponential_decay_engine.py

## Issue Identified
**Error**: `ModuleNotFoundError: No module named 'exponential_decay_engine'`

**Root Cause**: The `exponential_decay_engine.py` module was missing from the Dockerfile COPY statements, even though it exists in the codebase and is imported by multiple ACWR services.

## Fix Applied
✅ **Added missing COPY statement to Dockerfile.strava:**

```dockerfile
# Copy ACWR Configuration and Calculation Services
COPY acwr_calculation_service.py .
COPY acwr_configuration_service.py .
COPY acwr_configuration_admin.py .
COPY exponential_decay_engine.py .  # ← ADDED THIS LINE
```

## Files That Import exponential_decay_engine
The following ACWR services import this module:
- `acwr_configuration_service.py` (line 12)
- `acwr_migration_service.py` (line 21)

## Module Dependencies
✅ **No external dependencies** - `exponential_decay_engine.py` only uses:
- Standard Python libraries: `math`, `logging`, `datetime`, `typing`, `dataclasses`
- No additional packages required

## Verification
✅ **File exists**: `exponential_decay_engine.py` confirmed present in `/app/` directory
✅ **Import structure**: Uses standard Python imports only
✅ **Dockerfile updated**: COPY statement added to include the module

## Impact
- **Build Time**: No change (file already exists)
- **Runtime**: No change (no new dependencies)
- **Functionality**: Fixes import error that was preventing service startup

## Next Steps
1. **Rebuild Docker image** with updated Dockerfile
2. **Deploy to Cloud Run**
3. **Verify service starts successfully**
4. **Test ACWR functionality**

## Files Modified
- `app/Dockerfile.strava` - Added COPY statement for `exponential_decay_engine.py`

## Status
✅ **FIXED** - Ready for rebuild and deployment

