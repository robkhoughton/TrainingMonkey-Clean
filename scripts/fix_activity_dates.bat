@echo off
REM Fix Activity Timezone Dates - Easy Launcher
REM =============================================
REM This script fixes activity dates that were stored incorrectly due to the timezone bug.

echo.
echo ========================================
echo Activity Timezone Date Fix
echo ========================================
echo.
echo This script will check for activities with incorrect dates
echo (caused by UTC vs local timezone bug) and fix them.
echo.

REM Check if user_id is provided
if "%1"=="" (
    echo Usage: fix_activity_dates.bat USER_ID [--fix]
    echo.
    echo Examples:
    echo   fix_activity_dates.bat 123           ^(dry-run mode - shows what would be fixed^)
    echo   fix_activity_dates.bat 123 --fix     ^(actually fixes the dates^)
    echo.
    exit /b 1
)

set USER_ID=%1
set FIX_FLAG=%2

echo User ID: %USER_ID%
echo.

if "%FIX_FLAG%"=="--fix" (
    echo ⚠️  FIX MODE - Changes WILL be applied to the database
    echo.
    set /p CONFIRM="Are you sure you want to fix the dates? (y/n): "
    if /i not "!CONFIRM!"=="y" (
        echo Cancelled.
        exit /b 0
    )
    echo.
    python fix_activity_timezone_dates.py %USER_ID% --fix
) else (
    echo 🔍 DRY-RUN MODE - No changes will be made
    echo    Run with --fix flag to apply corrections
    echo.
    python fix_activity_timezone_dates.py %USER_ID%
)

echo.
echo Done!
pause
