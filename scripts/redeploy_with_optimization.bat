@echo off
echo ========================================
echo TrainingMonkey Database Optimization Deployment
echo ========================================
echo.

echo [1/4] Building Docker image with database optimization files...
cd /d "%~dp0..\app"
docker build -f Dockerfile.strava -t gcr.io/dev-ruler-460822-e8/training-monkey-strava:latest .

if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo [2/4] Pushing image to Google Container Registry...
docker push gcr.io/dev-ruler-460822-e8/training-monkey-strava:latest

if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)

echo [3/4] Deploying to Cloud Run...
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

echo [4/4] Testing deployment...
echo Waiting 30 seconds for service to start...
timeout /t 30 /nobreak > nul

echo Testing health endpoint...
curl -f https://yourtrainingmonkey.com/health

if %ERRORLEVEL% neq 0 (
    echo WARNING: Health check failed, but deployment may still be successful
    echo Check Cloud Run logs for more details
) else (
    echo SUCCESS: Health check passed!
)

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Service URL: https://yourtrainingmonkey.com
echo Health Check: https://yourtrainingmonkey.com/health
echo Admin Status: https://yourtrainingmonkey.com/admin/database-optimization-status
echo.
echo Check Cloud Run logs if you encounter any issues:
echo gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=training-monkey-strava" --limit 50 --format="table(timestamp,severity,textPayload)"
echo.
pause
