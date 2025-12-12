# Email Verification System - Debugging Guide

**Last Updated:** December 10, 2025
**System Status:** ✅ Working (Production)

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Environment Variables](#environment-variables)
4. [Common Issues & Solutions](#common-issues--solutions)
5. [Debugging Steps](#debugging-steps)
6. [Database Queries](#database-queries)
7. [Log Analysis](#log-analysis)
8. [Testing Procedures](#testing-procedures)

---

## System Overview

The email verification system requires new users to verify their email addresses before accessing the dashboard. It integrates with:
- **Strava OAuth** - Captures real email addresses during signup
- **Email Verification Module** - Sends verification emails with secure tokens
- **SMTP (Zoho)** - Sends emails via rob@yourtrainingmonkey.com
- **PostgreSQL** - Stores verification tokens and status

**Key Files:**
- `app/email_verification/core.py` - Token generation, email sending
- `app/email_verification/service.py` - Business logic layer
- `app/email_verification/routes.py` - Flask Blueprint with 4 routes
- `app/templates/email_verification_pending.html` - Waiting page with auto-polling
- `app/strava_app.py:720-735` - OAuth integration (new users)
- `app/strava_app.py:10246-10300` - Onboarding integration (email updates)

---

## Architecture

### Complete Flow (New User with Real Email)

```
1. User clicks "Connect to Strava"
   ↓
2. Strava OAuth (scope: read,activity:read_all,profile:read_all)
   ↓
3. OAuth callback receives athlete data with email
   ↓
4. Check if email is synthetic (@training-monkey.com)
   - YES → Skip verification, go to onboarding
   - NO → Continue to verification
   ↓
5. Create user in database with:
   - email = real_email (e.g., rob@yourtrainingmonkey.com)
   - email_verified = false
   - email_verification_token = hashed_token (SHA-256)
   - email_verification_expires_at = now + 48 hours
   ↓
6. Send verification email via SMTP
   ↓
7. Redirect to /email-verification-pending
   ↓
8. User clicks link in email → /verify-email?token=xxx
   ↓
9. Token validated, email marked as verified
   ↓
10. User redirected to /welcome-post-strava (onboarding)
```

### Module Structure

```
app/email_verification/
├── __init__.py          # Exports blueprint
├── routes.py            # 4 HTTP endpoints
├── service.py           # EmailVerificationService class
└── core.py              # Token generation, SMTP, validation
```

### Routes

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/email-verification-pending` | GET | Required | Blocking page, shows email, auto-polls status |
| `/verify-email` | GET | None | Handles email link clicks, validates token |
| `/api/resend-verification` | POST | Required | Resends verification email (60s cooldown) |
| `/api/check-verification-status` | GET | Required | Auto-polling endpoint (called every 5s) |

---

## Environment Variables

### Required for Email Verification

**Cloud Run Environment Variables:**

```bash
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=rob@yourtrainingmonkey.com
SMTP_PASSWORD=wq1ZdNZqenGM
SMTP_FROM_EMAIL=rob@yourtrainingmonkey.com  # MUST match SMTP_USER for Zoho
APP_BASE_URL=https://yourtrainingmonkey.com
```

### How to Check Current Settings

```bash
# List all environment variables
gcloud run services describe strava-training-personal \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Check specific variable
gcloud run services describe strava-training-personal \
  --region=us-central1 \
  --format="get(spec.template.spec.containers[0].env)" | grep SMTP
```

### How to Update Settings

```bash
# Update single variable
gcloud run services update strava-training-personal \
  --update-env-vars="SMTP_FROM_EMAIL=rob@yourtrainingmonkey.com" \
  --region=us-central1

# Update multiple variables
gcloud run services update strava-training-personal \
  --set-env-vars="SMTP_HOST=smtp.zoho.com,SMTP_PORT=587,SMTP_USER=rob@yourtrainingmonkey.com,SMTP_PASSWORD=wq1ZdNZqenGM,SMTP_FROM_EMAIL=rob@yourtrainingmonkey.com,APP_BASE_URL=https://yourtrainingmonkey.com" \
  --region=us-central1
```

---

## Common Issues & Solutions

### Issue 1: "No module named 'email_verification'"

**Symptom:** Cloud Run logs show `ModuleNotFoundError: No module named 'email_verification'`

**Cause:** The email_verification module isn't being copied into the Docker container.

**Solution:**
1. Check `app/Dockerfile.strava` line 46:
   ```dockerfile
   COPY email_verification/ /app/email_verification/
   ```
2. Rebuild and redeploy:
   ```bash
   cd app
   docker build -f Dockerfile.strava -t gcr.io/[PROJECT_ID]/strava-app:latest .
   docker push gcr.io/[PROJECT_ID]/strava-app:latest
   gcloud run deploy strava-training-personal --image gcr.io/[PROJECT_ID]/strava-app:latest
   ```

---

### Issue 2: "Sender is not allowed to relay emails"

**Symptom:** Error in logs: `SMTP error sending to ...: (553, b'Sender is not allowed to relay emails')`

**Cause:** Zoho requires SMTP_FROM_EMAIL to match SMTP_USER for authentication.

**Solution:**
```bash
gcloud run services update strava-training-personal \
  --update-env-vars="SMTP_FROM_EMAIL=rob@yourtrainingmonkey.com" \
  --region=us-central1
```

**Verification:**
```bash
gcloud run services describe strava-training-personal \
  --region=us-central1 \
  --format="get(spec.template.spec.containers[0].env)" | grep SMTP_FROM_EMAIL
```

---

### Issue 3: User Created with Synthetic Email (Not Real Email)

**Symptom:** User created with `strava_XXXXXXX@training-monkey.com` instead of real email.

**Cause:** Strava OAuth scope missing `profile:read_all`.

**Check OAuth URLs:**

```bash
cd app
grep -n "oauth/authorize" strava_app.py | grep scope
```

**Expected Results:**
- Line 1637: `scope=read,activity:read_all,profile:read_all` ✅
- Line 2380: `scope=read,activity:read_all,profile:read_all` ✅
- Line 3352: `scope=read,activity:read_all,profile:read_all` ✅

**If missing:** Add `,profile:read_all` to all OAuth URLs and redeploy.

---

### Issue 4: Verification Email Not Received

**Debugging Steps:**

1. **Check Cloud Run logs** for SMTP errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=strava-training-personal" \
     --limit=50 --format=json | grep -i smtp
   ```

2. **Check if email was sent** (look for success log):
   ```
   "SMTP email sent successfully to rob@yourtrainingmonkey.com"
   ```

3. **Check for SMTP errors:**
   ```
   "SMTP error sending to ...: ..."
   ```

4. **Verify SMTP credentials** are set:
   ```bash
   gcloud run services describe strava-training-personal \
     --region=us-central1 \
     --format="get(spec.template.spec.containers[0].env)" | grep SMTP
   ```

5. **Test SMTP connection locally:**
   ```bash
   cd app
   python scripts/testing/test_smtp_connection.py
   ```

---

### Issue 5: Verification Link Expired

**Symptom:** User clicks link, sees "Verification link has expired."

**Cause:** Tokens expire after 48 hours.

**Solution:**
1. User clicks "Resend Verification Email" on pending page
2. New token generated with fresh 48-hour expiry
3. Check database for token expiry:
   ```sql
   SELECT email, email_verification_expires_at,
          CASE
            WHEN email_verification_expires_at < NOW() THEN 'EXPIRED'
            ELSE 'VALID'
          END as status
   FROM user_settings
   WHERE email = 'user@example.com';
   ```

---

### Issue 6: Foreign Key Constraint When Deleting Test User

**Symptom:** `foreign key constraint "legal_compliance_user_id_fkey"`

**Solution:** Delete related records first:
```sql
-- Delete in correct order
DELETE FROM legal_compliance WHERE user_id = 105;
DELETE FROM user_settings WHERE id = 105;
```

---

## Debugging Steps

### Step 1: Verify User Was Created

```sql
SELECT id, email, strava_athlete_id, email_verified,
       email_verification_token IS NOT NULL as has_token,
       email_verification_expires_at,
       created_at
FROM user_settings
WHERE email = 'rob@yourtrainingmonkey.com'
   OR strava_athlete_id = 196816006
ORDER BY created_at DESC
LIMIT 1;
```

**Expected:**
- `email`: Real email (not synthetic)
- `email_verified`: false
- `has_token`: true
- `email_verification_expires_at`: ~48 hours in future

---

### Step 2: Check Cloud Run Logs

```bash
# Recent errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=strava-training-personal AND severity>=ERROR" \
  --limit=20 --format=json

# SMTP-related logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=strava-training-personal" \
  --limit=50 --format=json | grep -i "smtp\|email"

# Specific time range
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=strava-training-personal AND timestamp>=\"2025-12-11T00:00:00Z\"" \
  --limit=100 --format=json
```

**Look for:**
- `"Creating new user account for Strava athlete ..."`
- `"Using real email from Strava: ..."`
- `"Sending verification email to user ..."`
- `"SMTP email sent successfully to ..."`
- `"SMTP error sending to ..."`

---

### Step 3: Test Email Sending Manually

**Via Python:**
```python
cd app
python -c "
from dotenv import load_dotenv
load_dotenv()

from email_verification.core import send_verification_email

user_id = 999  # Test user ID
email = 'rob@yourtrainingmonkey.com'
base_url = 'https://yourtrainingmonkey.com'

success, error = send_verification_email(user_id, email, base_url)
print(f'Success: {success}')
if error:
    print(f'Error: {error}')
"
```

---

### Step 4: Verify SMTP Configuration

**Check environment variables:**
```bash
gcloud run services describe strava-training-personal \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"
```

**Required variables:**
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASSWORD
- SMTP_FROM_EMAIL (must equal SMTP_USER for Zoho)
- APP_BASE_URL

---

## Database Queries

### Check All Users Needing Verification

```sql
SELECT id, email, strava_athlete_id, email_verified, created_at
FROM user_settings
WHERE email NOT LIKE '%@training-monkey.com'  -- Real emails only
  AND email_verified = false
ORDER BY created_at DESC;
```

### Check Token Expiry Status

```sql
SELECT email,
       email_verification_expires_at,
       CASE
         WHEN email_verification_expires_at IS NULL THEN 'NO TOKEN'
         WHEN email_verification_expires_at < NOW() THEN 'EXPIRED'
         ELSE 'VALID'
       END as token_status,
       email_verified
FROM user_settings
WHERE email = 'rob@yourtrainingmonkey.com';
```

### Manually Mark Email as Verified

```sql
-- Only use if absolutely necessary (bypasses security)
UPDATE user_settings
SET email_verified = true,
    email_verification_token = NULL,
    email_verification_expires_at = NULL
WHERE id = 105;
```

### Reset Verification (Generate New Token)

```sql
-- Clear existing token to allow resend
UPDATE user_settings
SET email_verification_token = NULL,
    email_verification_expires_at = NULL,
    email_verified = false
WHERE id = 105;
```

### Find All Synthetic Emails

```sql
SELECT id, email, strava_athlete_id, created_at
FROM user_settings
WHERE email LIKE '%@training-monkey.com'
ORDER BY created_at DESC;
```

---

## Log Analysis

### Successful Email Verification Flow

**Expected Log Sequence:**

```
1. "Processing OAuth callback..."
2. "Creating new user account for Strava athlete 196816006"
3. "Athlete object attributes: ..." (debug logging)
4. "Email from athlete.email: rob@yourtrainingmonkey.com"
5. "Using real email from Strava: rob@yourtrainingmonkey.com"
6. "Created user with ID 105"
7. "Sending verification email to user 105 (rob@yourtrainingmonkey.com)"
8. "SMTP email sent successfully to rob@yourtrainingmonkey.com"
9. User redirected to /email-verification-pending
10. "Email verified successfully for user 105" (after clicking link)
```

### Common Error Patterns

**Pattern 1: No Email from Strava**
```
"Email from athlete.email: None"
"No email provided by Strava, using synthetic: strava_196816006@training-monkey.com"
```
→ Check OAuth scope includes `profile:read_all`

**Pattern 2: SMTP Relay Error**
```
"SMTP error sending to ...: (553, b'Sender is not allowed to relay emails')"
```
→ SMTP_FROM_EMAIL must match SMTP_USER

**Pattern 3: SMTP Authentication Failed**
```
"SMTP error sending to ...: (535, b'Authentication failed')"
```
→ Check SMTP_PASSWORD is correct

**Pattern 4: Connection Refused**
```
"SMTP error sending to ...: Connection refused"
```
→ Check SMTP_HOST and SMTP_PORT are correct

---

## Testing Procedures

### Full Integration Test

**Prerequisites:**
- Delete any existing test users from database
- Ensure SMTP is configured in Cloud Run
- Use incognito browser window

**Steps:**
1. Navigate to https://yourtrainingmonkey.com
2. Click "Connect to Strava"
3. Authorize with test Strava account (Athlete ID: 196816006)
4. **Expected:** Redirect to `/email-verification-pending`
5. **Expected:** Page shows "rob@yourtrainingmonkey.com"
6. **Expected:** Warning: "Failed to send email" should NOT appear
7. Check email inbox for verification email
8. **Expected:** Email from rob@yourtrainingmonkey.com
9. **Expected:** Subject: "Verify Your Email - Your Training Monkey"
10. Click "Verify My Email" button in email
11. **Expected:** Redirect to `/welcome-post-strava`
12. **Expected:** Welcome page shows:
    - "Your Strava account (Athlete ID No. 196816006) associated with rob@yourtrainingmonkey.com has been linked"
13. Complete onboarding form
14. **Expected:** Redirect to dashboard

### Test Resend Functionality

1. At verification pending page, click "Resend Verification Email"
2. **Expected:** Button disabled, shows "Sending..."
3. **Expected:** Success message: "✅ Verification email sent! Check your inbox."
4. **Expected:** Button shows "Resend in 60s" countdown
5. Wait for countdown to complete
6. **Expected:** Button re-enabled after 60 seconds

### Test Auto-Polling

1. At verification pending page on desktop
2. Open email on mobile device
3. Click verification link on mobile
4. **Expected:** Desktop page auto-redirects within 5 seconds

### Test Token Expiry

```sql
-- Manually expire a token for testing
UPDATE user_settings
SET email_verification_expires_at = NOW() - INTERVAL '1 hour'
WHERE id = 105;
```

1. Click verification link
2. **Expected:** "Verification link has expired. Please request a new one."
3. Login to account
4. **Expected:** Redirect to verification pending page
5. Click "Resend Verification Email"
6. **Expected:** New email with fresh token

---

## Troubleshooting Checklist

### Email Not Sending

- [ ] SMTP environment variables set in Cloud Run?
- [ ] SMTP_FROM_EMAIL = SMTP_USER?
- [ ] SMTP_PASSWORD correct?
- [ ] Check Cloud Run logs for SMTP errors
- [ ] Test SMTP connection locally

### User Created with Synthetic Email

- [ ] OAuth URLs include `profile:read_all`?
- [ ] Check Cloud Run logs for "Email from athlete.email: ..."
- [ ] Verify Strava account has email set
- [ ] Check Strava authorization page asks for email permission

### Verification Link Not Working

- [ ] Token expired? (Check email_verification_expires_at)
- [ ] Token matches database? (Check email_verification_token)
- [ ] APP_BASE_URL set correctly?
- [ ] Check Cloud Run logs for verification errors

### Database Issues

- [ ] email_verified, email_verification_token, email_verification_expires_at columns exist?
- [ ] Foreign key constraints preventing deletion?
- [ ] Database connection working?

---

## Quick Reference

### Service Information

**Service Name:** strava-training-personal
**Region:** us-central1
**URL:** https://strava-training-personal-382535371225.us-central1.run.app
**Domain:** https://yourtrainingmonkey.com
**Database:** train-d (PostgreSQL)
**SMTP Provider:** Zoho Mail
**SMTP User:** rob@yourtrainingmonkey.com

### Key Commands

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=strava-training-personal" --limit=50

# Update environment variable
gcloud run services update strava-training-personal --update-env-vars="KEY=value" --region=us-central1

# Deploy new revision
gcloud run deploy strava-training-personal --image gcr.io/PROJECT_ID/strava-app:latest --region=us-central1

# Check service status
gcloud run services describe strava-training-personal --region=us-central1
```

### Database Connection

```bash
# From local environment
cd app
python -c "
from dotenv import load_dotenv
load_dotenv()
from db_utils import execute_query
result = execute_query('SELECT COUNT(*) FROM user_settings WHERE email_verified = false', fetch=True)
print(result)
"
```

---

## Change Log

**December 10, 2025:**
- ✅ Implemented email verification system
- ✅ Fixed OAuth scope to request profile:read_all
- ✅ Configured Zoho SMTP
- ✅ Fixed SMTP relay issue (FROM email must match USER)
- ✅ Added transparency to welcome page (shows athlete ID and email)
- ✅ System tested and working in production

---

## Support Contacts

**Developer:** Rob Houghton
**Email:** rob@yourtrainingmonkey.com
**Strava Test Account:** Athlete ID 196816006
**SMTP Provider:** Zoho Mail (rob@yourtrainingmonkey.com)

---

**End of Debugging Guide**
