@echo off
REM Training Monkey - Local Deployment with Cloud Database
REM This script sets up and runs the app locally with direct connection to cloud database

echo ==============================================
echo Training Monkey - Local Deployment
echo ==============================================
echo.

echo This script will deploy the app locally with cloud database connection
echo and include the new ACWR configuration features.
echo.

set /p continue="Proceed with deployment? (Y/n): "
if /i not "%continue%"=="y" if /i not "%continue%"=="yes" if not "%continue%"=="" (
    echo Deployment cancelled.
    pause
    exit /b 0
)

echo.
echo Starting deployment process...
echo.

REM Run the Python deployment script
python deploy_local_with_cloud_db.py

echo.
echo Deployment process completed.
pause
