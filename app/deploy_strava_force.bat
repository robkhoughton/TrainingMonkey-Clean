@echo off
echo Starting Strava Training Personal Service FORCE build with UNIQUE TAG...
echo.

REM Create unique timestamp-based tag
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%-%HH%-%Min%-%Sec%"

set "UNIQUE_IMAGE=gcr.io/dev-ruler-460822-e8/strava-training-personal:%timestamp%"
echo Building with unique tag: %UNIQUE_IMAGE%
echo.

echo FORCE CLEANUP: Cleaning Docker cache and images...
docker system prune -f
docker image rm gcr.io/dev-ruler-460822-e8/strava-training-personal --force 2>nul || echo "Image not found locally, continuing..."
echo.

echo Step 1: Building Docker image with unique tag...
docker build --no-cache --pull -f Dockerfile.strava -t %UNIQUE_IMAGE% .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b %ERRORLEVEL%
)
echo Docker build completed successfully.
echo.

echo Step 2: Pushing unique image to Google Container Registry...
docker push %UNIQUE_IMAGE%
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b %ERRORLEVEL%
)
echo Docker push completed successfully.
echo.

echo Step 3: Updating database connection for private IP...
powershell -Command "Write-Output 'postgresql://appuser:trainmonk25@10.109.208.9:5432/train-d'" | gcloud secrets versions add database-url --data-file=-
echo.

echo Step 4: FORCE deleting existing service...
gcloud run services delete strava-training-personal --region=us-central1 --quiet
echo Waiting for service deletion to complete...
timeout /t 10 /nobreak > nul
echo.

echo Step 5: Fresh deployment with unique image...
gcloud run deploy strava-training-personal ^
  --image %UNIQUE_IMAGE% ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --set-env-vars GOOGLE_CLOUD_PROJECT=dev-ruler-460822-e8 ^
  --update-secrets DATABASE_URL=database-url:latest,STRAVA_CLIENT_ID=strava-client-id:latest,STRAVA_CLIENT_SECRET=strava-client-secret:latest,SECRET_KEY=app-secret-key:latest ^
  --memory 512Mi ^
  --cpu 1 ^
  --timeout 300 ^
  --max-instances 3 ^
  --port 8080 ^
  --vpc-connector projects/dev-ruler-460822-e8/locations/us-central1/connectors/default

if %ERRORLEVEL% neq 0 (
    echo.
    echo VPC connector might be missing. Creating one...
    gcloud compute networks vpc-access connectors create default ^
      --region=us-central1 ^
      --subnet=default ^
      --subnet-project=dev-ruler-460822-e8 ^
      --range=10.8.0.0/28

    echo Retrying deployment...
    gcloud run deploy strava-training-personal ^
      --image %UNIQUE_IMAGE% ^
      --platform managed ^
      --region us-central1 ^
      --allow-unauthenticated ^
      --set-env-vars GOOGLE_CLOUD_PROJECT=dev-ruler-460822-e8 ^
      --update-secrets DATABASE_URL=database-url:latest,STRAVA_CLIENT_ID=strava-client-id:latest,STRAVA_CLIENT_SECRET=strava-client-secret:latest,SECRET_KEY=app-secret-key:latest ^
      --memory 512Mi ^
      --cpu 1 ^
      --timeout 300 ^
      --max-instances 3 ^
      --port 8080 ^
      --vpc-connector projects/dev-ruler-460822-e8/locations/us-central1/connectors/default
)

echo.
echo Checking revisions to confirm new deployment...
gcloud run revisions list --service=strava-training-personal --region=us-central1 --limit=3
echo.

echo Getting service URL...
for /f "tokens=*" %%i in ('gcloud run services describe strava-training-personal --region=us-central1 --format="value(status.url)"') do set SERVICE_URL=%%i

if defined SERVICE_URL (
    echo Service URL: %SERVICE_URL%
    echo.
    echo Testing endpoints:
    curl %SERVICE_URL%/health
    echo.
    curl %SERVICE_URL%/debug
) else (
    echo Warning: Could not determine service URL
)

echo.
echo Deployment complete!
pause