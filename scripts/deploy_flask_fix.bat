@echo off
echo ========================================
echo Deploying Flask Compatibility Fix
echo ========================================
echo.

echo [1/3] Building Docker image with Flask fix...
cd /d "%~dp0..\app"
docker build -f Dockerfile.strava -t gcr.io/dev-ruler-460822-e8/training-monkey-strava:latest .

if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo [2/3] Pushing image to Google Container Registry...
docker push gcr.io/dev-ruler-460822-e8/training-monkey-strava:latest

if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)

echo [3/3] Deploying to Cloud Run...
gcloud run deploy training-monkey-strava ^
    --image gcr.io/dev-ruler-460822-e8/training-monkey-strava:latest ^
    --platform managed ^
    --region us-central1 ^
    --allow-unauthenticated ^
    --port 8080 ^
    --memory 2Gi ^
    --cpu 2 ^
    --timeout 300 ^
    --concurrency 1000 ^
    --max-instances 10 ^
    --set-env-vars "DATABASE_URL=postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d" ^
    --set-env-vars "GOOGLE_CLOUD_PROJECT=dev-ruler-460822-e8"

if %ERRORLEVEL% neq 0 (
    echo ERROR: Cloud Run deployment failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Flask Fix Deployment Complete!
echo ========================================
echo.
echo Service URL: https://yourtrainingmonkey.com
echo Health Check: https://yourtrainingmonkey.com/health
echo.
echo The Flask compatibility issue has been fixed.
echo Wait 2-3 minutes for the service to start, then test the dashboard.
echo.
pause
