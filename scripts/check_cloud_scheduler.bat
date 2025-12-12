@echo off
REM Check Cloud Scheduler configuration for LLM recommendations
REM This script checks if the daily recommendations cron job is properly configured

echo.
echo ======================================================
echo   CLOUD SCHEDULER DIAGNOSTIC FOR LLM RECOMMENDATIONS
echo ======================================================
echo.

echo [1/5] Checking if Cloud Scheduler jobs exist...
echo.
gcloud scheduler jobs list
echo.

echo.
echo [2/5] Getting details of daily-recommendations job...
echo.
gcloud scheduler jobs describe daily-recommendations --location=us-central1 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: daily-recommendations job not found!
    echo You may need to create it or check the location.
    echo.
)

echo.
echo [3/5] Checking recent Cloud Run logs for cron activity...
echo.
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~\"daily recommendations\"" --limit 20 --format="table(timestamp,textPayload)" --freshness=24h

echo.
echo [4/5] Checking for cron errors in last 24 hours...
echo.
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~\"cron\" AND severity>=ERROR" --limit 10 --format="table(timestamp,severity,textPayload)" --freshness=24h

echo.
echo [5/5] Checking Cloud Run service configuration...
echo.
gcloud run services describe strava-training-app --region=us-central1 --format="table(status.url,status.conditions[0].status,status.conditions[0].reason)"

echo.
echo ======================================================
echo   DIAGNOSTIC COMPLETE
echo ======================================================
echo.
echo To manually trigger the cron job for testing:
echo   gcloud scheduler jobs run daily-recommendations --location=us-central1
echo.
echo To view real-time logs:
echo   gcloud logging tail "resource.type=cloud_run_revision"
echo.

pause







