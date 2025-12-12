@echo off
echo ========================================
echo Quick Fix: Database Optimization Deployment
echo ========================================
echo.

echo [1/3] Building Docker image with updated Dockerfile...
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
    --update-secrets DATABASE_URL=DATABASE_URL:latest ^
    --set-env-vars "GOOGLE_CLOUD_PROJECT=dev-ruler-460822-e8"

if %ERRORLEVEL% neq 0 (
    echo ERROR: Cloud Run deployment failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Quick Fix Deployment Complete!
echo ========================================
echo.
echo Service URL: https://yourtrainingmonkey.com
echo Health Check: https://yourtrainingmonkey.com/health
echo.
echo The missing database optimization files have been added to the Docker image.
echo Check the service in a few minutes to confirm it's working.
echo.
pause
