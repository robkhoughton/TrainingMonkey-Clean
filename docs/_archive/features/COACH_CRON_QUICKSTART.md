# Coach Cron Jobs - Quick Start Guide

## TL;DR

Two cron jobs generate weekly training programs:

1. **Sunday 6 PM UTC**: Full 7-day program for upcoming week
2. **Wednesday 6 PM UTC**: Adjust remaining 4 days based on actuals

## Setup Commands (GCP)

Replace `YOUR_APP_URL` and `YOUR_SERVICE_ACCOUNT` with your values:

```bash
# Sunday: Full week generation
gcloud scheduler jobs create http weekly-program-sunday \
    --location=us-central1 \
    --schedule="0 18 * * 0" \
    --uri="https://YOUR_APP_URL/cron/weekly-program?mode=full" \
    --http-method=POST \
    --headers="X-Cloudscheduler=true" \
    --oidc-service-account-email="YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --oidc-token-audience="https://YOUR_APP_URL" \
    --time-zone="UTC"

# Wednesday: Mid-week adjustment
gcloud scheduler jobs create http weekly-program-wednesday \
    --location=us-central1 \
    --schedule="0 18 * * 3" \
    --uri="https://YOUR_APP_URL/cron/weekly-program?mode=adjustment" \
    --http-method=POST \
    --headers="X-Cloudscheduler=true" \
    --oidc-service-account-email="YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --oidc-token-audience="https://YOUR_APP_URL" \
    --time-zone="UTC"
```

## Local Testing

```bash
# Test Sunday mode (full week)
curl -X POST http://localhost:5000/cron/weekly-program?mode=full \
  -H "X-Cloudscheduler: true"

# Test Wednesday mode (adjustment)
curl -X POST http://localhost:5000/cron/weekly-program?mode=adjustment \
  -H "X-Cloudscheduler: true"
```

## Expected Response

```json
{
  "message": "Weekly program generation completed",
  "mode": "full",
  "total_users": 25,
  "successful": 23,
  "errors": 0,
  "skipped": 2,
  "timestamp": "2025-11-25T18:00:15.123456"
}
```

## What It Does

1. Finds active users (activity in last 14 days)
2. Skips users without race goals
3. Generates divergence-optimized 7-day training program
4. Saves to `weekly_programs` table
5. Returns summary JSON

## Cost Estimate

~$1.50/week for 25 active users (~$6/month)

See `COACH_CRON_SETUP.md` for complete documentation.

