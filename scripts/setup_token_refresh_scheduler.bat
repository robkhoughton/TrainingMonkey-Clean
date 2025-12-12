@echo off
echo Setting up Cloud Scheduler job for proactive token refresh...

REM Create the Cloud Scheduler job for token refresh
REM This runs daily at 5 AM UTC (before the 6 AM sync job)
gcloud scheduler jobs create http daily-token-refresh ^
    --schedule="0 5 * * *" ^
    --uri="https://strava-training-personal-382535371225.us-central1.run.app/cron/token-refresh" ^
    --http-method=POST ^
    --headers="Content-Type=application/json,X-Cloudscheduler=true" ^
    --location=us-central1 ^
    --description="Daily proactive token refresh for all users"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Token refresh scheduler job created successfully!
    echo.
    echo Job Details:
    echo - Schedule: Daily at 5:00 AM UTC
    echo - Endpoint: /cron/token-refresh
    echo - Purpose: Proactively refresh Strava tokens before they expire
    echo.
    echo This will run 1 hour before the daily sync job to ensure tokens are fresh.
) else (
    echo ❌ Failed to create token refresh scheduler job
    echo Error code: %ERRORLEVEL%
)

echo.
echo To verify the job was created, run:
echo gcloud scheduler jobs list --location=us-central1
echo.
echo To test the job manually, run:
echo gcloud scheduler jobs run daily-token-refresh --location=us-central1
