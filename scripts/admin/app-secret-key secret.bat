@echo off
echo Creating missing app-secret-key secret...

REM Create app secret key for session management
powershell -Command "[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString()))" | gcloud secrets create app-secret-key --data-file=-

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create app-secret-key secret!
    echo This secret may already exist. Checking...
    gcloud secrets list | findstr app-secret-key
    if %ERRORLEVEL% neq 0 (
        echo app-secret-key secret not found. Manual creation required.
    ) else (
        echo app-secret-key secret already exists.
    )
    pause
    exit /b %ERRORLEVEL%
)

echo app-secret-key secret created successfully!

echo.
echo Verifying all Strava secrets exist:
gcloud secrets list | findstr strava
gcloud secrets list | findstr app-secret-key

echo.
echo Testing secret access:
gcloud secrets versions access latest --secret="strava-client-id"
echo.
pause