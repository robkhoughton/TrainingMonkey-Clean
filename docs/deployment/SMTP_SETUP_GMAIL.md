# Gmail SMTP Setup Guide

## Step 1: Enable 2-Factor Authentication

1. Go to your Google Account: https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow prompts to enable (if not already enabled)

## Step 2: Generate App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select app: "Mail"
3. Select device: "Other (Custom name)"
4. Name it: "Your Training Monkey"
5. Click "Generate"
6. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)
7. Save it securely - you won't see it again!

## Step 3: Add to .env File

Add these lines to your `.env` file (or create if doesn't exist):

```bash
# SMTP Configuration - Gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM_EMAIL=noreply@yourtrainingmonkey.com
APP_BASE_URL=https://yourtrainingmonkey.com
```

**Replace:**
- `your.email@gmail.com` with your actual Gmail address
- `abcdefghijklmnop` with the 16-character app password (no spaces)
- `yourtrainingmonkey.com` with your actual domain

## Step 4: Test SMTP Connection

Run the test script (see below).

## Troubleshooting

**Error: "Username and Password not accepted"**
- Make sure you're using the app password, not your regular Gmail password
- Remove any spaces from the app password

**Error: "SMTP Authentication Error"**
- 2FA must be enabled first
- Regenerate app password and try again

**Emails go to spam**
- Normal for development
- In production, use SendGrid or configure SPF/DKIM records
