@echo off
echo TrainingMonkey Build and Copy Script
echo ====================================

echo.
echo Step 1: Building React app...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean\frontend"
if %errorlevel% neq 0 (
    echo Error: Failed to navigate to frontend directory
    pause
    exit /b 1
)

echo Building React app...
npm run build
if %errorlevel% neq 0 (
    echo Error: React build failed
    pause
    exit /b 1
)

echo.
echo Step 2: Copying build files to app directory...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean"
xcopy frontend\build\* app\build\ /E /Y
if %errorlevel% neq 0 (
    echo Error: Failed to copy build files
    pause
    exit /b 1
)

echo.
echo Build and copy completed successfully!
echo React app is now ready to serve from app/build/
pause

