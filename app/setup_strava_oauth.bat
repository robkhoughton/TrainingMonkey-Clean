@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo Strava OAuth Setup for Cloud Deployment
echo ===============================================
echo.

REM Step 1: Display authorization URL (safer than auto-opening)
echo Step 1: Please open this URL in your browser:
echo.
echo https://www.strava.com/oauth/authorize?client_id=47238^&response_type=code^&redirect_uri=http://localhost^&scope=read,activity:read_all
echo.
echo IMPORTANT: After authorizing, you'll be redirected to a localhost URL that looks like:
echo http://localhost/?state=^&code=1234567890abcdef1234567890abcdef12345678^&scope=read,activity:read_all
echo.
echo Copy ONLY the code part (the long string after 'code=' and before '^&scope')
echo The code should be about 40 characters long and contain letters and numbers.
echo.
set /p AUTH_CODE="Enter the authorization code: "

if "%AUTH_CODE%"=="" (
    echo ERROR: Authorization code is required!
    pause
    exit /b 1
)

echo.
echo DEBUG: Authorization code length:
echo %AUTH_CODE% | find /c /v ""
echo DEBUG: First 10 characters: %AUTH_CODE:~0,10%
echo.

if "%AUTH_CODE%"=="" (
    echo ERROR: Authorization code is required!
    pause
    exit /b 1
)

echo.
echo Step 2: Exchanging authorization code for access tokens...
echo.

REM Create temporary JSON file for the request
set TEMP_JSON=%TEMP%\strava_oauth.json
echo { > "%TEMP_JSON%"
echo   "code": "%AUTH_CODE%", >> "%TEMP_JSON%"
echo   "client_id": "47238", >> "%TEMP_JSON%"
echo   "client_secret": "65cb63b7b469b09d96ce72124fa7af7af4bf80e3" >> "%TEMP_JSON%"
echo } >> "%TEMP_JSON%"

REM Make the OAuth callback request
echo Making OAuth request...
curl -k -X POST https://strava-training-personal-382535371225.us-central1.run.app/oauth-callback -H "Content-Type: application/json" -d @"%TEMP_JSON%" > oauth_response.txt

echo.
echo OAuth Response:
type oauth_response.txt
echo.

REM Check if the response contains success
findstr /C:"success.*true" oauth_response.txt >nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: OAuth token exchange failed!
    echo The authorization code may be invalid, expired, or already used.
    echo Please try getting a new authorization code.
    echo.
    echo Troubleshooting:
    echo 1. Make sure you copied the ENTIRE code from the URL
    echo 2. The code should be about 40 characters long
    echo 3. Get a fresh code - they expire quickly and can only be used once
    echo.
    del "%TEMP_JSON%" 2>nul
    del oauth_response.txt 2>nul
    pause
    exit /b 1
)

echo SUCCESS: OAuth tokens obtained!

REM Clean up temp file
del "%TEMP_JSON%" 2>nul

echo.
echo.
echo Step 3: Testing data synchronization...
echo.

REM Create JSON for sync request
set SYNC_JSON=%TEMP%\strava_sync.json
echo {"days": 7} > "%SYNC_JSON%"

curl -k -X POST https://strava-training-personal-382535371225.us-central1.run.app/sync -H "Content-Type: application/json" -d @"%SYNC_JSON%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Data sync may have failed. Continuing with verification...
)

REM Clean up temp file
del "%SYNC_JSON%" 2>nul

echo.
echo.
echo Step 4: Verifying data was imported...
echo.
curl -k https://strava-training-personal-382535371225.us-central1.run.app/api/training-data

echo.
echo.
echo ===============================================
echo OAuth Setup Complete!
echo ===============================================
echo.
echo Your Strava data should now be syncing to:
echo https://strava-training-personal-382535371225.us-central1.run.app
echo.
echo Available endpoints:
echo - /api/training-data - View your training data
echo - /api/stats - View training statistics
echo - /sync - Manually trigger data sync
echo.
echo If you see errors above, you may need to:
echo 1. Check your internet connection
echo 2. Verify the authorization code was correct
echo 3. Try running this script again
echo.
pause