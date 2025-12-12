@echo off
echo ========================================
echo Training Monkey - Development Server
echo ========================================

echo.
echo Checking for port conflicts on 5000...

:: Check if port 5000 is in use
netstat -ano | findstr ":5000" > nul
if %errorlevel% equ 0 (
    echo WARNING: Port 5000 is already in use!
    echo.
    echo Checking what's running on port 5000:
    netstat -ano | findstr ":5000"
    echo.
    
    set /p choice="Do you want to kill the process using port 5000? (y/n): "
    if /i "%choice%"=="y" (
        echo.
        echo Killing process on port 5000...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
            echo Killing process PID: %%a
            taskkill /f /pid %%a >nul 2>&1
        )
        echo Process killed. Starting Flask app...
        timeout /t 2 >nul
    ) else (
        echo Please free up port 5000 and try again.
        pause
        exit /b 1
    )
) else (
    echo Port 5000 is available.
)

echo.
echo Starting Flask development server...
echo.
echo ========================================
echo Flask App Starting...
echo ========================================
echo.
echo Available URLs:
echo - Landing Page: http://localhost:5000/landing
echo - Login Page:   http://localhost:5000/login
echo - Dashboard:    http://localhost:5000/dashboard
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python run_flask.py

echo.
echo Flask server stopped.
pause
