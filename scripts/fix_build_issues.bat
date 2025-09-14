@echo off
echo TrainingMonkey Build Fix Script
echo ===============================

echo.
echo This script will attempt to fix common React build issues...

echo.
echo Step 1: Navigating to frontend directory...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean\frontend"
if %errorlevel% neq 0 (
    echo Error: Failed to navigate to frontend directory
    pause
    exit /b 1
)

echo.
echo Step 2: Clearing npm cache...
npm cache clean --force
if %errorlevel% neq 0 (
    echo Warning: Failed to clear npm cache
)

echo.
echo Step 3: Removing node_modules and package-lock.json...
if exist node_modules (
    echo Removing node_modules...
    rmdir /s /q node_modules
)
if exist package-lock.json (
    echo Removing package-lock.json...
    del package-lock.json
)

echo.
echo Step 4: Reinstalling dependencies...
npm install
if %errorlevel% neq 0 (
    echo Error: npm install failed
    pause
    exit /b 1
)

echo.
echo Step 5: Setting environment variables for build...
set CI=false
set GENERATE_SOURCEMAP=false
set NODE_OPTIONS=--max-old-space-size=4096

echo.
echo Step 6: Attempting build with increased memory...
npm run build
if %errorlevel% neq 0 (
    echo.
    echo Build still failed. Try these additional steps:
    echo 1. Run the troubleshoot_build.bat script for detailed error analysis
    echo 2. Check for TypeScript errors in your source code
    echo 3. Ensure all imports are correct
    echo 4. Try building with: npm run build -- --verbose
    pause
    exit /b 1
) else (
    echo.
    echo Build completed successfully!
    echo You can now run the deploy.bat script.
)

echo.
echo Build fix complete.
pause
