@echo off
REM Configure SMTP for TrainingMonkey Cloud Run Service
REM This will enable email notifications for new user registrations

echo ==========================================
echo SMTP Configuration for Cloud Run
echo ==========================================
echo.
echo BEFORE RUNNING THIS SCRIPT:
echo 1. Generate Gmail App Password at: https://myaccount.google.com/apppasswords
echo 2. Replace YOUR_APP_PASSWORD below with the generated password
echo.
echo ==========================================
echo.

REM EDIT THIS: Replace with your actual Gmail app password
set APP_PASSWORD=gfks tkir hfyz lsbj

REM Your service name (update if different)
set SERVICE_NAME=strava-training-personal

REM Your Google Cloud region (update if different)
set REGION=us-central1

echo Configuring SMTP environment variables...
echo.

gcloud run services update %SERVICE_NAME% ^
  --region=%REGION% ^
  --set-env-vars="SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,SMTP_USERNAME=rob.houghton.ca@gmail.com,SMTP_PASSWORD=%APP_PASSWORD%,FROM_EMAIL=rob.houghton.ca@gmail.com,FROM_NAME=TrainingMonkey Notifications"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo SUCCESS!
    echo ==========================================
    echo SMTP has been configured for Cloud Run.
    echo.
    echo Future user registrations will now trigger email notifications to:
    echo   rob.houghton.ca@gmail.com
    echo.
    echo Test it by:
    echo 1. Creating a test Strava account
    echo 2. Registering on yourtrainingmonkey.com
    echo 3. Check your email for the notification
    echo.
) else (
    echo.
    echo ==========================================
    echo ERROR
    echo ==========================================
    echo Failed to configure SMTP.
    echo Check your gcloud authentication and service name.
    echo.
)

pause

