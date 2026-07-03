# Coach Page - Weekly Program Generation Cron Setup

## Overview

The YTM Coach page requires automated weekly training program generation using Google Cloud Scheduler. This document provides complete setup instructions.

## Cron Jobs Required

### 1. Sunday Full Program Generation
**Purpose**: Generate complete 7-day training programs for the upcoming week

- **Schedule**: Every Sunday at 6:00 PM UTC (10:00 AM Pacific)
- **Endpoint**: `POST /cron/weekly-program?mode=full`
- **Mode**: `full` (generates Monday-Sunday program)
- **Rationale**: Gives users their full week plan on Sunday evening, ready for Monday start

### 2. Wednesday Mid-Week Adjustment
**Purpose**: Regenerate remaining 4 days based on actual Monday-Wednesday performance

- **Schedule**: Every Wednesday at 6:00 PM UTC (10:00 AM Pacific)
- **Endpoint**: `POST /cron/weekly-program?mode=adjustment`
- **Mode**: `adjustment` (regenerates Thursday-Sunday based on Mon-Wed actuals)
- **Rationale**: Adapts training to actual performance, adjusts for over/underperformance

## Active User Detection

Both cron jobs only process **active users**:
- Users with at least one activity in the last **14 days**
- Users with configured **race goals** (skips users who haven't set up Coach page)
- Prevents unnecessary API calls and costs

## Google Cloud Scheduler Configuration

### Prerequisites
1. Google Cloud Project with Cloud Scheduler API enabled
2. App deployed to Google Cloud Run or App Engine
3. Service account with permissions to invoke Cloud Run/App Engine

### Job 1: Sunday Full Program Generation

```bash
gcloud scheduler jobs create http weekly-program-sunday \
    --location=us-central1 \
    --schedule="0 18 * * 0" \
    --uri="https://YOUR_APP_URL/cron/weekly-program?mode=full" \
    --http-method=POST \
    --headers="X-Cloudscheduler=true" \
    --oidc-service-account-email="YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --oidc-token-audience="https://YOUR_APP_URL" \
    --time-zone="UTC" \
    --description="Generate full 7-day training programs for upcoming week"
```

### Job 2: Wednesday Mid-Week Adjustment

```bash
gcloud scheduler jobs create http weekly-program-wednesday \
    --location=us-central1 \
    --schedule="0 18 * * 3" \
    --uri="https://YOUR_APP_URL/cron/weekly-program?mode=adjustment" \
    --http-method=POST \
    --headers="X-Cloudscheduler=true" \
    --oidc-service-account-email="YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --oidc-token-audience="https://YOUR_APP_URL" \
    --time-zone="UTC" \
    --description="Adjust remaining 4 days based on Mon-Wed performance"
```

### Schedule Format
- `0 18 * * 0` = Every Sunday at 18:00 UTC (6 PM)
- `0 18 * * 3` = Every Wednesday at 18:00 UTC (6 PM)

Format: `minute hour day month day_of_week`
- Day of week: 0=Sunday, 1=Monday, ..., 6=Saturday

## Environment Variables

No new environment variables required. Uses existing:
- `ANTHROPIC_API_KEY` - Claude API access (already configured)
- `DATABASE_URL` - PostgreSQL connection (already configured)

## Security

### Authentication
- Cron jobs **require** `X-Cloudscheduler` header
- Requests without this header return `401 Unauthorized`
- Uses OIDC tokens for Cloud Scheduler → App authentication

### Rate Limiting
- 2-second delay between users to avoid API rate limits
- Claude API has rate limits; delay prevents hitting them

## Testing Cron Jobs

### Manual Test via Cloud Console
1. Go to Cloud Scheduler in GCP Console
2. Find the job (`weekly-program-sunday` or `weekly-program-wednesday`)
3. Click "RUN NOW"
4. Check logs in Cloud Logging

### Manual Test via curl (Local Development)

```bash
# Test Sunday full generation
curl -X POST http://localhost:5000/cron/weekly-program?mode=full \
  -H "X-Cloudscheduler: true"

# Test Wednesday adjustment
curl -X POST http://localhost:5000/cron/weekly-program?mode=adjustment \
  -H "X-Cloudscheduler: true"
```

### Test with Specific User (Development)

Temporarily modify cron to filter specific user:
```python
# In weekly_program_cron(), after getting active_users:
active_users = [u for u in active_users if u['user_id'] == YOUR_USER_ID]
```

## Monitoring & Logs

### Success Indicators
Check Cloud Logging for:
```
=== STARTING WEEKLY PROGRAM GENERATION CRON ===
Found N active users
✓ Generated weekly program for user X
=== WEEKLY PROGRAM CRON COMPLETE: {...} ===
```

### Expected Response
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

### Error Monitoring
- Set up Cloud Logging alerts for `ERROR` level logs in cron
- Monitor `errors` count in response JSON
- Check individual user errors in logs

## Troubleshooting

### Issue: No programs generated
**Symptoms**: `total_users: 0` or `skipped: N`

**Causes**:
1. No users with activity in last 14 days → Normal, no action needed
2. Users haven't configured race goals → Users need to visit Coach page
3. Check cutoff date calculation in logs

### Issue: High error rate
**Symptoms**: `errors` > 20% of `total_users`

**Causes**:
1. Claude API rate limits → Increase delay between users
2. Invalid race data → Check database integrity
3. Missing user settings → Verify `user_settings` table

### Issue: Unauthorized (401)
**Symptoms**: HTTP 401 response

**Causes**:
1. Missing `X-Cloudscheduler` header
2. OIDC token issues → Verify service account permissions
3. Check Cloud Run/App Engine authentication settings

### Issue: Programs not appearing in UI
**Symptoms**: Cron succeeds but users see no programs

**Causes**:
1. Check `weekly_programs` table for saved data
2. Verify `week_start_date` matches frontend query
3. Check frontend API call to `/api/coach/weekly-program`
4. Verify program expiry logic (CACHE_EXPIRY_DAYS = 3)

## Cost Considerations

### Claude API Usage
- **Sunday**: Full 7-day program generation (~4000 tokens per user)
- **Wednesday**: Adjustment generation (~4000 tokens per user)
- Estimated: **~8000 tokens per active user per week**

**Example cost** (25 active users):
- 25 users × 8000 tokens/week = 200,000 tokens/week
- Claude Sonnet 3.5: ~$0.60/week for generation
- Plus input tokens for context (~300K tokens) = ~$0.90/week
- **Total: ~$1.50/week or $6/month** for 25 active users

### Optimization
- Only processes active users (14-day activity window)
- Skips users without race goals
- Caches programs for 3 days to reduce redundant generation

## Maintenance

### Adjusting Schedule
To change cron timing:
```bash
gcloud scheduler jobs update http weekly-program-sunday \
    --schedule="0 20 * * 0"  # Change to 8 PM UTC
```

### Pausing Jobs
```bash
gcloud scheduler jobs pause weekly-program-sunday
gcloud scheduler jobs pause weekly-program-wednesday
```

### Resuming Jobs
```bash
gcloud scheduler jobs resume weekly-program-sunday
gcloud scheduler jobs resume weekly-program-wednesday
```

### Deleting Jobs
```bash
gcloud scheduler jobs delete weekly-program-sunday
gcloud scheduler jobs delete weekly-program-wednesday
```

## Related Documentation

- Main PRD: `tasks/prd-ytm-coach-page.md`
- Task List: `tasks/tasks-prd-ytm-coach-page.md`
- Coach Recommendations Module: `app/coach_recommendations.py`
- Deployment Process: `scripts/Deployment_script.txt`

## Support

For issues or questions:
1. Check Cloud Logging for detailed error messages
2. Review `app/coach_recommendations.py` for generation logic
3. Verify database schema in `sql/coach_schema.sql`
4. Test manually using curl commands above

