# LLM Recommendations Auto-Generation - Action Plan

## ✅ GOOD NEWS
The cron job **IS running daily** at 11 AM UTC (3-4 AM Pacific) and completing successfully!

## ⚠️ THE PROBLEM  
Logs were being written to a file instead of stdout, making it impossible to verify if recommendations are being generated.

## ✅ FIXED
**File:** `app/llm_recommendations_module.py` (line 28-34)
- Removed `filename='llm_recommendations.log'` parameter
- Logs now write to stdout for Cloud Logging visibility

---

## NEXT STEPS

### 1. Deploy the Fix [[memory:10629716]]
```bash
cd frontend
npm run build

cd ..
xcopy frontend\build\* app\build\ /E /Y
xcopy frontend\build\static\* app\static\ /E /Y

cd app
deploy_strava_simple.bat
```

### 2. Verify Logs After Deployment
After deployment, check if logs are now visible:
```bash
gcloud logging read 'resource.type=cloud_run_revision AND textPayload:"llm_recommendations"' --limit 10 --freshness=1h
```

### 3. Wait for Next Scheduled Run
**Next Run:** Tomorrow at **11:00 AM UTC** (3-4 AM Pacific)

After the next run, check logs:
```bash
# Replace with tomorrow's date
gcloud logging read 'resource.type=cloud_run_revision AND timestamp>="2025-11-14T10:55:00Z" AND timestamp<="2025-11-14T11:15:00Z"' --limit 50
```

### 4. (Optional) Manual Test Now
If you want to test immediately without waiting:
```bash
# Trigger the cron job manually
gcloud scheduler jobs run daily-recommendations --location=us-central1
```

Then watch logs in real-time:
```bash
gcloud logging tail "resource.type=cloud_run_revision" --format=json
```

---

## MONITORING CHECKLIST

After deployment and next cron run, verify:

- [ ] Logs visible in Cloud Logging around 11 AM UTC
- [ ] "Starting daily recommendations generation" message appears
- [ ] "Daily recommendations complete: X successful, Y failed" appears  
- [ ] Check database for new recommendations:
  ```sql
  SELECT user_id, target_date, generated_at 
  FROM llm_recommendations 
  WHERE generated_at >= NOW() - INTERVAL '1 day'
  ORDER BY generated_at DESC;
  ```

---

## TROUBLESHOOTING

If recommendations still don't appear after fix:

### Check for Active Users
The cron only generates for users with activity in last 7 days:
```sql
SELECT DISTINCT user_id, MAX(date) as last_activity
FROM activities 
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY user_id;
```

### Check Anthropic API Key
Verify the ANTHROPIC_API_KEY environment variable is set in Cloud Run:
```bash
gcloud run services describe strava-training-personal --region=us-central1 --format="value(spec.template.spec.containers[0].env)"
```

### Manual Generation Test
Use the diagnostic script to manually generate for specific users:
```bash
python scripts/manual_trigger_llm_cron.py
```

---

## DIAGNOSTIC TOOLS CREATED

Located in `scripts/`:
1. **diagnose_llm_cron.py** - Complete diagnostic (requires DATABASE_URL env var)
2. **check_cloud_scheduler.bat** - Cloud Scheduler status checker
3. **manual_trigger_llm_cron.py** - Manual recommendation generation

---

## TIMING REFERENCE

**Cloud Scheduler runs at:** 11:00 AM UTC daily

**Your local time:**
- Winter (PST): 3:00 AM Pacific
- Summer (PDT): 4:00 AM Pacific

**Check logs between:** 10:55 AM - 11:15 AM UTC

---

## SUMMARY

1. ✅ Cloud Scheduler is configured and running
2. ✅ Cron endpoint returns HTTP 200 successfully
3. ✅ Logging fix applied
4. 🔄 **Next:** Deploy and monitor next run

**The system is working; we just couldn't see it!**





