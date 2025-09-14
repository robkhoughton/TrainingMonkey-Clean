@echo off
echo TrainingMonkey Build Troubleshooting Script
echo ===========================================

echo.
echo Step 1: Checking Node.js and npm versions...
node --version
npm --version

echo.
echo Step 2: Navigating to frontend directory...
cd /d "C:\Users\robho\Documents\TrainingMonkey-Clean\frontend"
if %errorlevel% neq 0 (
    echo Error: Failed to navigate to frontend directory
    pause
    exit /b 1
)

echo.
echo Step 3: Checking if package.json exists...
if not exist package.json (
    echo Error: package.json not found in frontend directory
    pause
    exit /b 1
)
echo package.json found

echo.
echo Step 4: Checking if node_modules exists...
if not exist node_modules (
    echo Warning: node_modules not found, will need to run npm install
) else (
    echo node_modules found
)

echo.
echo Step 5: Checking for TypeScript errors...
echo Running TypeScript compiler check...
npx tsc --noEmit
if %errorlevel% neq 0 (
    echo Warning: TypeScript errors found
    echo This may cause the build to fail
) else (
    echo No TypeScript errors found
)

echo.
echo Step 6: Checking for linting errors...
echo Running ESLint check...
npx eslint src/ --ext .ts,.tsx
if %errorlevel% neq 0 (
    echo Warning: ESLint errors found
    echo This may cause the build to fail
) else (
    echo No ESLint errors found
)

echo.
echo Step 7: Attempting to build with verbose output...
echo This will show detailed build information...
set CI=false
npm run build -- --verbose
if %errorlevel% neq 0 (
    echo.
    echo Build failed. Common solutions:
    echo 1. Fix TypeScript errors shown above
    echo 2. Fix ESLint errors shown above
    echo 3. Delete node_modules and package-lock.json, then run npm install
    echo 4. Check for memory issues (React builds can be memory intensive)
    echo 5. Try building with: set NODE_OPTIONS=--max-old-space-size=4096
    pause
    exit /b 1
) else (
    echo.
    echo Build completed successfully!
)

echo.
echo Troubleshooting complete.
pause
