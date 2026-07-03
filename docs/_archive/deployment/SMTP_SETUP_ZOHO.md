# Zoho SMTP Setup Guide

## Your Configuration
- **Email**: rob@yourtrainingmonkey.com
- **Forwards to**: rob.houghton.ca@gmail.com
- **Use for**: Sending verification emails from Your Training Monkey

---

## Step 1: Generate Zoho App Password

Zoho requires app-specific passwords for third-party applications.

1. Log in to Zoho Mail: https://mail.zoho.com
2. Click your profile icon (top right) → **My Account**
3. Go to **Security** tab
4. Scroll to **App Passwords** section
5. Click **Generate New Password**
6. Name it: "Training Monkey SMTP"
7. **Copy the password** - you won't see it again!
8. Keep it secure

**Alternative method:**
- Direct link: https://accounts.zoho.com/home#security/app-passwords
- Or: Zoho Mail → Settings → Security → Application-Specific Passwords

---

## Step 2: Determine Your Zoho SMTP Server

Zoho has different servers based on your account region:

**United States/Global**: `smtp.zoho.com`
**Europe**: `smtp.zoho.eu`
**India**: `smtp.zoho.in`
**China**: `smtp.zoho.com.cn`
**Australia**: `smtp.zoho.com.au`

**Most likely for you**: `smtp.zoho.com` (US/Global)

---

## Step 3: Create .env Configuration

Add these lines to your `.env` file:

```bash
# SMTP Configuration - Zoho
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=rob@yourtrainingmonkey.com
SMTP_PASSWORD=your-app-specific-password-here
SMTP_FROM_EMAIL=rob@yourtrainingmonkey.com
APP_BASE_URL=https://yourtrainingmonkey.com

# Alternative: Use noreply alias if you set one up in Zoho
# SMTP_FROM_EMAIL=noreply@yourtrainingmonkey.com
```

**Replace:**
- `your-app-specific-password-here` with the app password from Step 1
- Keep `rob@yourtrainingmonkey.com` as-is

---

## Step 4: Test SMTP Connection

Run the test script:

```bash
cd app
python test_smtp_connection.py
```

When prompted, enter `rob.houghton.ca@gmail.com` to receive the test email.

---

## Zoho SMTP Settings Reference

| Setting | Value |
|---------|-------|
| **SMTP Host** | smtp.zoho.com |
| **SMTP Port** | 587 (TLS) or 465 (SSL) |
| **Encryption** | TLS/STARTTLS |
| **Authentication** | Required |
| **Username** | rob@yourtrainingmonkey.com |
| **Password** | App-specific password |
| **From Email** | rob@yourtrainingmonkey.com |

---

## Troubleshooting

### Error: "Authentication failed"
**Causes:**
- Using your regular Zoho password instead of app-specific password
- App password not generated yet
- Wrong username (must be full email: rob@yourtrainingmonkey.com)

**Fix:**
1. Generate new app-specific password in Zoho
2. Copy it exactly (no spaces)
3. Update SMTP_PASSWORD in .env

---

### Error: "Connection refused" or "Timeout"
**Causes:**
- Wrong SMTP host (wrong region)
- Firewall blocking port 587
- Network issues

**Fix:**
1. Try alternate port: Change `SMTP_PORT=465` in .env
2. Verify your region's SMTP server
3. Check firewall settings

---

### Emails go to spam
**Normal behavior:** Development emails often go to spam

**For production (optional improvements):**
1. **SPF Record**: Add to DNS
   ```
   v=spf1 include:zoho.com ~all
   ```

2. **DKIM**: Zoho provides DKIM automatically for your domain

3. **DMARC**: Add to DNS (optional)
   ```
   v=DMARC1; p=none; rua=mailto:rob@yourtrainingmonkey.com
   ```

4. **Verify domain**: In Zoho Control Panel → Domains → Verify

---

### Want to use noreply@yourtrainingmonkey.com?

**Option 1: Create email alias in Zoho**
1. Zoho Mail → Settings → Email Aliases
2. Add alias: noreply@yourtrainingmonkey.com
3. Update .env: `SMTP_FROM_EMAIL=noreply@yourtrainingmonkey.com`

**Option 2: Create separate Zoho account** (not recommended)
- More complex to manage
- Costs extra
- Use alias instead

---

## Rate Limits

**Zoho Free Plan:**
- 250 emails/day per account
- 50 recipients per email
- More than enough for your app

**Zoho Mail Lite ($1/month):**
- 500 emails/day
- Better if you expect high volume

---

## Security Best Practices

✅ **Do:**
- Use app-specific passwords (never your main password)
- Store password in .env file (never commit to git)
- Rotate app passwords periodically
- Monitor email sending logs

❌ **Don't:**
- Commit .env file to git
- Share app password
- Use same password for multiple apps
- Email sensitive data without encryption

---

## Testing Checklist

Before deploying:
- [ ] App-specific password generated in Zoho
- [ ] .env file configured with Zoho settings
- [ ] Test script runs without errors
- [ ] Test email received in Gmail inbox
- [ ] HTML formatting looks correct
- [ ] Verification link is properly formatted
- [ ] Email doesn't go to spam (or at least arrives)

---

## Production Deployment

Once tested and working:

1. **Add to production environment variables** (not .env file):
   ```bash
   # In your production server/container
   export SMTP_HOST=smtp.zoho.com
   export SMTP_PORT=587
   export SMTP_USER=rob@yourtrainingmonkey.com
   export SMTP_PASSWORD=your-app-password
   export SMTP_FROM_EMAIL=rob@yourtrainingmonkey.com
   export APP_BASE_URL=https://yourtrainingmonkey.com
   ```

2. **Docker/Docker Compose**: Add to environment section

3. **Heroku/Cloud**: Use config vars / environment settings

4. **Test in production** with a real signup

---

## Support Resources

- **Zoho SMTP Documentation**: https://www.zoho.com/mail/help/zoho-smtp.html
- **App Passwords**: https://www.zoho.com/mail/help/app-specific-passwords.html
- **Zoho Status**: https://status.zoho.com/ (check if service is down)

---

**Ready to test?** Run the test script and you'll receive an email at rob.houghton.ca@gmail.com!
