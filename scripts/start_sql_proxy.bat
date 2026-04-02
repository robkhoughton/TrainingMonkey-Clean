@echo off
REM Cloud SQL Auth Proxy — run this before any local DB work (migrations, scripts, local dev)
REM Connects to Cloud SQL via IAM, tunnels to localhost:5432
REM Keep this window open while working locally.

echo Starting Cloud SQL Auth Proxy...
echo Tunneling dev-ruler-460822-e8:us-central1:train-monk-db-v3 to localhost:5432
echo.
echo Keep this window open. Press Ctrl+C to stop.
echo.

"%USERPROFILE%\bin\cloud-sql-proxy.exe" dev-ruler-460822-e8:us-central1:train-monk-db-v3 --port 5432
