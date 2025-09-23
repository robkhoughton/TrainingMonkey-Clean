@echo off
echo Starting TrainingMonkey deployment process...

echo.
echo Step 1: Rebuilding React App...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean\frontend"
if %errorlevel% neq 0 (
    echo Error: Failed to navigate to frontend directory
    pause
    exit /b 1
)

echo Cleaning previous build...
if exist build rmdir /s /q build

echo Installing dependencies...
npm install
if %errorlevel% neq 0 (
    echo Error: npm install failed
    pause
    exit /b 1
)

echo Building React app (this may take a few minutes)...
set CI=false
npm run build
if %errorlevel% neq 0 (
    echo Error: npm run build failed
    echo.
    echo Common solutions:
    echo 1. Check for TypeScript errors in the console above
    echo 2. Ensure all dependencies are installed
    echo 3. Try running 'npm run build' manually in the frontend directory
    pause
    exit /b 1
)

echo.
echo Step 2: Copying build files to app directory...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean"
if %errorlevel% neq 0 (
    echo Error: Failed to navigate to project root
    pause
    exit /b 1
)

echo Creating app\build directory if it doesn't exist...
if not exist app\build mkdir app\build

echo Copying build files...
robocopy frontend\build app\build /E /NFL /NDL /NJH /NJS /nc /ns /np
if %errorlevel% gtr 7 (
    echo Error: Failed to copy build files
    pause
    exit /b 1
)
echo Build files copied successfully.

echo Copying static files for local development...
robocopy frontend\build\static app\static /E /NFL /NDL /NJH /NJS /nc /ns /np
if %errorlevel% gtr 7 (
    echo Error: Failed to copy static files
    pause
    exit /b 1
)
echo Static files copied successfully.

echo.
echo Step 3: Deploying to Cloud Run...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean\app"
if %errorlevel% neq 0 (
    echo Error: Failed to navigate to app directory
    pause
    exit /b 1
)

deploy_strava_simple.bat
if %errorlevel% neq 0 (
    echo Error: Deployment failed
    pause
    exit /b 1
)

echo.
echo Deployment completed successfully!
pause
