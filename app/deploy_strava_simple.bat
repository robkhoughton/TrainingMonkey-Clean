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

REM echo Changing to strava_sync_service directory...
REM cd strava_sync_service
REM if %ERRORLEVEL% neq 0 (
REM     echo ERROR: Could not find strava_sync_service directory!
REM     pause
REM     exit /b 1
REM )


echo Checking build directory...
if not exist "build" (
    echo ERROR: build directory not found in strava_sync_service!
    echo Please ensure your React app has been built and the build directory exists.
    pause
    exit /b 1
)

echo Building Docker image...
docker build --no-cache -f Dockerfile.strava -t %IMAGE_NAME%:%BUILD_TIME% .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    cd ..
    pause
    exit /b 1
)

echo Pushing Docker image...
docker push %IMAGE_NAME%:%BUILD_TIME%
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    cd ..
    pause
    exit /b 1
)

echo Updating Cloud Run service...
call gcloud run services update %SERVICE_NAME% --region=%REGION% --image %IMAGE_NAME%:%BUILD_TIME% --timeout=300
if %ERRORLEVEL% neq 0 (
    echo ERROR: Cloud Run update failed!
    pause
    exit /b 1
)

echo.
echo ==============================================
echo DEPLOYMENT COMPLETE
echo ==============================================
echo Deployed: %date% %time%
echo Build:    %BUILD_TIME%
echo Image:    %IMAGE_NAME%:%BUILD_TIME%
echo ==============================================
echo.

pause