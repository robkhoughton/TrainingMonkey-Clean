# SMTP Configuration for TrainingMonkey Email Notifications

## Problem
TrainingMonkey has 32 active users, but admin notifications were never sent because SMTP credentials are not configured in Cloud Run.

## Solution
Configure Gmail SMTP for Cloud Run to enable email notifications.

---

## Step-by-Step Setup

### 1. Generate Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with your Google account (rob.houghton.ca@gmail.com)
3. Select "App": **Mail**
4. Select "Device": **Other (Custom name)**
5. Enter: "TrainingMonkey Cloud Run"
6. Click **Generate**
7. **Copy the 16-character password** (format: xxxx xxxx xxxx xxxx)

**Important:** Save this password - you can't view it again!

---

### 2. Configure Cloud Run

#### Option A: Use the Batch Script (Windows)

1. Open `configure_smtp_cloudrun.bat` in a text editor
2. Replace `YOUR_APP_PASSWORD` with your generated app password:
   ```bat
   set APP_PASSWORD=your_actual_password_here
   ```
3. Save the file
4. Run the script:
   ```cmd
   configure_smtp_cloudrun.bat
   ```

#### Option B: Manual Command (Any Platform)

Run this command in your terminal (replace `YOUR_APP_PASSWORD`):

```bash
gcloud run services update training-monkey-service \
  --region=us-central1 \
  --set-env-vars="SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,SMTP_USERNAME=rob.houghton.ca@gmail.com,SMTP_PASSWORD=YOUR_APP_PASSWORD,FROM_EMAIL=rob.houghton.ca@gmail.com,FROM_NAME=TrainingMonkey Notifications"
```

---

### 3. Verify Configuration

After running the command, verify in Google Cloud Console:

1. Go to: https://console.cloud.google.com/run
2. Select your service: `training-monkey-service`
3. Click **"Variables & Secrets"** tab
4. Confirm these variables are set:
   - `SMTP_SERVER`: smtp.gmail.com
   - `SMTP_PORT`: 587
   - `SMTP_USERNAME`: rob.houghton.ca@gmail.com
   - `SMTP_PASSWORD`: ****************
   - `FROM_EMAIL`: rob.houghton.ca@gmail.com
   - `FROM_NAME`: TrainingMonkey Notifications

---

### 4. Test Email Notifications

**Option 1: Wait for Next User**
Simply wait for the next user to register - you'll receive an email!

**Option 2: Create Test User**
1. Use a different browser/incognito mode
2. Go to: https://yourtrainingmonkey.com
3. Sign up with a test Strava account
4. Check your email (rob.houghton.ca@gmail.com) for the notification

---

## What the Notification Will Look Like

**Subject:** "New User Registration - [user_email]"

**Body:**
```
New User Registration

User ID:      [ID]
Email:        [email]
Registration Time: [timestamp]

---
This is an automated notification from TrainingMonkey.
```

---

## Troubleshooting

### Email Not Received?

1. **Check Cloud Run Logs:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=training-monkey-service" --limit=50 --format=json
   ```
   Look for: "Admin notified of new user" or "Failed to send admin notification"

2. **Check Spam Folder:**
   Gmail might filter automated emails to spam initially

3. **Verify SMTP Credentials:**
   - App password is correct (no spaces)
   - rob.houghton.ca@gmail.com has "Less secure app access" enabled (if using regular password)
   - Or use App Password (recommended)

4. **Check Gmail Settings:**
   - 2-Factor Authentication must be enabled to generate App Passwords
   - IMAP must be enabled in Gmail settings

---

## Security Notes

- ✅ App Password is **more secure** than using your main Gmail password
- ✅ App Password can be revoked at any time without changing your main password
- ✅ Environment variables are encrypted in Cloud Run
- ✅ Never commit passwords to Git

---

## Alternative: SendGrid (Optional)

If Gmail doesn't work or you prefer a dedicated email service:

1. Sign up at: https://sendgrid.com (100 emails/day free)
2. Create an API key
3. Use these settings instead:
   ```bash
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=[your_sendgrid_api_key]
   FROM_EMAIL=notifications@yourtrainingmonkey.com
   ```

---

## Current User Stats

As of now:
- **Total Users:** 33 (including you)
- **Active Regular Users:** 32
- **Total Activities:** 3,152 across all users
- **Most Active Month:** October 2025 (16 new users)

You'll now be notified as new users join!

