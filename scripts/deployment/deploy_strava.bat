@echo off
REM Simple, reliable deployment script that mirrors successful manual commands
setlocal enabledelayedexpansion

echo ==============================================
echo Simple Strava Deployment Script
echo ==============================================
echo.

REM Configuration
set PROJECT_ID=dev-ruler-460822-e8
set REGION=us-central1
set SERVICE_NAME=strava-training-personal
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

REM Build with timestamp for uniqueness
set BUILD_TIME=%date:~-4,4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%
set BUILD_TIME=%BUILD_TIME: =0%

echo Building Docker image...
docker build --no-cache -f Dockerfile.strava -t %IMAGE_NAME%:%BUILD_TIME% .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo Pushing Docker image...
docker push %IMAGE_NAME%:%BUILD_TIME%
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)

echo Updating Cloud Run service...
gcloud run services update %SERVICE_NAME% --region=%REGION% --image %IMAGE_NAME%:%BUILD_TIME%
if %ERRORLEVEL% neq 0 (
    echo ERROR: Cloud Run update failed!
    pause
    exit /b 1
)

echo.
echo Waiting for deployment to complete...
timeout /t 10 /nobreak > nul

echo Testing deployment...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

if defined SERVICE_URL (
    echo Service URL: %SERVICE_URL%
    echo Testing health endpoint...
    curl -f %SERVICE_URL%/health
    if %ERRORLEVEL% neq 0 (
        echo WARNING: Health check failed - but deployment may still be starting
    ) else (
        echo SUCCESS: Health check passed!
    )
) else (
    echo ERROR: Could not get service URL
)

echo.
echo ==============================================
echo DEPLOYMENT COMPLETE
echo ==============================================
echo Build: %BUILD_TIME%
echo Image: %IMAGE_NAME%:%BUILD_TIME%
echo Service: %SERVICE_URL%
echo ==============================================

pause