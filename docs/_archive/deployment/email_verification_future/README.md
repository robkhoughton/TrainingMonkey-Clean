# Email Verification System (Future Deployment)

This folder contains the email verification system with double opt-in functionality.
**Status**: Preserved for future use, not currently deployed.

## Decision

After testing and risk assessment (Dec 5, 2024):
- Current signup flow captures emails successfully
- Email verification adds user friction and deployment risk
- System preserved here for future deployment when needed

## What's Included

### Core Module
- `email_verification.py` - Main verification module with token generation, validation, and email sending

### Templates
- `email_verification_pending.html` - Blocking page shown to users awaiting verification

### Diagnostic/Test Scripts
- `diagnose_email_verification.py` - Check deployment status and diagnose issues
- `check_email_verification_deployment.py` - Verify database schema and module import
- `check_user_verification_status.py` - Check specific user's verification status
- `check_verification_result.py` - Verify completion after user clicks email link
- `test_verification_flow.py` - End-to-end test of verification flow

### Email Testing
- `send_test_embedded_logo.py` - Send test verification email with circular logo

## Features

### Database Columns (Already Deployed)
- `email_verified` (boolean) - Whether email is verified
- `email_verification_token` (text) - Hashed verification token
- `email_verification_expires_at` (timestamp) - Token expiration (48 hours)

### Verification Flow
1. New user signs up via Strava OAuth
2. If real email (not @training-monkey.com synthetic), system:
   - Creates verification token (secure, 48hr expiration)
   - Sends email with verification link and circular YTM logo
   - Redirects to blocking page (cannot proceed)
3. User clicks email link
4. Token validated, email marked verified
5. User redirected to onboarding

### Routes (Not Currently in Production)
- `/email-verification-pending` - Blocking page with resend button
- `/verify-email?token=...` - Verification link handler
- `/api/resend-verification` - Resend verification email
- `/api/check-verification-status` - Auto-polling for verification status

### Bug Fixes Applied
- Lines 722-733 in strava_app.py: Fixed verification bypass bug
  - Users now blocked even if email send fails or exception occurs
  - Can use resend button from verification page
  - Hard verification enforced

## Git Branch

All code also preserved in git branch: `feature/email-verification`

To view:
```bash
git checkout feature/email-verification
```

To merge when ready:
```bash
git checkout master
git merge feature/email-verification
```

## Deployment Steps (When Ready)

1. **Copy files to production**:
   ```bash
   cp email_verification_future/email_verification.py app/
   cp email_verification_future/email_verification_pending.html app/templates/
   ```

2. **Merge code changes**:
   ```bash
   git checkout master
   git merge feature/email-verification
   ```
   Or cherry-pick specific commits if needed.

3. **Verify environment variables** (already configured):
   - SMTP_HOST
   - SMTP_PORT
   - SMTP_USER
   - SMTP_PASSWORD
   - SMTP_FROM_EMAIL
   - APP_BASE_URL

4. **Test deployment**:
   ```bash
   python app/diagnose_email_verification.py
   ```

5. **Monitor**:
   - Watch signup completion rates
   - Check application logs for errors
   - Test with multiple email providers
   - Have rollback plan ready

## Testing Locally

1. Start Flask app locally
2. Set `APP_BASE_URL=http://localhost:5000` in .env
3. Sign up new test user
4. Verify email flow works
5. Check logs for any errors

## Risk Assessment (Documented Dec 5, 2024)

**High Risk**: SMTP service failure blocks all new signups
**Medium Risk**: Email deliverability (spam folders), import errors
**Low Risk**: Existing users unaffected

**Mitigation**: Monitor metrics, test thoroughly, have rollback plan

## Contact

For questions about this system, refer to conversation logs from Dec 5, 2024.
