@echo off
REM Start TrainingMonkey with mock database for UI development
REM No Cloud SQL connection required - uses fake data

echo ============================================================
echo    TrainingMonkey - Mock Database Mode
echo ============================================================
echo.

cd /d "%~dp0..\app"

REM Set environment variables for mock mode
set USE_MOCK_DB=true
set DATABASE_URL=mock://localhost/trainingmonkey

REM Start the mock server
python run_mock_server.py

pause
