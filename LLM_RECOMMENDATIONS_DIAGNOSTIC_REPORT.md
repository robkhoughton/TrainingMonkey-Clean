# LLM Recommendations Auto-Generation Diagnostic Report

**Date:** November 13, 2025  
**Issue:** LLM recommendations not appearing to be auto-generated daily  
**Status:** ✅ IDENTIFIED - System IS running, but visibility issue

---

## FINDINGS

### ✅ Cloud Scheduler Status
- **Job Name:** `daily-recommendations`
- **Schedule:** 11:00 AM UTC daily (3-4 AM Pacific)
- **Status:** ENABLED
- **Last Execution:** Nov 12, 2025 at 11:00:01 UTC
- **Result:** HTTP 200 (Success)
- **Execution Time:** 96 seconds

### ✅ Cron Endpoint Executions
```
Nov 12, 2025 11:00:01 UTC - HTTP 200, 96 seconds
Nov 11, 2025 11:00:06 UTC - HTTP 200, 99 seconds
```

Both executions completed successfully with HTTP 200 responses.

### ⚠️ PRIMARY ISSUE: Log Visibility

**Problem:** Application logs from cron execution are NOT visible in Cloud Logging.

**Root Cause:** The LLM recommendations module configures logging to write to a FILE instead of stdout:

```python
# Line 29-34 in llm_recommendations_module.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='llm_recommendations.log'  # ⚠️ Writing to file, not stdout!
)
```

**Impact:**
- Logs are written to `llm_recommendations.log` inside the container
- Logs are NOT sent to Cloud Logging (stdout/stderr)
- Cannot verify if recommendations are actually being generated
- No visibility into failures or success rates

---

## SECONDARY FINDINGS

### ⚠️ Performance Issue
- Cron executions taking 96-99 seconds
- Close to Cloud Run timeout limits
- May cause intermittent timeouts if user count increases

### ⚠️ Code Quality Issues Found
Multiple errors in production logs (unrelated to LLM cron):
1. `AttributeError: module 'db_utils' has no attribute 'get_connection'` 
2. `UndefinedColumn: column "hr_stream_data" of relation "activities" does not exist`

---

## IMMEDIATE ACTIONS REQUIRED

### 1. Fix Logging Configuration (CRITICAL)

**File:** `app/llm_recommendations_module.py` (lines 29-34)

**Current (BAD):**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='llm_recommendations.log'  # Writes to file
)
```

**Should Be:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # NO filename parameter - logs to stdout
)
```

### 2. Verify Recommendations Are Being Generated

Run diagnostic query to check recent recommendations:

```sql
SELECT 
    user_id,
    target_date,
    generation_date,
    generated_at,
    is_autopsy_informed
FROM llm_recommendations
WHERE generated_at >= NOW() - INTERVAL '7 days'
ORDER BY generated_at DESC;
```

### 3. Manual Test Execution

Test the cron endpoint manually:

```bash
# Option A: Via gcloud (triggers actual scheduler)
gcloud scheduler jobs run daily-recommendations --location=us-central1

# Option B: Via diagnostic script
python scripts/manual_trigger_llm_cron.py
```

---

## INVESTIGATION COMMANDS

### Check Cloud Scheduler
```bash
# List all jobs
gcloud scheduler jobs list --location=us-central1

# Get job details
gcloud scheduler jobs describe daily-recommendations --location=us-central1
```

### Check Cron Execution Logs
```bash
# Recent cron requests
gcloud logging read 'resource.type=cloud_run_revision AND httpRequest.requestUrl:"/cron/daily-recommendations"' --limit 10 --freshness=48h

# All logs from specific time window (adjust date)
gcloud logging read 'resource.type=cloud_run_revision AND timestamp>="2025-11-13T10:59:00Z" AND timestamp<="2025-11-13T11:02:00Z"' --limit 100
```

### Check for Errors
```bash
# Recent errors
gcloud logging read 'resource.type=cloud_run_revision AND severity>=ERROR' --limit 20 --freshness=24h
```

---

## NEXT STEPS

1. **CRITICAL:** Fix logging configuration in `llm_recommendations_module.py`
2. **VERIFY:** Check database for recent recommendations
3. **TEST:** Manually trigger cron to verify it works
4. **DEPLOY:** Push logging fix to production
5. **MONITOR:** Watch Cloud Logging after next scheduled run (tomorrow 11 AM UTC)

---

## TIMEZONE REFERENCE

**Cron Schedule:** 11:00 AM UTC  
**Converts to:**
- 3:00 AM PST (Pacific Standard Time - Winter)
- 4:00 AM PDT (Pacific Daylight Time - Summer)

**Check logs around:** 10:55 AM - 11:15 AM UTC

---

## FILES CREATED

Diagnostic tools created in `scripts/`:
- `diagnose_llm_cron.py` - Full diagnostic tool
- `check_cloud_scheduler.bat` - Cloud Scheduler checker
- `manual_trigger_llm_cron.py` - Manual trigger for testing

---

## CONCLUSION

The system **IS WORKING** - Cloud Scheduler is executing the cron job successfully. However, we cannot verify if recommendations are actually being generated because logs are being written to a file instead of stdout. 

**Fix the logging configuration first, then verify operation.**




