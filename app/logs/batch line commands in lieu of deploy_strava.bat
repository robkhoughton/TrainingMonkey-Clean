docker build --no-cache -f Dockerfile.strava -t gcr.io/dev-ruler-460822-e8/strava-training-personal .
docker push gcr.io/dev-ruler-460822-e8/strava-training-personal
gcloud run services update strava-training-personal --region=us-central1 --image gcr.io/dev-ruler-460822-e8/strava-training-personal