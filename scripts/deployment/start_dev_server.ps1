#!/usr/bin/env pwsh
# Training Monkey - Development Server Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Training Monkey - Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking for port conflicts on 5000..." -ForegroundColor Yellow

# Check if port 5000 is in use
$portCheck = netstat -ano | Select-String ":5000" | Select-String "LISTENING"

if ($portCheck) {
    Write-Host "WARNING: Port 5000 is already in use!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Processes using port 5000:" -ForegroundColor Yellow
    netstat -ano | Select-String ":5000" | Select-String "LISTENING"
    Write-Host ""
    
    $choice = Read-Host "Do you want to kill the process using port 5000? (y/n)"
    if ($choice -eq 'y' -or $choice -eq 'Y') {
        Write-Host ""
        Write-Host "Killing process on port 5000..." -ForegroundColor Yellow
        
        # Extract PID and kill process
        $pidMatch = $portCheck -match '(\d+)$'
        if ($pidMatch) {
            $pid = $matches[1]
            Write-Host "Killing process PID: $pid" -ForegroundColor Yellow
            try {
                Stop-Process -Id $pid -Force
                Write-Host "Process killed successfully." -ForegroundColor Green
                Start-Sleep -Seconds 2
            }
            catch {
                Write-Host "Error killing process: $_" -ForegroundColor Red
                exit 1
            }
        }
    }
    else {
        Write-Host "Please free up port 5000 and try again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
else {
    Write-Host "Port 5000 is available." -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting Flask development server..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Flask App Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available URLs:" -ForegroundColor White
Write-Host "- Landing Page: http://localhost:5000/landing" -ForegroundColor Green
Write-Host "- Login Page:   http://localhost:5000/login" -ForegroundColor Green
Write-Host "- Dashboard:    http://localhost:5000/dashboard" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Flask app
try {
    python run_flask.py
}
catch {
    Write-Host "Error starting Flask app: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Flask server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
