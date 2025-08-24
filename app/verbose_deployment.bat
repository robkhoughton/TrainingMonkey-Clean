@echo off
echo ============================================
echo VERBOSE DEPLOYMENT - Full Diagnostic Mode
echo ============================================
echo.

echo === ENVIRONMENT CHECK ===
echo Current project:
gcloud config get-value project
echo.
echo Current account:
gcloud config get-value account
echo.
echo Available regions:
gcloud run regions list --limit=5
echo.

echo === IMAGE CHECK ===
echo Checking existing images:
gcloud container images list-tags gcr.io/dev-ruler-460822-e8/strava-training-personal --limit=3
echo.

echo === CURRENT SERVICES ===
echo Existing Cloud Run services:
gcloud run services list --region=us-central1
echo.

echo === BUILDING IMAGE ===
docker build --no-cache -f Dockerfile.strava -t gcr.io/dev-ruler-460822-e8/strava-training-personal .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo === PUSHING IMAGE ===
docker push gcr.io/dev-ruler-460822-e8/strava-training-personal
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo === VERIFYING IMAGE PUSH ===
echo Confirming image is in registry:
gcloud container images list-tags gcr.io/dev-ruler-460822-e8/strava-training-personal --limit=1
echo.

echo === DEPLOYMENT ATTEMPT 1 - Minimal Configuration ===
echo Trying basic deployment first...
gcloud run deploy strava-training-personal ^
  --image gcr.io/dev-ruler-460822-e8/strava-training-personal ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --memory 512Mi ^
  --port 8080 ^
  --verbosity=debug

echo.
echo === CHECKING RESULT ===
echo Services after basic deployment:
gcloud run services list --region=us-central1
echo.

if %ERRORLEVEL% equ 0 (
    echo Basic deployment succeeded! Adding secrets...

    echo === ADDING SECRETS ===
    gcloud run services update strava-training-personal ^
      --region us-central1 ^
      --set-env-vars GOOGLE_CLOUD_PROJECT=dev-ruler-460822-e8 ^
      --update-secrets DATABASE_URL=database-url:latest,STRAVA_CLIENT_ID=strava-client-id:latest,STRAVA_CLIENT_SECRET=strava-client-secret:latest,SECRET_KEY=app-secret-key:latest ^
      --verbosity=debug

    echo === ADDING VPC CONNECTOR ===
    echo Checking VPC connector...
    gcloud compute networks vpc-access connectors list --region=us-central1

    gcloud run services update strava-training-personal ^
      --region us-central1 ^
      --vpc-connector projects/dev-ruler-460822-e8/locations/us-central1/connectors/default ^
      --verbosity=debug

) else (
    echo Basic deployment failed! Checking permissions...

    echo === PERMISSION CHECK ===
    echo Your IAM roles:
    gcloud projects get-iam-policy dev-ruler-460822-e8 --flatten="bindings[].members" --filter="bindings.members:*$(gcloud config get-value account)*"

    echo === ALTERNATIVE DEPLOYMENT ===
    echo Trying without managed platform flag...
    gcloud run deploy strava-training-personal ^
      --image gcr.io/dev-ruler-460822-e8/strava-training-personal ^
      --region us-central1 ^
      --allow-unauthenticated ^
      --memory 512Mi ^
      --port 8080 ^
      --verbosity=debug
)

echo.
echo === FINAL STATUS ===
echo Final service list:
gcloud run services list --region=us-central1
echo.

echo Getting service details...
gcloud run services describe strava-training-personal --region=us-central1 2>nul || echo "Service not found!"

echo.
echo === TESTING ACCESS ===
for /f "tokens=*" %%i in ('gcloud run services describe strava-training-personal --region=us-central1 --format="value(status.url)" 2^>nul') do set SERVICE_URL=%%i

if defined SERVICE_URL (
    echo Service URL: %SERVICE_URL%
    echo Testing health endpoint...
    curl %SERVICE_URL%/health
) else (
    echo No service URL found. Deployment may have failed silently.
)

echo.
echo ============================================
echo VERBOSE DEPLOYMENT COMPLETE
echo ============================================
pause