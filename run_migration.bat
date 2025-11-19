@echo off
REM Schema migration script for Windows
REM Adds start_time and device_name columns to activities table

echo ============================================================
echo SCHEMA MIGRATION RUNNER
echo ============================================================
echo.

REM Check if DATABASE_URL is set
if "%DATABASE_URL%"=="" (
    echo ERROR: DATABASE_URL environment variable is not set
    echo.
    echo Please set it first using ONE of these methods:
    echo.
    echo METHOD 1 - Temporary (this session only):
    echo   set DATABASE_URL=postgresql://appuser:password@35.223.144.85:5432/train-d
    echo   run_migration.bat
    echo.
    echo METHOD 2 - Run with the variable inline:
    echo   set DATABASE_URL=postgresql://appuser:password@35.223.144.85:5432/train-d^&^& cd app ^&^& python run_migration.py
    echo.
    pause
    exit /b 1
)

echo DATABASE_URL is set (first 50 chars): %DATABASE_URL:~0,50%...
echo.
echo Running migration...
echo.

cd app
python run_migration.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Migration completed.
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo FAILED! Migration encountered errors.
    echo ============================================================
)

cd ..
pause


