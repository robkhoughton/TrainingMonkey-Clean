@echo off
REM ============================================================================
REM Lighthouse Performance Audit Script
REM ============================================================================
REM This script runs a Lighthouse audit on the deployed TrainingMonkey app
REM and generates a detailed performance report
REM
REM Prerequisites:
REM   1. Node.js and npm installed
REM   2. App deployed to cloud (get URL from deployment)
REM   3. Lighthouse CLI installed (npm install -g lighthouse)
REM ============================================================================

echo.
echo ====================================
echo TrainingMonkey Lighthouse Audit
echo ====================================
echo.

REM Check if Lighthouse is installed
where lighthouse >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Lighthouse not found. Installing...
    npm install -g lighthouse
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install Lighthouse. Install manually with: npm install -g lighthouse
        pause
        exit /b 1
    )
)

REM Get app URL from user or use default
set /p APP_URL="Enter your app URL (or press Enter for default): "
if "%APP_URL%"=="" (
    REM Default to common Google Cloud App Engine URL pattern
    echo [INFO] Using default URL pattern - update this script with your actual URL
    set APP_URL=https://your-project-id.uc.r.appspot.com
)

echo.
echo [INFO] Running Lighthouse audit on: %APP_URL%
echo [INFO] This may take 30-60 seconds...
echo.

REM Create reports directory if it doesn't exist
if not exist "reports" mkdir reports

REM Get current date/time for filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM Run Lighthouse audit
REM - Only audit performance category (faster)
REM - Save as HTML and JSON
REM - Simulate mobile device
REM - Include detailed breakdown
lighthouse %APP_URL% ^
    --only-categories=performance ^
    --output=html ^
    --output=json ^
    --output-path=reports\lighthouse_%TIMESTAMP% ^
    --view ^
    --chrome-flags="--headless --no-sandbox" ^
    --emulated-form-factor=mobile ^
    --throttling-method=simulate

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo [SUCCESS] Lighthouse Audit Complete!
    echo ====================================
    echo.
    echo Reports saved to:
    echo   - reports\lighthouse_%TIMESTAMP%.html
    echo   - reports\lighthouse_%TIMESTAMP%.json
    echo.
    echo The HTML report should open in your browser automatically.
    echo.
    echo Key Metrics to Review:
    echo   - Performance Score (target: 90+)
    echo   - First Contentful Paint (target: < 1.8s)
    echo   - Largest Contentful Paint (target: < 2.5s)
    echo   - Total Blocking Time (target: < 200ms)
    echo   - Cumulative Layout Shift (target: < 0.1)
    echo   - Speed Index (target: < 3.4s)
    echo.
    
    REM Also run desktop audit
    echo [INFO] Running desktop audit for comparison...
    lighthouse %APP_URL% ^
        --only-categories=performance ^
        --output=html ^
        --output-path=reports\lighthouse_desktop_%TIMESTAMP% ^
        --chrome-flags="--headless --no-sandbox" ^
        --emulated-form-factor=desktop ^
        --throttling-method=simulate
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] Desktop audit also complete!
        echo   - reports\lighthouse_desktop_%TIMESTAMP%.html
        echo.
    )
) else (
    echo.
    echo [ERROR] Lighthouse audit failed!
    echo.
    echo Common issues:
    echo   1. App URL is incorrect or not accessible
    echo   2. App requires authentication (Lighthouse can't login)
    echo   3. Network connectivity issues
    echo   4. Chrome/Chromium not installed
    echo.
    echo Try running manually:
    echo   lighthouse %APP_URL% --view --only-categories=performance
    echo.
)

echo.
pause




